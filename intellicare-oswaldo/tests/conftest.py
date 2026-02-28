"""Fixtures compartilhadas para testes do Oswaldo."""

from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from oswaldo.profiles.registry import DiseaseProfileRegistry
from src.oswaldo.models.oswaldo_models import Base


PROFILES_DIR = Path(__file__).parent.parent / "oswaldo" / "profiles" / "diseases"


@pytest.fixture
def registry() -> DiseaseProfileRegistry:
    """Registry carregado com perfis reais."""
    reg = DiseaseProfileRegistry(PROFILES_DIR)
    reg.load_all()
    return reg


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_condicao_data():
    """Sample chronic condition data."""
    from datetime import date
    return {
        "paciente_cpf_hash": "abc123def456ghi789jkl",
        "cid10": "I10",  # HAS
        "data_diagnostico": date.today(),
        "medico_diagnosticador": "Dr. João Silva",
        "confirmacao_exames": True,
        "gravidade_inicial": "MODERADA"
    }


@pytest.fixture
def sample_exame_data():
    """Sample exam data for classification."""
    return {
        "glicemia": 180,
        "hba1c": 7.5,
        "creatinina": 1.4,
        "tfge": 52,
        "pa_sistolica": 160,
        "pa_diastolica": 100,
        "kolesterol_total": 240,
        "ldl": 160,
        "potassio": 4.5
    }
