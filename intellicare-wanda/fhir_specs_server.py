"""
Servidor de Especificações FHIR (FHIR Specs Server)
Fornece schemas, exemplos e documentação FHIR customizada via API REST.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
import json

app = FastAPI(title="FHIR Specs Server", description="Schemas e exemplos FHIR para agentes IntelliCare")

FHIR_SCHEMAS_DIR = Path(__file__).parent / "schemas"
FHIR_EXAMPLES_DIR = Path(__file__).parent / "examples"

@app.get("/schemas/{resource}")
def get_schema(resource: str):
    path = FHIR_SCHEMAS_DIR / f"{resource}.json"
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "Schema not found"})
    return json.load(open(path, "r", encoding="utf-8"))

@app.get("/examples/{resource}")
def get_example(resource: str):
    path = FHIR_EXAMPLES_DIR / f"{resource}.json"
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "Example not found"})
    return json.load(open(path, "r", encoding="utf-8"))

@app.get("/docs/{resource}")
def get_docs(resource: str):
    # Placeholder: pode servir markdown ou HTML futuramente
    return {"info": f"Documentação para {resource} (em desenvolvimento)"}
