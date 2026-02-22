
import logging
import sys
import uvicorn
from typing import Any, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grahame.lite")

app = FastAPI(
    title="IntelliCare Grahame (FHIR)",
    description="Agente de Interoperabilidade FHIR",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mock Data (FHIR Resources) ---

class MockFhir:
    PATIENTS = [
        {
            "resourceType": "Patient",
            "id": "123",
            "active": True,
            "name": [{"family": "Silva", "given": ["João"]}],
            "gender": "male",
            "birthDate": "1980-01-01",
            "address": [{"city": "São Paulo", "state": "SP"}]
        },
        {
            "resourceType": "Patient",
            "id": "456",
            "active": True,
            "name": [{"family": "Santos", "given": ["Maria"]}],
            "gender": "female",
            "birthDate": "1990-05-15",
            "address": [{"city": "Rio de Janeiro", "state": "RJ"}]
        }
    ]

    OBSERVATIONS = [
        {
            "resourceType": "Observation",
            "id": "obs-1",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
            "subject": {"reference": "Patient/123"},
            "valueQuantity": {"value": 80, "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
        },
        {
            "resourceType": "Observation",
            "id": "obs-2",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]},
            "subject": {"reference": "Patient/123"},
            "valueQuantity": {"value": 36.6, "unit": "Cel", "system": "http://unitsofmeasure.org", "code": "Cel"}
        }
    ]

# --- Endpoints ---

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "module": "Grahame (FHIR Mock)"}

@app.get("/api/v1/Patient")
def search_patients(name: str = None):
    results = MockFhir.PATIENTS
    if name:
        term = name.lower()
        results = [p for p in results if term in p["name"][0]["family"].lower() or term in p["name"][0]["given"][0].lower()]
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(results),
        "entry": [{"resource": p} for p in results]
    }

@app.get("/api/v1/Patient/{patient_id}")
def get_patient(patient_id: str):
    for p in MockFhir.PATIENTS:
        if p["id"] == patient_id:
            return p
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/api/v1/Observation")
def search_observations(patient: str = None):
    results = MockFhir.OBSERVATIONS
    if patient:
        # patient param usually is "Patient/123" or just "123"
        ref = patient if "Patient/" in patient else f"Patient/{patient}"
        results = [o for o in results if o["subject"]["reference"] == ref]

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(results),
        "entry": [{"resource": o} for o in results]
    }

# --- Startup ---

if __name__ == "__main__":
    logger.info("🚀 Starting Grahame (FHIR) API on port 8004...")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
