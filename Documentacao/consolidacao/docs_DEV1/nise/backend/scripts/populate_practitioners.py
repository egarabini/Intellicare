"""
============================================================================
NISE TRAINING MODULE - POPULATE PRACTITIONERS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Script para popular tabela de profissionais
Versão: 1.0
Data: 10/03/2026
Responsável: DEV2
============================================================================
"""

import asyncio
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.generators.practitioner_generator import PractitionerGenerator
from app.database import get_db_connection
from app.config import settings
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# POPULATE PRACTITIONERS
# ============================================================================

async def populate_practitioners(count: int = 1000):
    """
    Popular tabela de profissionais com dados sintéticos.
    
    Args:
        count: Número de profissionais (padrão: 1000)
    """
    logger.info(f"🚀 Starting practitioner generation: {count} practitioners")
    start_time = datetime.now()
    
    # Gerar profissionais
    logger.info("📊 Generating synthetic practitioners...")
    generator = PractitionerGenerator()
    practitioners = generator.generate_batch(count)
    logger.info(f"✅ Generated {len(practitioners)} practitioners")
    
    # Inserir no banco de dados
    logger.info("💾 Inserting practitioners into database...")
    
    async with get_db_connection() as conn:
        # Preparar query de inserção
        insert_query = """
            INSERT INTO nise_training.practitioners (
                fhir_id, cpf, cns, name_given, name_family,
                specialty, crm, data
            ) VALUES (
                :fhir_id, :cpf, :cns, :name_given, :name_family,
                :specialty, :crm, :data
            )
        """
        
        # Inserir em lotes de 100
        batch_size = 100
        for i in range(0, len(practitioners), batch_size):
            batch = practitioners[i:i + batch_size]
            
            # Converter data JSONB para string
            for pract in batch:
                pract['data'] = json.dumps(pract['data'])
            
            # Executar inserção
            await conn.execute_many(insert_query, batch)
            
            logger.info(f"✅ Inserted {min(i + batch_size, len(practitioners))}/{len(practitioners)} practitioners")
        
        await conn.commit()
    
    # Estatísticas
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("🎉 PRACTITIONER GENERATION COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"📊 Total practitioners: {len(practitioners)}")
    logger.info(f"⏱️  Duration: {duration:.2f} seconds")
    logger.info(f"🚀 Rate: {len(practitioners) / duration:.2f} practitioners/second")
    logger.info("=" * 80)
    
    # Verificar inserção
    async with get_db_connection() as conn:
        result = await conn.execute(
            "SELECT COUNT(*) FROM nise_training.practitioners"
        )
        count_db = result.scalar()
        logger.info(f"✅ Database verification: {count_db} practitioners in database")
        
        # Estatísticas por especialidade
        result = await conn.execute("""
            SELECT specialty, COUNT(*) as count
            FROM nise_training.practitioners
            GROUP BY specialty
            ORDER BY count DESC
        """)
        specialties = result.fetchall()
        
        logger.info("\n📋 Practitioners by specialty:")
        for spec in specialties:
            logger.info(f"  - {spec.specialty}: {spec.count} practitioners")
        
        # Amostra de profissionais
        result = await conn.execute("""
            SELECT name_given, name_family, specialty, crm
            FROM nise_training.practitioners
            LIMIT 5
        """)
        sample = result.fetchall()
        
        logger.info("\n📋 Sample practitioners:")
        for pract in sample:
            logger.info(
                f"  - {pract.name_given} {pract.name_family} - "
                f"{pract.specialty} (CRM: {pract.crm})"
            )

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main function"""
    count = 1000  # Target: 1,000 practitioners
    
    logger.info("=" * 80)
    logger.info("NISE TRAINING MODULE - PRACTITIONER POPULATION")
    logger.info("=" * 80)
    logger.info(f"Target: {count} synthetic practitioners")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Schema: {settings.DB_SCHEMA}")
    logger.info("=" * 80)
    
    try:
        await populate_practitioners(count)
        logger.info("\n✅ SUCCESS: Practitioner population completed!")
        return 0
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

