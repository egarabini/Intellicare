#!/usr/bin/env python3
"""
Script de Validação de Dados - Projeto 02
Valida integridade e contagem de dados migrados
"""

import psycopg2
import logging
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataValidator:
    """Classe para validação de dados"""
    
    OLTP_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_oltp',
        'user': 'intellicare_app',
        'password': 'IntelliCare@2026!OLTP'
    }
    
    def __init__(self):
        self.conn = None
        self.validation_results = []
    
    def connect(self):
        """Conecta ao banco OLTP"""
        try:
            self.conn = psycopg2.connect(**self.OLTP_CONFIG)
            logger.info("✅ Conectado ao OLTP")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise
    
    def disconnect(self):
        """Desconecta do banco"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Desconectado")
    
    def validate_counts(self) -> bool:
        """Valida contagem de registros"""
        logger.info("📊 Validando contagem de registros...")
        
        cur = self.conn.cursor()
        
        # Tabelas esperadas e contagens mínimas
        expected_counts = {
            'donabedian.indicadores': 3,
            'donabedian.medicoes': 36,  # 3 indicadores * 12 meses
            'wanda.leitos': 50,
            'wanda.ocupacoes': 200
        }
        
        all_valid = True
        
        for table, min_count in expected_counts.items():
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            actual_count = cur.fetchone()[0]
            
            if actual_count >= min_count:
                logger.info(f"  ✅ {table}: {actual_count} registros (mínimo: {min_count})")
                self.validation_results.append((table, True, actual_count))
            else:
                logger.error(f"  ❌ {table}: {actual_count} registros (esperado: >= {min_count})")
                self.validation_results.append((table, False, actual_count))
                all_valid = False
        
        cur.close()
        return all_valid
    
    def validate_referential_integrity(self) -> bool:
        """Valida integridade referencial"""
        logger.info("🔗 Validando integridade referencial...")
        
        cur = self.conn.cursor()
        all_valid = True
        
        # Teste 1: Todas as medições têm indicador válido
        cur.execute("""
            SELECT COUNT(*) 
            FROM donabedian.medicoes m
            LEFT JOIN donabedian.indicadores i ON m.indicador_id = i.id
            WHERE i.id IS NULL;
        """)
        orphan_medicoes = cur.fetchone()[0]
        
        if orphan_medicoes == 0:
            logger.info(f"  ✅ Medições: todas têm indicador válido")
        else:
            logger.error(f"  ❌ Medições: {orphan_medicoes} sem indicador válido")
            all_valid = False
        
        # Teste 2: Todas as ocupações têm leito válido
        cur.execute("""
            SELECT COUNT(*) 
            FROM wanda.ocupacoes o
            LEFT JOIN wanda.leitos l ON o.leito_id = l.id
            WHERE l.id IS NULL;
        """)
        orphan_ocupacoes = cur.fetchone()[0]
        
        if orphan_ocupacoes == 0:
            logger.info(f"  ✅ Ocupações: todas têm leito válido")
        else:
            logger.error(f"  ❌ Ocupações: {orphan_ocupacoes} sem leito válido")
            all_valid = False
        
        # Teste 3: Todas as transferências têm ocupação válida
        cur.execute("""
            SELECT COUNT(*) 
            FROM wanda.transferencias t
            LEFT JOIN wanda.ocupacoes o ON t.ocupacao_id = o.id
            WHERE o.id IS NULL;
        """)
        orphan_transferencias = cur.fetchone()[0]
        
        if orphan_transferencias == 0:
            logger.info(f"  ✅ Transferências: todas têm ocupação válida")
        else:
            logger.error(f"  ❌ Transferências: {orphan_transferencias} sem ocupação válida")
            all_valid = False
        
        cur.close()
        return all_valid
    
    def validate_data_quality(self) -> bool:
        """Valida qualidade dos dados"""
        logger.info("✨ Validando qualidade dos dados...")
        
        cur = self.conn.cursor()
        all_valid = True
        
        # Teste 1: Indicadores têm nome
        cur.execute("""
            SELECT COUNT(*) 
            FROM donabedian.indicadores
            WHERE nome IS NULL OR nome = '';
        """)
        invalid_names = cur.fetchone()[0]
        
        if invalid_names == 0:
            logger.info(f"  ✅ Indicadores: todos têm nome válido")
        else:
            logger.error(f"  ❌ Indicadores: {invalid_names} sem nome")
            all_valid = False
        
        # Teste 2: Medições têm período válido
        cur.execute("""
            SELECT COUNT(*) 
            FROM donabedian.medicoes
            WHERE periodo_fim < periodo_inicio;
        """)
        invalid_periods = cur.fetchone()[0]
        
        if invalid_periods == 0:
            logger.info(f"  ✅ Medições: todos os períodos são válidos")
        else:
            logger.error(f"  ❌ Medições: {invalid_periods} com período inválido")
            all_valid = False
        
        # Teste 3: Leitos têm número único
        cur.execute("""
            SELECT numero, COUNT(*) 
            FROM wanda.leitos
            GROUP BY numero
            HAVING COUNT(*) > 1;
        """)
        duplicate_leitos = cur.fetchall()
        
        if len(duplicate_leitos) == 0:
            logger.info(f"  ✅ Leitos: todos os números são únicos")
        else:
            logger.error(f"  ❌ Leitos: {len(duplicate_leitos)} números duplicados")
            all_valid = False
        
        # Teste 4: Ocupações têm datas válidas
        cur.execute("""
            SELECT COUNT(*) 
            FROM wanda.ocupacoes
            WHERE data_saida IS NOT NULL AND data_saida < data_entrada;
        """)
        invalid_dates = cur.fetchone()[0]
        
        if invalid_dates == 0:
            logger.info(f"  ✅ Ocupações: todas as datas são válidas")
        else:
            logger.error(f"  ❌ Ocupações: {invalid_dates} com datas inválidas")
            all_valid = False
        
        cur.close()
        return all_valid
    
    def validate_indexes(self) -> bool:
        """Valida existência de índices"""
        logger.info("🔍 Validando índices...")
        
        cur = self.conn.cursor()
        
        # Listar índices criados
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname
            FROM pg_indexes
            WHERE schemaname IN ('donabedian', 'wanda')
            AND indexname NOT LIKE '%_pkey'
            ORDER BY schemaname, tablename, indexname;
        """)
        
        indexes = cur.fetchall()
        
        logger.info(f"  ✅ Total de índices: {len(indexes)}")
        for schema, table, index in indexes:
            logger.info(f"    - {schema}.{table}: {index}")
        
        cur.close()
        return len(indexes) > 0
    
    def generate_statistics(self):
        """Gera estatísticas dos dados"""
        logger.info("📈 Gerando estatísticas...")
        
        cur = self.conn.cursor()
        
        # Estatísticas Donabedian
        cur.execute("""
            SELECT 
                tipo,
                COUNT(*) as total,
                AVG(meta_valor) as meta_media
            FROM donabedian.indicadores
            GROUP BY tipo;
        """)
        
        logger.info("\n  📊 Indicadores por tipo:")
        for tipo, total, meta_media in cur.fetchall():
            logger.info(f"    - {tipo}: {total} indicadores (meta média: {meta_media:.2f})")
        
        # Estatísticas de medições
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN atingiu_meta THEN 1 ELSE 0 END) as atingiu_meta,
                AVG(valor_medido) as valor_medio
            FROM donabedian.medicoes;
        """)
        
        total, atingiu, valor_medio = cur.fetchone()
        logger.info(f"\n  📊 Medições:")
        logger.info(f"    - Total: {total}")
        logger.info(f"    - Atingiu meta: {atingiu} ({atingiu/total*100:.1f}%)")
        logger.info(f"    - Valor médio: {valor_medio:.2f}")
        
        # Estatísticas Wanda
        cur.execute("""
            SELECT 
                tipo,
                COUNT(*) as total
            FROM wanda.leitos
            GROUP BY tipo;
        """)
        
        logger.info(f"\n  🏥 Leitos por tipo:")
        for tipo, total in cur.fetchall():
            logger.info(f"    - {tipo}: {total} leitos")
        
        # Estatísticas de ocupações
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as total,
                AVG(EXTRACT(EPOCH FROM (COALESCE(data_saida, CURRENT_TIMESTAMP) - data_entrada))/86400) as media_dias
            FROM wanda.ocupacoes
            GROUP BY status;
        """)
        
        logger.info(f"\n  🛏️  Ocupações por status:")
        for status, total, media_dias in cur.fetchall():
            logger.info(f"    - {status}: {total} ocupações (média: {media_dias:.1f} dias)")
        
        cur.close()
    
    def run_all_validations(self) -> bool:
        """Executa todas as validações"""
        logger.info("🚀 Iniciando validações...\n")
        
        results = []
        
        # Validação 1: Contagens
        logger.info("=" * 60)
        logger.info("VALIDAÇÃO 1: Contagem de Registros")
        logger.info("=" * 60)
        results.append(self.validate_counts())
        
        # Validação 2: Integridade Referencial
        logger.info("\n" + "=" * 60)
        logger.info("VALIDAÇÃO 2: Integridade Referencial")
        logger.info("=" * 60)
        results.append(self.validate_referential_integrity())
        
        # Validação 3: Qualidade dos Dados
        logger.info("\n" + "=" * 60)
        logger.info("VALIDAÇÃO 3: Qualidade dos Dados")
        logger.info("=" * 60)
        results.append(self.validate_data_quality())
        
        # Validação 4: Índices
        logger.info("\n" + "=" * 60)
        logger.info("VALIDAÇÃO 4: Índices")
        logger.info("=" * 60)
        results.append(self.validate_indexes())
        
        # Estatísticas
        logger.info("\n" + "=" * 60)
        logger.info("ESTATÍSTICAS")
        logger.info("=" * 60)
        self.generate_statistics()
        
        # Resumo
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DAS VALIDAÇÕES")
        logger.info("=" * 60)
        
        total = len(results)
        passed = sum(results)
        
        logger.info(f"Total de validações: {total}")
        logger.info(f"Validações passadas: {passed}")
        logger.info(f"Validações falhadas: {total - passed}")
        
        if all(results):
            logger.info("\n🎉 TODAS AS VALIDAÇÕES PASSARAM!")
            return True
        else:
            logger.error("\n❌ ALGUMAS VALIDAÇÕES FALHARAM!")
            return False


def main():
    """Função principal"""
    validator = DataValidator()
    
    try:
        validator.connect()
        success = validator.run_all_validations()
        
        if success:
            exit(0)
        else:
            exit(1)
    
    finally:
        validator.disconnect()


if __name__ == '__main__':
    main()

