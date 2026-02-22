"""
Database connection and session management for Oswaldo.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("OSWALDO_DB_USER", "admin_intellicare")
DB_PASSWORD = os.getenv("OSWALDO_DB_PASSWORD", "Crazy#57LB")
DB_HOST = os.getenv("OSWALDO_DB_HOST", "161.97.141.186")
DB_PORT = os.getenv("OSWALDO_DB_PORT", "5432")
DB_NAME = os.getenv("OSWALDO_DB_NAME", "intellicareDB")
DB_SCHEMA = os.getenv("OSWALDO_DB_SCHEMA", "oswaldo")

# Build connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections every hour
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Set default schema for all connections
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set search_path to use Oswaldo schema."""
    dbapi_conn.set_isolation_level(0)
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET search_path TO {DB_SCHEMA}, public")
    cursor.close()
    dbapi_conn.set_isolation_level(1)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables in Oswaldo schema."""
    from src.oswaldo.models.oswaldo_models import Base
    
    # Create schema if not exists
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        conn.commit()
    
    # Create tables in the default schema (which is set via search_path event)
    Base.metadata.create_all(bind=engine)
    
    print(f"✓ Database initialized in schema '{DB_SCHEMA}' on {DB_HOST}:{DB_PORT}/{DB_NAME}")

