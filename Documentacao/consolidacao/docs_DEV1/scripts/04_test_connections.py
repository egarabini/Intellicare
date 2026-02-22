#!/usr/bin/env python3
"""
Script de Teste de Conexões - Projeto 02
Testa conectividade com OLTP e OLAP e valida permissões
"""

import psycopg2
import logging
from typing import Dict, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectionTester:
    """Classe para testar conexões aos bancos de dados"""
    
    # Configurações de conexão
    OLTP_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_oltp',
        'user': 'intellicare_app',
        'password': 'IntelliCare@2026!OLTP'
    }
    
    OLAP_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'intellicare_olap',
        'user': 'intellicare_analytics',
        'password': 'IntelliCare@2026!OLAP'
    }
    
    def test_connection(self, config: Dict, db_name: str) -> Tuple[bool, str]:
        """Testa conexão com um banco de dados"""
        try:
            conn = psycopg2.connect(**config)
            cur = conn.cursor()
            
            # Testar query simples
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            logger.info(f"✅ Conexão {db_name} OK")
            return True, version
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar {db_name}: {e}")
            return False, str(e)
    
    def test_oltp_permissions(self) -> bool:
        """Testa permissões de leitura/escrita no OLTP"""
        logger.info("🔐 Testando permissões OLTP...")
        
        try:
            conn = psycopg2.connect(**self.OLTP_CONFIG)
            cur = conn.cursor()
            
            # Testar SELECT
            cur.execute("SELECT COUNT(*) FROM donabedian.indicadores;")
            count = cur.fetchone()[0]
            logger.info(f"  ✅ SELECT OK - {count} indicadores")
            
            # Testar INSERT
            cur.execute("""
                INSERT INTO donabedian.indicadores 
                (nome, tipo, meta_valor, meta_unidade)
                VALUES ('Teste Conexão', 'estrutura', 100, '%')
                RETURNING id;
            """)
            test_id = cur.fetchone()[0]
            logger.info(f"  ✅ INSERT OK - ID {test_id}")
            
            # Testar UPDATE
            cur.execute("""
                UPDATE donabedian.indicadores 
                SET nome = 'Teste Conexão Atualizado'
                WHERE id = %s;
            """, (test_id,))
            logger.info(f"  ✅ UPDATE OK")
            
            # Testar DELETE
            cur.execute("""
                DELETE FROM donabedian.indicadores 
                WHERE id = %s;
            """, (test_id,))
            logger.info(f"  ✅ DELETE OK")
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("✅ Permissões OLTP: READ/WRITE OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar permissões OLTP: {e}")
            return False
    
    def test_olap_permissions(self) -> bool:
        """Testa permissões de somente leitura no OLAP"""
        logger.info("🔐 Testando permissões OLAP...")
        
        try:
            conn = psycopg2.connect(**self.OLAP_CONFIG)
            cur = conn.cursor()
            
            # Testar SELECT (deve funcionar)
            cur.execute("SELECT COUNT(*) FROM analytics_donabedian.fato_medicoes;")
            count = cur.fetchone()[0]
            logger.info(f"  ✅ SELECT OK - {count} medições")
            
            # Testar INSERT (deve falhar)
            try:
                cur.execute("""
                    INSERT INTO analytics_donabedian.fato_medicoes 
                    (indicador_hash, periodo_ano, periodo_mes, valor_medido)
                    VALUES ('test', 2026, 2, 100);
                """)
                conn.commit()
                logger.error("  ❌ INSERT deveria ter falhado (usuário read-only)")
                return False
            except psycopg2.Error:
                logger.info("  ✅ INSERT bloqueado (esperado para read-only)")
                conn.rollback()
            
            cur.close()
            conn.close()
            
            logger.info("✅ Permissões OLAP: READ-ONLY OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar permissões OLAP: {e}")
            return False
    
    def test_schemas(self) -> bool:
        """Testa existência de schemas e tabelas"""
        logger.info("📋 Testando schemas e tabelas...")
        
        try:
            # Testar OLTP
            conn_oltp = psycopg2.connect(**self.OLTP_CONFIG)
            cur_oltp = conn_oltp.cursor()
            
            cur_oltp.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname IN ('donabedian', 'wanda')
                ORDER BY schemaname, tablename;
            """)
            
            tables_oltp = cur_oltp.fetchall()
            logger.info(f"  ✅ OLTP: {len(tables_oltp)} tabelas encontradas")
            for schema, table in tables_oltp:
                logger.info(f"    - {schema}.{table}")
            
            cur_oltp.close()
            conn_oltp.close()
            
            # Testar OLAP
            conn_olap = psycopg2.connect(**self.OLAP_CONFIG)
            cur_olap = conn_olap.cursor()
            
            cur_olap.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname IN ('analytics_donabedian', 'analytics_wanda')
                ORDER BY schemaname, tablename;
            """)
            
            tables_olap = cur_olap.fetchall()
            logger.info(f"  ✅ OLAP: {len(tables_olap)} tabelas encontradas")
            for schema, table in tables_olap:
                logger.info(f"    - {schema}.{table}")
            
            cur_olap.close()
            conn_olap.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar schemas: {e}")
            return False
    
    def test_anonymization_functions(self) -> bool:
        """Testa funções de anonimização"""
        logger.info("🔒 Testando funções de anonimização...")
        
        try:
            conn = psycopg2.connect(**self.OLAP_CONFIG)
            cur = conn.cursor()
            
            # Testar hash_id
            cur.execute("SELECT hash_id(123);")
            hash_result = cur.fetchone()[0]
            logger.info(f"  ✅ hash_id(123) = {hash_result[:16]}...")
            
            # Testar categorizar_valor
            cur.execute("SELECT categorizar_valor(50, 30, 70);")
            cat_result = cur.fetchone()[0]
            logger.info(f"  ✅ categorizar_valor(50, 30, 70) = {cat_result}")
            
            # Testar generalizar_data
            cur.execute("SELECT generalizar_data(CURRENT_TIMESTAMP);")
            gen_result = cur.fetchone()[0]
            logger.info(f"  ✅ generalizar_data(now) = {gen_result}")
            
            cur.close()
            conn.close()
            
            logger.info("✅ Funções de anonimização OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar funções: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Executa todos os testes"""
        logger.info("🚀 Iniciando testes de conexão...\n")
        
        results = []
        
        # Teste 1: Conexão OLTP
        logger.info("=" * 60)
        logger.info("TESTE 1: Conexão OLTP")
        logger.info("=" * 60)
        success, msg = self.test_connection(self.OLTP_CONFIG, "OLTP")
        results.append(success)
        
        # Teste 2: Conexão OLAP
        logger.info("\n" + "=" * 60)
        logger.info("TESTE 2: Conexão OLAP")
        logger.info("=" * 60)
        success, msg = self.test_connection(self.OLAP_CONFIG, "OLAP")
        results.append(success)
        
        # Teste 3: Permissões OLTP
        logger.info("\n" + "=" * 60)
        logger.info("TESTE 3: Permissões OLTP (READ/WRITE)")
        logger.info("=" * 60)
        results.append(self.test_oltp_permissions())
        
        # Teste 4: Permissões OLAP
        logger.info("\n" + "=" * 60)
        logger.info("TESTE 4: Permissões OLAP (READ-ONLY)")
        logger.info("=" * 60)
        results.append(self.test_olap_permissions())
        
        # Teste 5: Schemas e Tabelas
        logger.info("\n" + "=" * 60)
        logger.info("TESTE 5: Schemas e Tabelas")
        logger.info("=" * 60)
        results.append(self.test_schemas())
        
        # Teste 6: Funções de Anonimização
        logger.info("\n" + "=" * 60)
        logger.info("TESTE 6: Funções de Anonimização")
        logger.info("=" * 60)
        results.append(self.test_anonymization_functions())
        
        # Resumo
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DOS TESTES")
        logger.info("=" * 60)
        
        total = len(results)
        passed = sum(results)
        
        logger.info(f"Total de testes: {total}")
        logger.info(f"Testes passados: {passed}")
        logger.info(f"Testes falhados: {total - passed}")
        
        if all(results):
            logger.info("\n🎉 TODOS OS TESTES PASSARAM!")
            return True
        else:
            logger.error("\n❌ ALGUNS TESTES FALHARAM!")
            return False


def main():
    """Função principal"""
    tester = ConnectionTester()
    success = tester.run_all_tests()
    
    if success:
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()

