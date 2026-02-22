"""
============================================================================
NISE TRAINING MODULE - DATABASE CONNECTION
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Database Connection & Session Management
Versão: 1.0
Data: 04/03/2026
Responsável: DEV2
============================================================================
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import asynccontextmanager
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE
# ============================================================================

# Criar engine assíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries em modo debug
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verificar conexões antes de usar
    poolclass=QueuePool,
)

# ============================================================================
# SESSION FACTORY
# ============================================================================

# Criar session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ============================================================================
# BASE CLASS (para models SQLAlchemy, se necessário)
# ============================================================================

Base = declarative_base()

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_db() -> AsyncSession:
    """
    Dependency para obter sessão do banco de dados.
    
    Uso:
        @app.get("/patients")
        async def get_patients(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

async def init_db():
    """Inicializar banco de dados (criar tabelas se necessário)"""
    logger.info("🔌 Initializing database...")
    
    try:
        async with engine.begin() as conn:
            # Verificar conexão
            await conn.execute("SELECT 1")
            logger.info("✅ Database connection successful")
            
            # Verificar schema nise_training
            result = await conn.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'nise_training'"
            )
            if result.scalar():
                logger.info("✅ Schema 'nise_training' exists")
            else:
                logger.warning("⚠️ Schema 'nise_training' not found - run SQL scripts first!")
            
            # Verificar pgvector extension
            result = await conn.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            if result.scalar():
                logger.info("✅ pgvector extension installed")
            else:
                logger.warning("⚠️ pgvector extension not found!")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_db():
    """Fechar conexões do banco de dados"""
    logger.info("🛑 Closing database connections...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# ============================================================================
# RAW SQL EXECUTION (para queries diretas)
# ============================================================================

@asynccontextmanager
async def get_db_connection():
    """
    Context manager para obter conexão direta (raw SQL).
    
    Uso:
        async with get_db_connection() as conn:
            result = await conn.execute("SELECT * FROM nise_training.patients")
    """
    async with engine.begin() as conn:
        try:
            yield conn
        except Exception:
            await conn.rollback()
            raise


async def execute_query(query: str, params: dict = None):
    """
    Executar query SQL direta.
    
    Args:
        query: SQL query string
        params: Parâmetros para query (opcional)
    
    Returns:
        Result object
    """
    async with get_db_connection() as conn:
        if params:
            result = await conn.execute(query, params)
        else:
            result = await conn.execute(query)
        return result


async def fetch_one(query: str, params: dict = None):
    """Executar query e retornar uma linha"""
    result = await execute_query(query, params)
    return result.fetchone()


async def fetch_all(query: str, params: dict = None):
    """Executar query e retornar todas as linhas"""
    result = await execute_query(query, params)
    return result.fetchall()


# ============================================================================
# HEALTH CHECK
# ============================================================================

async def check_db_health() -> dict:
    """
    Verificar saúde do banco de dados.
    
    Returns:
        dict com status e informações
    """
    try:
        async with get_db_connection() as conn:
            # Verificar conexão
            await conn.execute("SELECT 1")
            
            # Contar pacientes
            result = await conn.execute(
                "SELECT COUNT(*) FROM nise_training.patients"
            )
            patients_count = result.scalar() or 0
            
            # Contar observações
            result = await conn.execute(
                "SELECT COUNT(*) FROM nise_training.observations"
            )
            observations_count = result.scalar() or 0
            
            return {
                "status": "healthy",
                "connected": True,
                "schema": "nise_training",
                "patients_count": patients_count,
                "observations_count": observations_count
            }
            
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }

