#!/usr/bin/env python3
"""
ETL Donabedian - Projeto 02
Extrai dados de indicadores do OLTP, anonimiza e carrega no OLAP
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
        logging.FileHandler(f'etl_donabedian_{datetime.now().strftime("%Y%m%d")}.log'),
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


class ETLDonabedian:
    """Pipeline ETL para dados Donabedian"""
    
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
    def categorizar_valor(valor: float, meta: float) -> str:
        """Categoriza valor em relação à meta"""
        if valor < meta * 0.8:
            return 'baixo'
        elif valor > meta * 1.2:
            return 'alto'
        else:
            return 'medio'
    
    def extract(self, since_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Extrai medições do OLTP
        
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
                m.id,
                m.indicador_id,
                i.nome as indicador_nome,
                i.tipo as indicador_tipo,
                m.periodo_inicio,
                m.periodo_fim,
                m.valor_medido,
                m.valor_meta,
                m.atingiu_meta,
                m.created_at
            FROM donabedian.medicoes m
            JOIN donabedian.indicadores i ON m.indicador_id = i.id
            WHERE m.created_at >= %s
            ORDER BY m.created_at;
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
        - Hash SHA-256 de indicador_id
        - Categorização de valores
        - Generalização de datas (ano/mês/trimestre)
        """
        logger.info("🔄 Iniciando transformação...")
        
        transformed = []
        
        for record in data:
            try:
                # Anonimizar ID do indicador
                indicador_hash = self.hash_id(record['indicador_id'])
                
                # Extrair componentes temporais
                periodo_inicio = record['periodo_inicio']
                ano = periodo_inicio.year
                mes = periodo_inicio.month
                trimestre = (mes - 1) // 3 + 1
                
                # Categorizar valor
                faixa_valor = self.categorizar_valor(
                    record['valor_medido'],
                    record['valor_meta']
                )
                
                # Criar registro transformado
                transformed_record = {
                    'indicador_hash': indicador_hash,
                    'indicador_nome': record['indicador_nome'],
                    'indicador_tipo': record['indicador_tipo'],
                    'periodo_ano': ano,
                    'periodo_mes': mes,
                    'periodo_trimestre': trimestre,
                    'valor_medido': record['valor_medido'],
                    'valor_meta': record['valor_meta'],
                    'atingiu_meta': record['atingiu_meta'],
                    'faixa_valor': faixa_valor
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
                r['indicador_hash'],
                r['indicador_nome'],
                r['indicador_tipo'],
                r['periodo_ano'],
                r['periodo_mes'],
                r['periodo_trimestre'],
                r['valor_medido'],
                r['valor_meta'],
                r['atingiu_meta'],
                r['faixa_valor']
            )
            for r in data
        ]
        
        # INSERT em lote
        insert_query = """
            INSERT INTO analytics_donabedian.fato_medicoes (
                indicador_hash,
                indicador_nome,
                indicador_tipo,
                periodo_ano,
                periodo_mes,
                periodo_trimestre,
                valor_medido,
                valor_meta,
                atingiu_meta,
                faixa_valor
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
        logger.info("🚀 Iniciando ETL Donabedian...")
        
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
            
            logger.info("✅ ETL Donabedian concluído com sucesso!")
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
    etl = ETLDonabedian()
    
    # Executar ETL para últimas 24 horas
    metrics = etl.run()
    
    # Salvar métricas em JSON
    with open(f'etl_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)


if __name__ == '__main__':
    main()

