#!/usr/bin/env python3
"""
ETL Orchestrator - Projeto 02
Orquestra execução de todos os pipelines ETL com controle de transações e retry
"""

import sys
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# Importar ETLs
try:
    from etl_donabedian import ETLDonabedian
    from etl_wanda import ETLWanda
except ImportError:
    # Se executado de outro diretório
    sys.path.append(str(Path(__file__).parent))
    from etl_donabedian import ETLDonabedian
    from etl_wanda import ETLWanda

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'etl_orchestrator_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Orquestrador de pipelines ETL"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 60):
        """
        Args:
            max_retries: Número máximo de tentativas em caso de erro
            retry_delay: Tempo de espera entre tentativas (segundos)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.execution_log = []
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'duration': None,
            'pipelines_executed': 0,
            'pipelines_failed': 0,
            'total_records_processed': 0,
            'errors': []
        }
    
    def execute_pipeline(self, pipeline_name: str, pipeline_class, since_date: datetime = None) -> Dict[str, Any]:
        """
        Executa um pipeline ETL com retry automático
        
        Args:
            pipeline_name: Nome do pipeline
            pipeline_class: Classe do pipeline
            since_date: Data inicial para extração
        
        Returns:
            Métricas de execução do pipeline
        """
        logger.info(f"🚀 Iniciando pipeline: {pipeline_name}")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Criar instância do pipeline
                pipeline = pipeline_class()
                
                # Executar pipeline
                metrics = pipeline.run(since_date)
                
                # Log de sucesso
                self.execution_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'pipeline': pipeline_name,
                    'status': 'SUCCESS',
                    'attempt': attempt,
                    'metrics': metrics
                })
                
                logger.info(f"✅ Pipeline {pipeline_name} concluído com sucesso!")
                logger.info(f"   - Registros processados: {metrics.get('records_loaded', 0)}")
                logger.info(f"   - Duração: {metrics.get('duration', 0):.2f}s")
                
                return metrics
                
            except Exception as e:
                error_msg = f"Erro no pipeline {pipeline_name} (tentativa {attempt}/{self.max_retries}): {e}"
                logger.error(f"❌ {error_msg}")
                
                self.execution_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'pipeline': pipeline_name,
                    'status': 'ERROR',
                    'attempt': attempt,
                    'error': str(e)
                })
                
                # Se não é a última tentativa, aguardar antes de retry
                if attempt < self.max_retries:
                    logger.warning(f"⏳ Aguardando {self.retry_delay}s antes de tentar novamente...")
                    time.sleep(self.retry_delay)
                else:
                    # Última tentativa falhou
                    logger.error(f"❌ Pipeline {pipeline_name} falhou após {self.max_retries} tentativas")
                    self.metrics['errors'].append({
                        'pipeline': pipeline_name,
                        'error': str(e),
                        'attempts': self.max_retries
                    })
                    raise
    
    def run_daily_etl(self, since_date: datetime = None) -> Dict[str, Any]:
        """
        Executa ETL diário completo
        
        Args:
            since_date: Data inicial para extração (padrão: últimas 24h)
        
        Returns:
            Métricas consolidadas de execução
        """
        self.metrics['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO ETL DIÁRIO - INTELLICARE")
        logger.info("=" * 60)
        logger.info(f"Data/Hora: {self.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if since_date is None:
            since_date = datetime.now() - timedelta(days=1)
            logger.info(f"Período: Últimas 24 horas (desde {since_date.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            logger.info(f"Período: Desde {since_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("=" * 60)
        
        # Lista de pipelines a executar
        pipelines = [
            ('Donabedian', ETLDonabedian),
            ('Wanda', ETLWanda)
        ]
        
        # Executar cada pipeline
        for pipeline_name, pipeline_class in pipelines:
            try:
                metrics = self.execute_pipeline(pipeline_name, pipeline_class, since_date)
                self.metrics['pipelines_executed'] += 1
                self.metrics['total_records_processed'] += metrics.get('records_loaded', 0)
                
            except Exception as e:
                self.metrics['pipelines_failed'] += 1
                logger.error(f"❌ Pipeline {pipeline_name} falhou definitivamente: {e}")
                # Continuar com próximo pipeline mesmo se um falhar
                continue
        
        # Finalizar
        self.metrics['end_time'] = datetime.now()
        self.metrics['duration'] = (
            self.metrics['end_time'] - self.metrics['start_time']
        ).total_seconds()
        
        # Log de resumo
        self._log_summary()
        
        # Salvar logs
        self._save_execution_log()
        
        return self.metrics
    
    def _log_summary(self):
        """Registra resumo da execução"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 RESUMO DA EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Início: {self.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Fim: {self.metrics['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duração: {self.metrics['duration']:.2f}s ({self.metrics['duration']/60:.1f} minutos)")
        logger.info("")
        logger.info(f"Pipelines executados: {self.metrics['pipelines_executed']}")
        logger.info(f"Pipelines com falha: {self.metrics['pipelines_failed']}")
        logger.info(f"Total de registros processados: {self.metrics['total_records_processed']}")
        logger.info(f"Erros: {len(self.metrics['errors'])}")
        
        if self.metrics['errors']:
            logger.error("")
            logger.error("❌ ERROS ENCONTRADOS:")
            for error in self.metrics['errors']:
                logger.error(f"  - {error['pipeline']}: {error['error']}")
        
        logger.info("=" * 60)
        
        # Status final
        if self.metrics['pipelines_failed'] == 0:
            logger.info("✅ ETL DIÁRIO CONCLUÍDO COM SUCESSO!")
        else:
            logger.warning("⚠️  ETL DIÁRIO CONCLUÍDO COM FALHAS!")
        
        logger.info("=" * 60)
    
    def _save_execution_log(self):
        """Salva log de execução em arquivo JSON"""
        log_file = f'etl_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        output = {
            'execution_summary': self.metrics,
            'execution_log': self.execution_log
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 Log de execução salvo em: {log_file}")
    
    def validate_execution(self) -> bool:
        """
        Valida se a execução foi bem-sucedida
        
        Returns:
            True se todos os pipelines foram executados com sucesso
        """
        return self.metrics['pipelines_failed'] == 0


def main():
    """Função principal"""
    # Criar orquestrador
    orchestrator = ETLOrchestrator(
        max_retries=3,
        retry_delay=60
    )
    
    # Executar ETL diário
    try:
        metrics = orchestrator.run_daily_etl()
        
        # Validar execução
        if orchestrator.validate_execution():
            logger.info("✅ Validação: ETL executado com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Validação: ETL executado com falhas!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Erro fatal no orquestrador: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()

