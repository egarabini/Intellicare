#!/usr/bin/env python3
"""
Script de Migração de Dados - Projeto 02
Migra dados históricos para OLTP e popula OLAP com dados anonimizados
"""

import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
import hashlib
import logging
from typing import List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configurações de conexão aos bancos de dados"""
    
    # OLTP (Operacional)
    OLTP_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_oltp',
        'user': 'intellicare_app',
        'password': 'IntelliCare@2026!OLTP'
    }
    
    # OLAP (Analítico)
    OLAP_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_olap',
        'user': 'postgres',  # Precisa de permissão de escrita
        'password': 'postgres'
    }


class DataMigrator:
    """Classe para migração de dados"""
    
    def __init__(self):
        self.conn_oltp = None
        self.conn_olap = None
        
    def connect(self):
        """Conecta aos bancos de dados"""
        try:
            self.conn_oltp = psycopg2.connect(**DatabaseConfig.OLTP_CONFIG)
            self.conn_olap = psycopg2.connect(**DatabaseConfig.OLAP_CONFIG)
            logger.info("✅ Conexões estabelecidas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise
    
    def disconnect(self):
        """Desconecta dos bancos de dados"""
        if self.conn_oltp:
            self.conn_oltp.close()
        if self.conn_olap:
            self.conn_olap.close()
        logger.info("🔌 Conexões fechadas")
    
    @staticmethod
    def hash_id(value: int) -> str:
        """Gera hash SHA-256 de um ID"""
        return hashlib.sha256(str(value).encode()).hexdigest()
    
    @staticmethod
    def categorizar_valor(valor: float, baixo: float, alto: float) -> str:
        """Categoriza valor em faixas"""
        if valor < baixo:
            return 'baixo'
        elif valor > alto:
            return 'alto'
        else:
            return 'medio'
    
    @staticmethod
    def categorizar_permanencia(dias: int) -> str:
        """Categoriza tempo de permanência"""
        if dias < 3:
            return 'curta'
        elif dias <= 7:
            return 'media'
        else:
            return 'longa'
    
    def migrate_donabedian(self):
        """Migra dados do módulo Donabedian"""
        logger.info("📊 Iniciando migração Donabedian...")
        
        cur_oltp = self.conn_oltp.cursor()
        
        # 1. Inserir indicadores de exemplo
        indicadores = [
            ('Taxa de Ocupação de Leitos', 'Percentual de leitos ocupados', 'estrutura', 
             '(leitos_ocupados / total_leitos) * 100', 85.0, '%'),
            ('Tempo Médio de Permanência', 'Média de dias de internação', 'processo', 
             'AVG(data_saida - data_entrada)', 5.0, 'dias'),
            ('Taxa de Mortalidade', 'Percentual de óbitos', 'resultado', 
             '(total_obitos / total_internacoes) * 100', 2.0, '%'),
        ]
        
        cur_oltp.executemany("""
            INSERT INTO donabedian.indicadores 
            (nome, descricao, tipo, formula, meta_valor, meta_unidade)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, indicadores)
        
        logger.info(f"✅ Inseridos {len(indicadores)} indicadores")
        
        # 2. Inserir medições dos últimos 12 meses
        cur_oltp.execute("SELECT id FROM donabedian.indicadores")
        indicador_ids = [row[0] for row in cur_oltp.fetchall()]
        
        medicoes = []
        for mes in range(12, 0, -1):
            data_fim = datetime.now() - timedelta(days=30 * (mes - 1))
            data_inicio = data_fim - timedelta(days=30)
            
            for ind_id in indicador_ids:
                # Gerar valores aleatórios (em produção, viriam do sistema antigo)
                import random
                valor = round(random.uniform(70, 95), 2)
                meta = 85.0
                
                medicoes.append((
                    ind_id,
                    data_inicio.date(),
                    data_fim.date(),
                    valor,
                    meta,
                    valor >= meta
                ))
        
        cur_oltp.executemany("""
            INSERT INTO donabedian.medicoes 
            (indicador_id, periodo_inicio, periodo_fim, valor_medido, valor_meta, atingiu_meta)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, medicoes)
        
        logger.info(f"✅ Inseridas {len(medicoes)} medições")
        
        self.conn_oltp.commit()
        logger.info("✅ Migração Donabedian concluída")
    
    def migrate_wanda(self):
        """Migra dados do módulo Wanda"""
        logger.info("🏥 Iniciando migração Wanda...")
        
        cur_oltp = self.conn_oltp.cursor()
        
        # 1. Inserir leitos de exemplo
        leitos = []
        for i in range(1, 51):  # 50 leitos
            setor = 'UTI' if i <= 10 else 'Enfermaria' if i <= 40 else 'Isolamento'
            tipo = 'UTI' if i <= 10 else 'enfermaria' if i <= 40 else 'isolamento'
            
            leitos.append((
                f'L{i:03d}',
                setor,
                tipo,
                'disponivel'
            ))
        
        cur_oltp.executemany("""
            INSERT INTO wanda.leitos 
            (numero, setor, tipo, status)
            VALUES (%s, %s, %s, %s)
        """, leitos)
        
        logger.info(f"✅ Inseridos {len(leitos)} leitos")
        
        # 2. Inserir ocupações dos últimos 6 meses
        cur_oltp.execute("SELECT id FROM wanda.leitos")
        leito_ids = [row[0] for row in cur_oltp.fetchall()]
        
        ocupacoes = []
        import random
        
        for _ in range(200):  # 200 ocupações
            leito_id = random.choice(leito_ids)
            paciente_id = random.randint(1000, 9999)
            
            dias_atras = random.randint(0, 180)
            data_entrada = datetime.now() - timedelta(days=dias_atras)
            
            # 70% já tiveram alta
            if random.random() < 0.7:
                permanencia = random.randint(1, 15)
                data_saida = data_entrada + timedelta(days=permanencia)
                status = random.choice(['alta', 'transferido'])
            else:
                data_saida = None
                status = 'ativo'
            
            ocupacoes.append((
                leito_id,
                paciente_id,
                data_entrada,
                data_saida,
                'Internação clínica',
                status
            ))
        
        cur_oltp.executemany("""
            INSERT INTO wanda.ocupacoes 
            (leito_id, paciente_id, data_entrada, data_saida, motivo_internacao, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ocupacoes)
        
        logger.info(f"✅ Inseridas {len(ocupacoes)} ocupações")
        
        self.conn_oltp.commit()
        logger.info("✅ Migração Wanda concluída")
    
    def populate_olap(self):
        """Popula OLAP com dados anonimizados"""
        logger.info("🔒 Iniciando população OLAP com dados anonimizados...")
        
        # Implementação será feita no script ETL
        logger.info("⏭️  População OLAP será feita pelo pipeline ETL")
    
    def validate_migration(self):
        """Valida a migração"""
        logger.info("✅ Validando migração...")
        
        cur_oltp = self.conn_oltp.cursor()
        
        # Contar registros OLTP
        cur_oltp.execute("SELECT COUNT(*) FROM donabedian.indicadores")
        count_indicadores = cur_oltp.fetchone()[0]
        
        cur_oltp.execute("SELECT COUNT(*) FROM donabedian.medicoes")
        count_medicoes = cur_oltp.fetchone()[0]
        
        cur_oltp.execute("SELECT COUNT(*) FROM wanda.leitos")
        count_leitos = cur_oltp.fetchone()[0]
        
        cur_oltp.execute("SELECT COUNT(*) FROM wanda.ocupacoes")
        count_ocupacoes = cur_oltp.fetchone()[0]
        
        logger.info(f"""
        📊 Resumo da Migração:
        ├── Donabedian:
        │   ├── Indicadores: {count_indicadores}
        │   └── Medições: {count_medicoes}
        └── Wanda:
            ├── Leitos: {count_leitos}
            └── Ocupações: {count_ocupacoes}
        """)
        
        return True


def main():
    """Função principal"""
    logger.info("🚀 Iniciando migração de dados...")
    
    migrator = DataMigrator()
    
    try:
        # Conectar
        migrator.connect()
        
        # Migrar dados
        migrator.migrate_donabedian()
        migrator.migrate_wanda()
        
        # Validar
        migrator.validate_migration()
        
        logger.info("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        raise
    
    finally:
        # Desconectar
        migrator.disconnect()


if __name__ == '__main__':
    main()

