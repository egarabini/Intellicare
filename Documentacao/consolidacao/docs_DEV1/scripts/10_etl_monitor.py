#!/usr/bin/env python3
"""
ETL Monitor - Projeto 02
Monitora execuções ETL, gera métricas e envia alertas
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLMonitor:
    """Monitor de execuções ETL"""
    
    def __init__(self, log_directory: str = '.'):
        """
        Args:
            log_directory: Diretório onde estão os logs de execução
        """
        self.log_directory = Path(log_directory)
        self.metrics_history = []
    
    def load_execution_logs(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Carrega logs de execução dos últimos N dias
        
        Args:
            days: Número de dias para carregar
        
        Returns:
            Lista de logs de execução
        """
        logger.info(f"📂 Carregando logs dos últimos {days} dias...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        logs = []
        
        # Buscar arquivos de log JSON
        for log_file in self.log_directory.glob('etl_execution_*.json'):
            try:
                # Extrair data do nome do arquivo
                date_str = log_file.stem.split('_')[-2]  # YYYYMMDD
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date >= cutoff_date:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        logs.append(log_data)
            
            except Exception as e:
                logger.warning(f"⚠️  Erro ao carregar {log_file}: {e}")
        
        logger.info(f"✅ Carregados {len(logs)} logs")
        return logs
    
    def calculate_metrics(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula métricas consolidadas
        
        Args:
            logs: Lista de logs de execução
        
        Returns:
            Métricas consolidadas
        """
        logger.info("📊 Calculando métricas...")
        
        total_executions = len(logs)
        successful_executions = 0
        failed_executions = 0
        total_records = 0
        total_duration = 0
        errors = []
        
        for log in logs:
            summary = log.get('execution_summary', {})
            
            # Contar sucessos e falhas
            if summary.get('pipelines_failed', 0) == 0:
                successful_executions += 1
            else:
                failed_executions += 1
            
            # Somar registros e duração
            total_records += summary.get('total_records_processed', 0)
            total_duration += summary.get('duration', 0)
            
            # Coletar erros
            if summary.get('errors'):
                errors.extend(summary['errors'])
        
        # Calcular médias
        avg_duration = total_duration / total_executions if total_executions > 0 else 0
        avg_records = total_records / total_executions if total_executions > 0 else 0
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        metrics = {
            'period': {
                'start': min([log['execution_summary']['start_time'] for log in logs]) if logs else None,
                'end': max([log['execution_summary']['end_time'] for log in logs]) if logs else None
            },
            'executions': {
                'total': total_executions,
                'successful': successful_executions,
                'failed': failed_executions,
                'success_rate': round(success_rate, 2)
            },
            'records': {
                'total': total_records,
                'average_per_execution': round(avg_records, 2)
            },
            'performance': {
                'total_duration_seconds': round(total_duration, 2),
                'average_duration_seconds': round(avg_duration, 2),
                'average_duration_minutes': round(avg_duration / 60, 2)
            },
            'errors': {
                'total': len(errors),
                'details': errors
            }
        }
        
        logger.info("✅ Métricas calculadas")
        return metrics
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """
        Gera relatório em formato texto
        
        Args:
            metrics: Métricas consolidadas
        
        Returns:
            Relatório formatado
        """
        report = []
        report.append("=" * 60)
        report.append("📊 RELATÓRIO DE MONITORAMENTO ETL - INTELLICARE")
        report.append("=" * 60)
        report.append("")
        
        # Período
        report.append("📅 PERÍODO:")
        report.append(f"  Início: {metrics['period']['start']}")
        report.append(f"  Fim: {metrics['period']['end']}")
        report.append("")
        
        # Execuções
        report.append("🚀 EXECUÇÕES:")
        report.append(f"  Total: {metrics['executions']['total']}")
        report.append(f"  Sucesso: {metrics['executions']['successful']}")
        report.append(f"  Falhas: {metrics['executions']['failed']}")
        report.append(f"  Taxa de Sucesso: {metrics['executions']['success_rate']}%")
        report.append("")
        
        # Registros
        report.append("📦 REGISTROS PROCESSADOS:")
        report.append(f"  Total: {metrics['records']['total']:,}")
        report.append(f"  Média por execução: {metrics['records']['average_per_execution']:,.2f}")
        report.append("")
        
        # Performance
        report.append("⚡ PERFORMANCE:")
        report.append(f"  Duração total: {metrics['performance']['total_duration_seconds']:.2f}s")
        report.append(f"  Duração média: {metrics['performance']['average_duration_minutes']:.2f} minutos")
        report.append("")
        
        # Erros
        report.append("❌ ERROS:")
        report.append(f"  Total: {metrics['errors']['total']}")
        if metrics['errors']['details']:
            report.append("  Detalhes:")
            for error in metrics['errors']['details'][:5]:  # Mostrar apenas os 5 primeiros
                report.append(f"    - {error.get('pipeline', 'N/A')}: {error.get('error', 'N/A')}")
        report.append("")
        
        # Status
        report.append("=" * 60)
        if metrics['executions']['success_rate'] >= 95:
            report.append("✅ STATUS: SAUDÁVEL")
        elif metrics['executions']['success_rate'] >= 80:
            report.append("⚠️  STATUS: ATENÇÃO")
        else:
            report.append("❌ STATUS: CRÍTICO")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def send_alert(self, subject: str, message: str, recipients: List[str] = None):
        """
        Envia alerta por email
        
        Args:
            subject: Assunto do email
            message: Corpo do email
            recipients: Lista de destinatários
        """
        if recipients is None:
            recipients = ['dev1@intellicare.com']
        
        logger.info(f"📧 Enviando alerta: {subject}")
        
        # Configuração SMTP (exemplo - ajustar conforme necessário)
        smtp_config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'user': 'etl@intellicare.com',
            'password': 'senha_segura'
        }
        
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = smtp_config['user']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Enviar (comentado para não enviar emails reais em simulação)
            # server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            # server.starttls()
            # server.login(smtp_config['user'], smtp_config['password'])
            # server.send_message(msg)
            # server.quit()
            
            logger.info("✅ Alerta enviado com sucesso (SIMULADO)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta: {e}")
    
    def check_health(self, metrics: Dict[str, Any]) -> bool:
        """
        Verifica saúde do sistema ETL
        
        Args:
            metrics: Métricas consolidadas
        
        Returns:
            True se sistema está saudável
        """
        success_rate = metrics['executions']['success_rate']
        avg_duration = metrics['performance']['average_duration_minutes']
        
        # Critérios de saúde
        is_healthy = True
        alerts = []
        
        # Taxa de sucesso < 95%
        if success_rate < 95:
            is_healthy = False
            alerts.append(f"Taxa de sucesso baixa: {success_rate}% (esperado: >= 95%)")
        
        # Duração média > 10 minutos
        if avg_duration > 10:
            is_healthy = False
            alerts.append(f"Duração média alta: {avg_duration:.2f} min (esperado: <= 10 min)")
        
        # Enviar alertas se necessário
        if not is_healthy:
            alert_message = "⚠️  ALERTA DE SAÚDE DO ETL\n\n"
            alert_message += "\n".join(alerts)
            self.send_alert("⚠️  Alerta ETL - Sistema com problemas", alert_message)
        
        return is_healthy
    
    def run_monitoring(self, days: int = 7):
        """
        Executa monitoramento completo
        
        Args:
            days: Número de dias para analisar
        """
        logger.info("🚀 Iniciando monitoramento ETL...")
        
        # Carregar logs
        logs = self.load_execution_logs(days)
        
        if not logs:
            logger.warning("⚠️  Nenhum log encontrado")
            return
        
        # Calcular métricas
        metrics = self.calculate_metrics(logs)
        
        # Gerar relatório
        report = self.generate_report(metrics)
        print("\n" + report)
        
        # Salvar relatório
        report_file = f'etl_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 Relatório salvo em: {report_file}")
        
        # Verificar saúde
        is_healthy = self.check_health(metrics)
        
        if is_healthy:
            logger.info("✅ Sistema ETL está saudável!")
        else:
            logger.warning("⚠️  Sistema ETL requer atenção!")


def main():
    """Função principal"""
    monitor = ETLMonitor(log_directory='.')
    monitor.run_monitoring(days=7)


if __name__ == '__main__':
    main()

