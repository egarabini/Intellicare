#!/usr/bin/env python3
"""
ETL Wanda - Projeto 02
Extrai dados de ocupação de leitos do OLTP, anonimiza e carrega no OLAP
"""

import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
import hashlib
import logging
import json
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'etl_wanda_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configurações de conexão"""
    
    OLTP = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_oltp',
        'user': 'intellicare_app',
        'password': 'IntelliCare@2026!OLTP'
    }
    
    OLAP = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_olap',
        'user': 'postgres',
        'password': 'postgres'
    }


class ETLWanda:
    """Pipeline ETL para dados Wanda (Gestão de Leitos)"""
    
    def __init__(self):
        self.conn_oltp = None
        self.conn_olap = None
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'records_extracted': 0,
            'records_transformed': 0,
            'records_loaded': 0,
            'errors': []
        }
    
    def connect(self):
        """Conecta aos bancos de dados"""
        try:
            self.conn_oltp = psycopg2.connect(**DatabaseConfig.OLTP)
            self.conn_olap = psycopg2.connect(**DatabaseConfig.OLAP)
            logger.info("✅ Conexões estabelecidas")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise
    
    def disconnect(self):
        """Desconecta dos bancos"""
        if self.conn_oltp:
            self.conn_oltp.close()
        if self.conn_olap:
            self.conn_olap.close()
        logger.info("🔌 Conexões fechadas")
    
    @staticmethod
    def hash_id(value: int) -> str:
        """Gera hash SHA-256 irreversível"""
        return hashlib.sha256(str(value).encode()).hexdigest()
    
    @staticmethod
    def categorizar_permanencia(dias: float) -> str:
        """Categoriza tempo de permanência"""
        if dias < 3:
            return 'curta'
        elif dias <= 7:
            return 'media'
        else:
            return 'longa'
    
    @staticmethod
    def calcular_permanencia(data_entrada: datetime, data_saida: datetime = None) -> float:
        """Calcula tempo de permanência em dias"""
        if data_saida is None:
            data_saida = datetime.now()
        delta = data_saida - data_entrada
        return delta.total_seconds() / 86400  # Converter para dias
    
    def extract(self, since_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Extrai ocupações do OLTP
        
        Args:
            since_date: Data inicial para extração incremental
                       Se None, extrai últimas 24 horas
        """
        logger.info("📥 Iniciando extração...")
        
        if since_date is None:
            since_date = datetime.now() - timedelta(days=1)
        
        cur = self.conn_oltp.cursor()
        
        query = """
            SELECT 
                o.id,
                o.leito_id,
                l.numero as leito_numero,
                l.tipo as leito_tipo,
                o.paciente_id,
                o.data_entrada,
                o.data_saida,
                o.motivo_saida,
                o.created_at
            FROM wanda.ocupacoes o
            JOIN wanda.leitos l ON o.leito_id = l.id
            WHERE o.created_at >= %s
            ORDER BY o.created_at;
        """
        
        cur.execute(query, (since_date,))
        rows = cur.fetchall()
        
        # Converter para lista de dicionários
        columns = [desc[0] for desc in cur.description]
        data = [dict(zip(columns, row)) for row in rows]
        
        self.metrics['records_extracted'] = len(data)
        logger.info(f"✅ Extraídos {len(data)} registros")
        
        cur.close()
        return data
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma e anonimiza dados
        
        Anonimização LGPD:
        - Hash SHA-256 de leito_id e paciente_id
        - Categorização de tempo de permanência
        - Generalização de datas (ano/mês/trimestre)
        - Remoção de identificadores diretos
        """
        logger.info("🔄 Iniciando transformação...")
        
        transformed = []
        
        for record in data:
            try:
                # Anonimizar IDs
                leito_hash = self.hash_id(record['leito_id'])
                paciente_hash = self.hash_id(record['paciente_id'])
                
                # Calcular permanência
                permanencia_dias = self.calcular_permanencia(
                    record['data_entrada'],
                    record['data_saida']
                )
                
                # Categorizar permanência
                faixa_permanencia = self.categorizar_permanencia(permanencia_dias)
                
                # Extrair componentes temporais
                data_entrada = record['data_entrada']
                ano = data_entrada.year
                mes = data_entrada.month
                trimestre = (mes - 1) // 3 + 1
                
                # Determinar status
                status = 'concluida' if record['data_saida'] else 'em_andamento'
                
                # Criar registro transformado
                transformed_record = {
                    'leito_hash': leito_hash,
                    'leito_tipo': record['leito_tipo'],
                    'paciente_hash': paciente_hash,
                    'entrada_ano': ano,
                    'entrada_mes': mes,
                    'entrada_trimestre': trimestre,
                    'permanencia_dias': round(permanencia_dias, 2),
                    'faixa_permanencia': faixa_permanencia,
                    'status': status,
                    'motivo_saida': record['motivo_saida'] if record['data_saida'] else None
                }
                
                transformed.append(transformed_record)
                
            except Exception as e:
                logger.error(f"❌ Erro ao transformar registro {record.get('id')}: {e}")
                self.metrics['errors'].append({
                    'record_id': record.get('id'),
                    'error': str(e)
                })
        
        self.metrics['records_transformed'] = len(transformed)
        logger.info(f"✅ Transformados {len(transformed)} registros")
        
        return transformed
    
    def load(self, data: List[Dict[str, Any]]) -> int:
        """
        Carrega dados no OLAP
        
        Returns:
            Número de registros carregados
        """
        logger.info("📤 Iniciando carga...")
        
        if not data:
            logger.warning("⚠️  Nenhum dado para carregar")
            return 0
        
        cur = self.conn_olap.cursor()
        
        # Preparar dados para inserção em lote
        values = [
            (
                r['leito_hash'],
                r['leito_tipo'],
                r['paciente_hash'],
                r['entrada_ano'],
                r['entrada_mes'],
                r['entrada_trimestre'],
                r['permanencia_dias'],
                r['faixa_permanencia'],
                r['status'],
                r['motivo_saida']
            )
            for r in data
        ]
        
        # INSERT em lote
        insert_query = """
            INSERT INTO analytics_wanda.fato_ocupacoes (
                leito_hash,
                leito_tipo,
                paciente_hash,
                entrada_ano,
                entrada_mes,
                entrada_trimestre,
                permanencia_dias,
                faixa_permanencia,
                status,
                motivo_saida
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """
        
        execute_batch(cur, insert_query, values, page_size=100)
        self.conn_olap.commit()
        
        self.metrics['records_loaded'] = len(data)
        logger.info(f"✅ Carregados {len(data)} registros")
        
        cur.close()
        return len(data)
    
    def run(self, since_date: datetime = None) -> Dict[str, Any]:
        """
        Executa pipeline ETL completo
        
        Args:
            since_date: Data inicial para extração
        
        Returns:
            Métricas de execução
        """
        self.metrics['start_time'] = datetime.now()
        logger.info("🚀 Iniciando ETL Wanda...")
        
        try:
            # Conectar
            self.connect()
            
            # Extract
            data = self.extract(since_date)
            
            # Transform
            transformed_data = self.transform(data)
            
            # Load
            self.load(transformed_data)
            
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration'] = (
                self.metrics['end_time'] - self.metrics['start_time']
            ).total_seconds()
            
            logger.info("✅ ETL Wanda concluído com sucesso!")
            self._log_metrics()
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"❌ Erro no ETL: {e}")
            self.metrics['errors'].append({'fatal': str(e)})
            raise
        
        finally:
            self.disconnect()
    
    def _log_metrics(self):
        """Registra métricas de execução"""
        logger.info("📊 Métricas de Execução:")
        logger.info(f"  - Duração: {self.metrics['duration']:.2f}s")
        logger.info(f"  - Extraídos: {self.metrics['records_extracted']}")
        logger.info(f"  - Transformados: {self.metrics['records_transformed']}")
        logger.info(f"  - Carregados: {self.metrics['records_loaded']}")
        logger.info(f"  - Erros: {len(self.metrics['errors'])}")


def main():
    """Função principal"""
    etl = ETLWanda()
    
    # Executar ETL para últimas 24 horas
    metrics = etl.run()
    
    # Salvar métricas em JSON
    with open(f'etl_wanda_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)


if __name__ == '__main__':
    main()

