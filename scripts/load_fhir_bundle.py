#!/usr/bin/env python3
"""
Carrega recursos FHIR gerados por seed_staging_data.py no servidor GRAHAME.

Uso:
  python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir
  python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --base-url http://localhost:8012
  python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --workers 20  # carga paralela
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Instale httpx: pip install httpx")
    sys.exit(1)

# Ordem de carga (dependências) e mapeamento pasta -> resourceType
RESOURCE_DIRS = [
    ("organizations", "Organization"),
    ("locations", "Location"),
    ("patients", "Patient"),
    ("practitioners", "Practitioner"),
    ("practitionerroles", "PractitionerRole"),
    ("conditions", "Condition"),
    ("observations", "Observation"),
    ("encounters", "Encounter"),
    ("medications", "MedicationRequest"),
    ("allergies", "AllergyIntolerance"),
    ("goals", "Goal"),
    ("careplans", "CarePlan"),
    ("procedures", "Procedure"),
    ("diagnosticreports", "DiagnosticReport"),
    ("relatedpersons", "RelatedPerson"),
]


def _post_one(
    base_url: str,
    headers: dict,
    resource_type: str,
    resource: dict,
    rid: str,
) -> tuple[bool, str | None]:
    """Envia um recurso; retorna (sucesso, mensagem_erro)."""
    try:
        payload = {"resource": resource}
        url = f"{base_url}/api/v1/{resource_type}"
        with httpx.Client(timeout=60) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            return True, None
        return False, f"{resource_type}/{rid}: {resp.status_code} {resp.text[:200]}"
    except Exception as e:
        return False, f"{rid}: {e}"


def load_resources(
    fhir_dir: Path,
    base_url: str,
    token: str | None = None,
    workers: int = 10,
    verbose: bool = True,
    tenant_id: str = "default",
) -> dict[str, int]:
    """Carrega todos os recursos FHIR do diretório (paralelo quando workers > 1)."""
    base_url = base_url.rstrip("/")
    headers = {"Content-Type": "application/json", "X-Tenant-ID": tenant_id}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    stats: dict[str, int] = {}
    errors: list[str] = []

    for dir_name, resource_type in RESOURCE_DIRS:
        type_dir = fhir_dir / dir_name
        if not type_dir.exists():
            continue

        files = sorted(type_dir.glob("*.json"))
        if not files:
            continue

        if verbose:
            print(f"  {resource_type}: {len(files)} recursos...", end=" ", flush=True)

        count = 0
        if workers <= 1:
            for json_file in files:
                with open(json_file, encoding="utf-8") as f:
                    resource = json.load(f)
                rt = resource.get("resourceType", resource_type)
                rid = resource.get("id", json_file.stem)
                ok, err = _post_one(base_url, headers, rt, resource, rid)
                if ok:
                    count += 1
                else:
                    errors.append(err or "")
        else:
            def load_and_post(fp: Path) -> tuple[bool, str | None]:
                with open(fp, encoding="utf-8") as f:
                    resource = json.load(f)
                rt = resource.get("resourceType", resource_type)
                rid = resource.get("id", fp.stem)
                return _post_one(base_url, headers, rt, resource, rid)

            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(load_and_post, f): f for f in files}
                for fut in as_completed(futures):
                    ok, err = fut.result()
                    if ok:
                        count += 1
                    elif err:
                        errors.append(err)

        stats[resource_type] = count
        if verbose:
            print(f"OK {count}", flush=True)
        if count == 0 and errors:
            type_errors = [e for e in errors if e and e.startswith(resource_type)]
            if type_errors:
                print(f"    Ex.: {type_errors[0][:120]}", flush=True)

    if errors:
        print("\nErros:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... e mais {len(errors) - 20} erros")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega recursos FHIR no GRAHAME")
    parser.add_argument("fhir_dir", type=Path, help="Diretório com subpastas patients/, conditions/, etc.")
    parser.add_argument("--base-url", default="http://localhost:8012", help="URL base do GRAHAME")
    parser.add_argument("--token", help="JWT Bearer token (opcional)")
    parser.add_argument("--workers", type=int, default=10, help="Workers paralelos (default: 10)")
    parser.add_argument("--tenant-id", default="default", help="X-Tenant-ID header (default: default)")
    args = parser.parse_args()

    if not args.fhir_dir.exists():
        print(f"Diretório não encontrado: {args.fhir_dir}")
        sys.exit(1)

    print(f"Carregando de {args.fhir_dir} para {args.base_url} (workers={args.workers})...")
    stats = load_resources(
        args.fhir_dir,
        args.base_url,
        args.token,
        workers=args.workers,
        tenant_id=args.tenant_id,
    )
    print("\nRecursos carregados:")
    for rt, n in stats.items():
        print(f"  {rt}: {n}")


if __name__ == "__main__":
    main()
