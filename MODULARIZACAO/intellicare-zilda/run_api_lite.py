
import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from typing import Any, List
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Ensure package is in path
sys.path.insert(0, ".")

from zilda.engine.models import HealthEstablishment, HealthRegion, HealthUnitType, CnesValidation
from zilda.config import ZildaConfig
from zilda.engine.territorial import TerritorialEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zilda.lite")

# --- Mock Data ---

class MockData:
    CITIES = {
        "355030": {
            "name": "SAO PAULO",
            "state": "SP",
            "region": "35016",
            "region_name": "SAO PAULO",
            "macro": "3501",
            "macro_name": "RRAS 6",
            "population": 11451245,
            "ibge_context": {
                "idh": 0.805,
                "pib_per_capita": 63000.00,
                "area_km2": 1521.11,
                "densidade": 7398.26
            },
            "rnds_stats": {
                "total_records": 15432000,
                "last_update": "2024-02-17T10:30:00",
                "vaccination_coverage": 92.5
            }
        },
        "330455": {
            "name": "RIO DE JANEIRO",
            "state": "RJ",
            "region": "33005",
            "region_name": "METROPOLITANA I",
            "macro": "3301",
            "macro_name": "METROPOLITANA",
            "population": 6211423,
            "ibge_context": {
                "idh": 0.799,
                "pib_per_capita": 54000.00,
                "area_km2": 1200.25,
                "densidade": 5175.12
            },
            "rnds_stats": {
                "total_records": 8120500,
                "last_update": "2024-02-17T09:45:00",
                "vaccination_coverage": 88.2
            }
        },
        "410690": {
            "name": "CURITIBA",
            "state": "PR",
            "region": "41002",
            "region_name": "2A RS METROPOLITANA",
            "macro": "4101",
            "macro_name": "LESTE",
            "population": 1773733,
            "ibge_context": {
                "idh": 0.823,
                "pib_per_capita": 49000.00,
                "area_km2": 435.03,
                "densidade": 4077.20
            },
            "rnds_stats": {
                "total_records": 2500100,
                "last_update": "2024-02-17T11:00:00",
                "vaccination_coverage": 95.1
            }
        },
        "292740": {
            "name": "SALVADOR",
            "state": "BA",
            "region": "29010",
            "region_name": "SALVADOR",
            "macro": "2901",
            "macro_name": "LESTE",
            "population": 2418005,
             "ibge_context": {
                "idh": 0.759,
                "pib_per_capita": 22000.00,
                "area_km2": 692.81,
                "densidade": 3489.90
            },
            "rnds_stats": {
                "total_records": 3100800,
                "last_update": "2024-02-17T08:15:00",
                "vaccination_coverage": 85.5
            }
        }
    }

    ESTABLISHMENTS = [
        HealthEstablishment(
            cnes_code="2077485", legal_name="HOSPITAL MUNICIPAL DE EXEMPLO", fantasy_name="HOSPITAL EXEMPLO SP",
            unit_type_code="05", unit_type_description="HOSPITAL GERAL", state_code="35", city_code="355030", city_name="SAO PAULO",
            active=True, has_surgical_center=True,
            cnpj="00.000.000/0001-00", address="RUA EXEMPLO, 123", neighborhood="CENTRO", phone="(11) 3333-4444"
        ),
        HealthEstablishment(
            cnes_code="1234567", legal_name="UBS VILA EXEMPLO", fantasy_name="UBS VILA EXEMPLO",
            unit_type_code="02", unit_type_description="CENTRO DE SAUDE/UNIDADE BASICA", state_code="35", city_code="355030", city_name="SAO PAULO",
            active=True,
            cnpj="00.000.000/0002-00", address="RUA DA VILA, 456", neighborhood="VILA EXEMPLO", phone="(11) 5555-6666"
        ),
         HealthEstablishment(
            cnes_code="9876543", legal_name="HOSPITAL SOUZA AGUIAR MOCK", fantasy_name="HOSPITAL SOUZA AGUIAR",
            unit_type_code="05", unit_type_description="HOSPITAL GERAL", state_code="33", city_code="330455", city_name="RIO DE JANEIRO",
            active=True, has_surgical_center=True,
            cnpj="00.000.000/0003-00", address="PRACA DA REPUBLICA, 111", neighborhood="CENTRO", phone="(21) 2222-3333"
        ),
        HealthEstablishment(
            cnes_code="1122334", legal_name="UPA COPACABANA MOCK", fantasy_name="UPA COPACABANA",
            unit_type_code="73", unit_type_description="PRONTO ATENDIMENTO", state_code="33", city_code="330455", city_name="RIO DE JANEIRO",
            active=True,
            cnpj="00.000.000/0004-00", address="AV COPACABANA, 999", neighborhood="COPACABANA", phone="(21) 9999-8888"
        ),
         HealthEstablishment(
            cnes_code="5566778", legal_name="HOSPITAL DE CLINICAS UFPR MOCK", fantasy_name="HC UFPR",
            unit_type_code="05", unit_type_description="HOSPITAL GERAL", state_code="41", city_code="410690", city_name="CURITIBA",
            active=True,
            cnpj="00.000.000/0005-00", address="RUA GENERAL CARNEIRO, 181", neighborhood="ALTO DA GLORIA", phone="(41) 3360-1800"
        ),
         HealthEstablishment(
            cnes_code="9988776", legal_name="HOSPITAL GERAL DO ESTADO BA MOCK", fantasy_name="HGE SALVADOR",
            unit_type_code="05", unit_type_description="HOSPITAL GERAL", state_code="29", city_code="292740", city_name="SALVADOR",
            active=True,
            cnpj="00.000.000/0006-00", address="AV VASCO DA GAMA, S/N", neighborhood="BROTAS", phone="(71) 3117-5999"
        )
    ]


