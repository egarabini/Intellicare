"""
============================================================================
NISE TRAINING MODULE - POPULATE PATIENTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Script para popular tabela de pacientes
Versão: 1.0
Data: 05/03/2026
Responsável: DEV2
============================================================================
"""

import asyncio
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.generators.patient_generator import PatientGenerator
from app.database import get_db_connection
from app.config import settings
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# POPULATE PATIENTS
# ============================================================================

async def populate_patients(count: int = 5000):
    """
    Popular tabela de pacientes com dados sintéticos.
    
    Args:
        count: Número de pacientes a gerar (padrão: 5000)
    """
    logger.info(f"🚀 Starting patient generation: {count} patients")
    start_time = datetime.now()
    
    # Gerar pacientes
    logger.info("📊 Generating synthetic patients...")
    generator = PatientGenerator()
    patients = generator.generate_batch(count)
    logger.info(f"✅ Generated {len(patients)} patients")
    
    # Inserir no banco de dados
    logger.info("💾 Inserting patients into database...")
    
    async with get_db_connection() as conn:
        # Preparar query de inserção
        insert_query = """
            INSERT INTO nise_training.patients (
                fhir_id, cpf, cns, name_given, name_family,
                birth_date, gender, municipality_code, municipality_name, data
            ) VALUES (
                :fhir_id, :cpf, :cns, :name_given, :name_family,
                :birth_date, :gender, :municipality_code, :municipality_name, :data
            )
        """
        
        # Inserir em lotes de 100
        batch_size = 100
        for i in range(0, len(patients), batch_size):
            batch = patients[i:i + batch_size]
            
            # Converter data JSONB para string
            for patient in batch:
                patient['data'] = json.dumps(patient['data'])
            
            # Executar inserção
            await conn.execute_many(insert_query, batch)
            
            logger.info(f"✅ Inserted {min(i + batch_size, len(patients))}/{len(patients)} patients")
        
        await conn.commit()
    
    # Estatísticas
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("🎉 PATIENT GENERATION COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"📊 Total patients: {len(patients)}")
    logger.info(f"⏱️  Duration: {duration:.2f} seconds")
    logger.info(f"🚀 Rate: {len(patients) / duration:.2f} patients/second")
    logger.info("=" * 80)
    
    # Verificar inserção
    async with get_db_connection() as conn:
        result = await conn.execute(
            "SELECT COUNT(*) FROM nise_training.patients"
        )
        count_db = result.scalar()
        logger.info(f"✅ Database verification: {count_db} patients in database")
        
        # Amostra de pacientes
        result = await conn.execute(
            "SELECT fhir_id, name_given, name_family, cpf, birth_date "
            "FROM nise_training.patients LIMIT 5"
        )
        sample = result.fetchall()
        
        logger.info("\n📋 Sample patients:")
        for patient in sample:
            logger.info(
                f"  - {patient.name_given} {patient.name_family} "
                f"(CPF: {patient.cpf}, Birth: {patient.birth_date})"
            )

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main function"""
    count = settings.SYNTHETIC_PATIENTS_COUNT
    
    logger.info("=" * 80)
    logger.info("NISE TRAINING MODULE - PATIENT POPULATION")
    logger.info("=" * 80)
    logger.info(f"Target: {count} synthetic patients")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Schema: {settings.DB_SCHEMA}")
    logger.info("=" * 80)
    
    try:
        await populate_patients(count)
        logger.info("\n✅ SUCCESS: Patient population completed!")
        return 0
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

