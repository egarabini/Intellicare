"""
============================================================================
NISE TRAINING MODULE - POPULATE OBSERVATIONS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Script para popular tabela de observações
Versão: 1.0
Data: 06/03/2026
Responsável: DEV2
============================================================================
"""

import asyncio
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.generators.observation_generator import ObservationGenerator
from app.database import get_db_connection
from app.config import settings
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# POPULATE OBSERVATIONS
# ============================================================================

async def populate_observations(target_count: int = 20000):
    """
    Popular tabela de observações com dados sintéticos.
    
    Args:
        target_count: Número alvo de observações (padrão: 20000)
    """
    logger.info(f"🚀 Starting observation generation: ~{target_count} observations")
    start_time = datetime.now()
    
    # Buscar pacientes existentes
    logger.info("📊 Fetching existing patients...")
    async with get_db_connection() as conn:
        result = await conn.execute(
            "SELECT fhir_id FROM nise_training.patients"
        )
        patients = result.fetchall()
        patient_ids = [p.fhir_id for p in patients]
    
    logger.info(f"✅ Found {len(patient_ids)} patients")
    
    if not patient_ids:
        logger.error("❌ No patients found! Run populate_patients.py first!")
        return
    
    # Calcular observações por paciente
    observations_per_patient = target_count // len(patient_ids)
    logger.info(f"📊 Target: ~{observations_per_patient} observations per patient")
    
    # Gerar observações
    logger.info("📊 Generating synthetic observations...")
    generator = ObservationGenerator()
    observations = generator.generate_batch_for_patients(
        patient_ids, 
        observations_per_patient
    )
    logger.info(f"✅ Generated {len(observations)} observations")
    
    # Inserir no banco de dados
    logger.info("💾 Inserting observations into database...")
    
    async with get_db_connection() as conn:
        # Preparar query de inserção
        insert_query = """
            INSERT INTO nise_training.observations (
                fhir_id, patient_fhir_id, code_loinc, code_display,
                value_quantity, value_unit, effective_datetime, data
            ) VALUES (
                :fhir_id, :patient_fhir_id, :code_loinc, :code_display,
                :value_quantity, :value_unit, :effective_datetime, :data
            )
        """
        
        # Inserir em lotes de 100
        batch_size = 100
        for i in range(0, len(observations), batch_size):
            batch = observations[i:i + batch_size]
            
            # Converter data JSONB para string
            for obs in batch:
                obs['data'] = json.dumps(obs['data'])
            
            # Executar inserção
            await conn.execute_many(insert_query, batch)
            
            logger.info(f"✅ Inserted {min(i + batch_size, len(observations))}/{len(observations)} observations")
        
        await conn.commit()
    
    # Estatísticas
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("🎉 OBSERVATION GENERATION COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"📊 Total observations: {len(observations)}")
    logger.info(f"👥 Total patients: {len(patient_ids)}")
    logger.info(f"📈 Avg observations/patient: {len(observations) / len(patient_ids):.1f}")
    logger.info(f"⏱️  Duration: {duration:.2f} seconds")
    logger.info(f"🚀 Rate: {len(observations) / duration:.2f} observations/second")
    logger.info("=" * 80)
    
    # Verificar inserção
    async with get_db_connection() as conn:
        result = await conn.execute(
            "SELECT COUNT(*) FROM nise_training.observations"
        )
        count_db = result.scalar()
        logger.info(f"✅ Database verification: {count_db} observations in database")
        
        # Estatísticas por código LOINC
        result = await conn.execute("""
            SELECT code_display, COUNT(*) as count
            FROM nise_training.observations
            GROUP BY code_display
            ORDER BY count DESC
            LIMIT 10
        """)
        top_codes = result.fetchall()
        
        logger.info("\n📋 Top 10 observation types:")
        for code in top_codes:
            logger.info(f"  - {code.code_display}: {code.count} observations")
        
        # Amostra de observações
        result = await conn.execute("""
            SELECT o.code_display, o.value_quantity, o.value_unit, 
                   p.name_given, p.name_family
            FROM nise_training.observations o
            JOIN nise_training.patients p ON o.patient_fhir_id = p.fhir_id
            LIMIT 5
        """)
        sample = result.fetchall()
        
        logger.info("\n📋 Sample observations:")
        for obs in sample:
            logger.info(
                f"  - {obs.name_given} {obs.name_family}: "
                f"{obs.code_display} = {obs.value_quantity} {obs.value_unit}"
            )

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main function"""
    target_count = settings.SYNTHETIC_OBSERVATIONS_COUNT
    
    logger.info("=" * 80)
    logger.info("NISE TRAINING MODULE - OBSERVATION POPULATION")
    logger.info("=" * 80)
    logger.info(f"Target: ~{target_count} synthetic observations")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Schema: {settings.DB_SCHEMA}")
    logger.info("=" * 80)
    
    try:
        await populate_observations(target_count)
        logger.info("\n✅ SUCCESS: Observation population completed!")
        return 0
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