# --- Mock Client ---

class MockCnesClient:
    def __init__(self, *args, **kwargs):
        pass

    def close(self):
        pass

    def get_unit_types(self) -> List[HealthUnitType]:
        return [
            HealthUnitType(code="05", description="HOSPITAL GERAL"),
            HealthUnitType(code="07", description="HOSPITAL ESPECIALIZADO"),
            HealthUnitType(code="01", description="POSTO DE SAUDE"),
            HealthUnitType(code="02", description="CENTRO DE SAUDE/UNIDADE BASICA"),
            HealthUnitType(code="36", description="CLINICA/CENTRO DE ESPECIALIDADE"),
        ]

    def search_establishments(self, limit=20, offset=0, city_code=None, state_code=None, **kwargs) -> List[HealthEstablishment]:
        results = MockData.ESTABLISHMENTS
        
        # Simple Mock Filtering
        if city_code:
            results = [e for e in results if e.city_code == city_code]
        elif state_code:
            results = [e for e in results if e.state_code == state_code]
            
        # Text search simulation (if passed via kwargs in real app, but here we scan common fields)
        # Note: The real engine passes specific fields. If a user searches "Sao Paulo" in the frontend,
        # usually the frontend or the territorial engine resolves to a city_code.
        # But for this Lite mode, we can imply city context if not filtered.
        
        return results

    def get_establishment_by_cnes(self, cnes_code: str) -> HealthEstablishment | None:
        for est in MockData.ESTABLISHMENTS:
            if est.cnes_code == cnes_code:
                return est
        
        # Dynamic fallback
        return HealthEstablishment(
            cnes_code=cnes_code,
            legal_name=f"ESTABELECIMENTO GENERIDO {cnes_code}",
            fantasy_name=f"HOSPITAL {cnes_code}",
            unit_type_code="05",
            unit_type_description="HOSPITAL GERAL",
            state_code="35",
            city_code="355030",
            city_name="SAO PAULO",
            active=True,
            cnpj="00.000.000/0000-00", address="ENDERECO GENERICO", neighborhood="BAIRRO GENERICO", phone="(00) 0000-0000"
        )

    def get_health_regions(self, limit=100, offset=0, city_code=None, state_code=None, **kwargs) -> List[HealthRegion]:
        regions = []
        for code, data in MockData.CITIES.items():
            if city_code and code != city_code:
                continue
            if state_code and data["state"] != state_code:
                continue
                
            regions.append(HealthRegion(
                city_code=code,
                city_name=data["name"],
                state_code=data["state"], # Simplified mapping (requires lookup table normally)
                state_name=data["state"], # Mocked
                region_code=data["region"],
                region_name=data["region_name"],
                macro_region_code=data["macro"],
                macro_region_name=data["macro_name"],
                population=data["population"]
            ))
        return regions

    def validate_cnes(self, cnes_code: str) -> CnesValidation:
        digits = "".join(c for c in cnes_code if c.isdigit())
        if len(digits) != 7:
            return CnesValidation(
                cnes_code=cnes_code,
                valid_format=False,
                found=False,
                message=f"CNES invalido: esperados 7 digitos, recebidos {len(digits)}",
            )
        
        est = self.get_establishment_by_cnes(digits)
        if est:
             return CnesValidation(
                cnes_code=digits,
                valid_format=True,
                found=True,
                establishment=est,
                message=f"CNES {digits} encontrado: {est.fantasy_name}",
            )
            
        return CnesValidation(
            cnes_code=digits,
            valid_format=True,
            found=False,
            message=f"CNES {digits} nao encontrado",
        )

# --- Extended Endpoints (IBGE/RNDS mocks) ---

extra_router = APIRouter(prefix="/api/v1")

@extra_router.get("/ibge/context/{city_code}")
def get_ibge_context(city_code: str):
    data = MockData.CITIES.get(city_code)
    if not data:
        return {"error": "Município não encontrado na base IBGE mock"}
    return data["ibge_context"]

@extra_router.get("/rnds/stats/{city_code}")
def get_rnds_stats(city_code: str):
    data = MockData.CITIES.get(city_code)
    if not data:
        return {"error": "Dados RNDS não encontrados para este município"}
    return data["rnds_stats"]

# --- Startup ---

from fastapi.responses import RedirectResponse

@extra_router.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    try:
        from zilda.api.app import create_app, _state
        
        # Override client in _state BEFORE app creation/startup
        mock_client = MockCnesClient()
        _state["client"] = mock_client
        _state["config"] = ZildaConfig()
        _state["engine"] = TerritorialEngine(mock_client)
        
        logger.info("Setting up Zilda Lite (Mocked CNES + IBGE + RNDS)...")
        app = create_app()

        # Configurar CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include extra routes for RNDS/IBGE
        app.include_router(extra_router)
        
        logger.info("🚀 Starting Zilda API (Lite Mode + Extended Mocks) on port 8003...")
        uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
        
    except Exception as e:
        logger.error(f"Failed to start Zilda Lite: {e}")
        sys.exit(1)
