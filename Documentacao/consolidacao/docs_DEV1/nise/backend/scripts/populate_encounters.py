"""
============================================================================
NISE TRAINING MODULE - POPULATE ENCOUNTERS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Script para popular tabela de consultas/atendimentos
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

from app.generators.encounter_generator import EncounterGenerator
from app.database import get_db_connection
from app.config import settings
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# POPULATE ENCOUNTERS
# ============================================================================

async def populate_encounters(target_count: int = 500):
    """
    Popular tabela de consultas com dados sintéticos.
    
    Args:
        target_count: Número alvo de consultas (padrão: 500)
    """
    logger.info(f"🚀 Starting encounter generation: ~{target_count} encounters")
    start_time = datetime.now()
    
    # Buscar pacientes e profissionais existentes
    logger.info("📊 Fetching existing patients and practitioners...")
    async with get_db_connection() as conn:
        # Buscar pacientes
        result = await conn.execute(
            "SELECT fhir_id FROM nise_training.patients LIMIT 500"
        )
        patients = result.fetchall()
        patient_ids = [p.fhir_id for p in patients]
        
        # Buscar profissionais
        result = await conn.execute(
            "SELECT fhir_id FROM nise_training.practitioners"
        )
        practitioners = result.fetchall()
        practitioner_ids = [p.fhir_id for p in practitioners]
    
    logger.info(f"✅ Found {len(patient_ids)} patients")
    logger.info(f"✅ Found {len(practitioner_ids)} practitioners")
    
    if not patient_ids:
        logger.error("❌ No patients found! Run populate_patients.py first!")
        return
    
    if not practitioner_ids:
        logger.error("❌ No practitioners found! Run populate_practitioners.py first!")
        return
    
    # Calcular consultas por paciente
    encounters_per_patient = max(1, target_count // len(patient_ids))
    logger.info(f"📊 Target: ~{encounters_per_patient} encounters per patient")
    
    # Gerar consultas
    logger.info("📊 Generating synthetic encounters...")
    generator = EncounterGenerator()
    encounters = generator.generate_batch_for_patients(
        patient_ids, 
        practitioner_ids,
        encounters_per_patient
    )
    logger.info(f"✅ Generated {len(encounters)} encounters")
    
    # Inserir no banco de dados
    logger.info("💾 Inserting encounters into database...")
    
    async with get_db_connection() as conn:
        # Preparar query de inserção
        insert_query = """
            INSERT INTO nise_training.encounters (
                fhir_id, patient_fhir_id, practitioner_fhir_id,
                encounter_type, start_datetime, end_datetime, data
            ) VALUES (
                :fhir_id, :patient_fhir_id, :practitioner_fhir_id,
                :encounter_type, :start_datetime, :end_datetime, :data
            )
        """
        
        # Inserir em lotes de 100
        batch_size = 100
        for i in range(0, len(encounters), batch_size):
            batch = encounters[i:i + batch_size]
            
            # Converter data JSONB para string
            for enc in batch:
                enc['data'] = json.dumps(enc['data'])
            
            # Executar inserção
            await conn.execute_many(insert_query, batch)
            
            logger.info(f"✅ Inserted {min(i + batch_size, len(encounters))}/{len(encounters)} encounters")
        
        await conn.commit()
    
    # Estatísticas
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("🎉 ENCOUNTER GENERATION COMPLETED!")
    logger.info("=" * 80)
    logger.info(f"📊 Total encounters: {len(encounters)}")
    logger.info(f"👥 Total patients: {len(patient_ids)}")
    logger.info(f"👨‍⚕️ Total practitioners: {len(practitioner_ids)}")
    logger.info(f"📈 Avg encounters/patient: {len(encounters) / len(patient_ids):.1f}")
    logger.info(f"⏱️  Duration: {duration:.2f} seconds")
    logger.info(f"🚀 Rate: {len(encounters) / duration:.2f} encounters/second")
    logger.info("=" * 80)
    
    # Verificar inserção
    async with get_db_connection() as conn:
        result = await conn.execute(
            "SELECT COUNT(*) FROM nise_training.encounters"
        )
        count_db = result.scalar()
        logger.info(f"✅ Database verification: {count_db} encounters in database")
        
        # Estatísticas por tipo
        result = await conn.execute("""
            SELECT encounter_type, COUNT(*) as count
            FROM nise_training.encounters
            GROUP BY encounter_type
            ORDER BY count DESC
        """)
        types = result.fetchall()
        
        logger.info("\n📋 Encounters by type:")
        for enc_type in types:
            logger.info(f"  - {enc_type.encounter_type}: {enc_type.count} encounters")
        
        # Amostra de consultas
        result = await conn.execute("""
            SELECT e.encounter_type, e.start_datetime,
                   p.name_given || ' ' || p.name_family as patient_name,
                   pr.name_given || ' ' || pr.name_family as practitioner_name
            FROM nise_training.encounters e
            JOIN nise_training.patients p ON e.patient_fhir_id = p.fhir_id
            JOIN nise_training.practitioners pr ON e.practitioner_fhir_id = pr.fhir_id
            LIMIT 5
        """)
        sample = result.fetchall()
        
        logger.info("\n📋 Sample encounters:")
        for enc in sample:
            logger.info(
                f"  - {enc.encounter_type}: {enc.patient_name} → "
                f"{enc.practitioner_name} ({enc.start_datetime})"
            )

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main function"""
    target_count = 500  # Target: 500 encounters
    
    logger.info("=" * 80)
    logger.info("NISE TRAINING MODULE - ENCOUNTER POPULATION")
    logger.info("=" * 80)
    logger.info(f"Target: ~{target_count} synthetic encounters")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Schema: {settings.DB_SCHEMA}")
    logger.info("=" * 80)
    
    try:
        await populate_encounters(target_count)
        logger.info("\n✅ SUCCESS: Encounter population completed!")
        return 0
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

