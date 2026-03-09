#!/usr/bin/env python3
"""
Gera carga de dados para staging do IntelliCare.

Demonstra todo o potencial: Patient, Organization, Practitioner, Condition,
Observation (incl. críticas para AlertHub), Encounter, MedicationRequest,
AllergyIntolerance, CarePlan, Goal, Procedure, DiagnosticReport, RelatedPerson.

Baseado em:
- docs/V2.0.0-KEYCLOAK (abordagem Keycloak realm bemcuidar)
- data/REG-brasilia.csv e data/REG-montesClaros.csv (pessoas reais)
- data/V2.0.0-KEYCLOAK/conditions_anon, practitioners
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
DATA_ROOT = REPO_ROOT / "data"
CPF_SYSTEM = "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf"


def parse_date_br(value: str) -> str | None:
    """Converte DD/MM/YYYY para YYYY-MM-DD (FHIR)."""
    if not value or not value.strip():
        return None
    try:
        parts = value.strip().split("/")
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            if 1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2030:
                return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, IndexError):
        pass
    return None


def parse_csv_reg(path: Path) -> list[dict]:
    """Lê CSV REG (semicolon, quoted)."""
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            rows.append(row)
    return rows


def reg_to_fhir_patient(row: dict, patient_id: str, city: str) -> dict:
    """Converte linha REG para FHIR Patient R4."""
    nome = row.get("NOME_COMPLETO", "").strip()
    if not nome:
        return None
    parts = nome.split()
    family = parts[-1] if parts else ""
    given = parts[:-1] if len(parts) > 1 else parts

    cpf = "".join(c for c in row.get("CPF", "") if c.isdigit())
    birth = parse_date_br(row.get("DATA_NASCIMENTO", ""))
    sexo = row.get("SEXO", "").upper()
    gender = "male" if sexo == "M" else "female" if sexo == "F" else "unknown"

    identifiers = []
    if cpf:
        identifiers.append({
            "use": "official",
            "system": CPF_SYSTEM,
            "value": cpf,
        })

    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {"profile": ["http://rnds.saude.gov.br/fhir/r4/StructureDefinition/Patient"]},
        "name": [{"use": "official", "given": given, "family": family}],
        "gender": gender,
        "birthDate": birth or "",
    }
    if identifiers:
        patient["identifier"] = identifiers

    # Address
    cep = row.get("CEP", "").strip()
    num = row.get("NUMERO", "").strip()
    comp = row.get("COMPLEMENTO", "").strip()
    if cep or num or comp:
        addr = {"postalCode": cep}
        if num or comp:
            addr["line"] = [f"{num} {comp}".strip() or "S/N"]
        if city:
            addr["city"] = city
        patient["address"] = [addr]

    # Telecom
    tel = row.get("TELEFONE", "").strip()
    email = row.get("EMAIL", "").strip()
    telecom = []
    if tel:
        telecom.append({"system": "phone", "value": tel, "use": "home"})
    if email and email and "nao" not in email.lower() and "@" in email:
        telecom.append({"system": "email", "value": email, "use": "home"})
    if telecom:
        patient["telecom"] = telecom

    return patient


def load_conditions_anon(approach_dir: Path) -> list[dict]:
    """Carrega condições anonimizadas (sem referência a paciente)."""
    conditions = []
    cond_dir = approach_dir / "conditions_anon"
    if not cond_dir.exists():
        return conditions
    for f in cond_dir.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    conditions.extend(data)
                else:
                    conditions.append(data)
        except Exception:
            pass
    return conditions


def make_condition_fhir(cond: dict, patient_id: str, recorded_date: str) -> dict:
    """Cria FHIR Condition a partir de condição anonimizada."""
    cid = cond.get("cid", "N18.9")
    display = cond.get("display", "DRC não especificada")
    cond_id = f"cond-{hashlib.sha256(f'{patient_id}_{cid}_{recorded_date}'.encode()).hexdigest()[:16]}"
    return {
        "resourceType": "Condition",
        "id": cond_id,
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
        "code": {"coding": [{"system": "http://www.saude.gov.br/fhir/r4/CodeSystem/cid-10", "code": cid, "display": display}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "recordedDate": recorded_date,
        "onsetDateTime": recorded_date,
    }


def make_observation_creatinine(patient_id: str, value: float, date_str: str, obs_id: str) -> dict:
    """Cria FHIR Observation para creatinina (LOINC 2160-0)."""
    return {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0", "display": "Creatinina"}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": date_str,
        "valueQuantity": {"value": round(value, 2), "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
        "referenceRange": [{"low": {"value": 0.7}, "high": {"value": 1.2}}],
    }


def make_observation_egfr(patient_id: str, value: float, date_str: str, obs_id: str) -> dict:
    """Cria FHIR Observation para eGFR (LOINC 33914-3)."""
    return {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "33914-3", "display": "eGFR"}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": date_str,
        "valueQuantity": {"value": round(value, 1), "unit": "mL/min/1.73m2", "system": "http://unitsofmeasure.org", "code": "mL/min/{1.73_m2}"},
    }


def creatinine_from_egfr(egfr: float) -> float:
    """Fórmula aproximada inversa: eGFR -> creatinina (Cockcroft)."""
    if egfr <= 0:
        return 2.5
    return max(0.5, min(8.0, 120 / egfr))


def make_encounter(patient_id: str, org_id: str, enc_type: str, date_str: str, enc_id: str, practitioner_id: str = None) -> dict:
    """Cria FHIR Encounter (atendimento)."""
    type_map = {
        "ambulatorio": ("AMB", "ambulatory"),
        "emergencia": ("EMER", "emergency"),
        "internacao": ("IMP", "inpatient"),
    }
    code, _ = type_map.get(enc_type, ("AMB", "ambulatory"))
    enc = {
        "resourceType": "Encounter",
        "id": enc_id,
        "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": code, "display": enc_type},
        "type": [{"coding": [{"system": "http://snomed.info/sct", "code": "185349003", "display": "Consulta"}]}],
        "subject": {"reference": f"Patient/{patient_id}"},
        "serviceProvider": {"reference": f"Organization/{org_id}"},
        "period": {"start": date_str, "end": date_str},
    }
    if practitioner_id:
        enc["participant"] = [{"individual": {"reference": f"Practitioner/{practitioner_id}"}, "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType", "code": "PPRF", "display": "Profissional"}]}]}]
    return enc


def make_medication_request(patient_id: str, med_name: str, date_str: str, med_id: str) -> dict:
    """Cria FHIR MedicationRequest."""
    return {
        "resourceType": "MedicationRequest",
        "id": med_id,
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"coding": [{"system": "http://www.saude.gov.br/fhir/r4/CodeSystem/brmed", "display": med_name}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": date_str,
        "dosageInstruction": [{"timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}, "route": {"text": "Oral"}}],
    }


def make_practitioner(prac: dict) -> dict:
    """Cria FHIR Practitioner."""
    name_parts = prac["name"].split()
    family = name_parts[-1] if name_parts else ""
    given = name_parts[:-1] if len(name_parts) > 1 else name_parts
    qual = []
    if prac.get("crm"):
        qual.append({"identifier": {"system": "http://www.saude.gov.br/fhir/r4/NamingSystem/crm", "value": prac["crm"]}, "code": {"coding": [{"system": "http://snomed.info/sct", "code": "223366009", "display": "Médico"}]}})
    if prac.get("conselho"):
        qual.append({"identifier": {"system": "http://www.saude.gov.br/fhir/r4/NamingSystem/coren", "value": prac["conselho"]}, "code": {"coding": [{"system": "http://snomed.info/sct", "code": "224535009", "display": "Enfermeiro"}]}})
    return {
        "resourceType": "Practitioner",
        "id": prac["id"],
        "name": [{"use": "official", "given": given, "family": family}],
        "qualification": qual or [{"code": {"coding": [{"system": "http://snomed.info/sct", "code": "223366009", "display": "Profissional de saúde"}]}}],
    }


def make_practitioner_role(prac_id: str, org_id: str, role_code: str = "doctor", location_id: str = None) -> dict:
    """Cria FHIR PractitionerRole (profissional associado à organização e unidade)."""
    pr = {
        "resourceType": "PractitionerRole",
        "id": f"pr-{prac_id}-{org_id}",
        "practitioner": {"reference": f"Practitioner/{prac_id}"},
        "organization": {"reference": f"Organization/{org_id}"},
        "code": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-role", "code": role_code}]}],
    }
    if location_id:
        pr["location"] = [{"reference": f"Location/{location_id}"}]
    return pr


def make_location(loc: dict) -> dict:
    """Cria FHIR Location (unidade física)."""
    return {
        "resourceType": "Location",
        "id": loc["id"],
        "name": loc["name"],
        "status": "active",
        "mode": "instance",
        "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": "si", "display": "Site"}]},
        "managingOrganization": {"reference": f"Organization/{loc['org_id']}"},
    }


def make_allergy_intolerance(patient_id: str, allergy: dict, date_str: str, all_id: str) -> dict:
    """Cria FHIR AllergyIntolerance."""
    crit = allergy.get("criticality", "unable-to-assess")
    if crit == "moderate":
        crit = "high"
    return {
        "resourceType": "AllergyIntolerance",
        "id": all_id,
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
        "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": "confirmed"}]},
        "type": "allergy",
        "category": [allergy.get("category", "medication")],
        "criticality": crit,
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": allergy.get("code", "91935009"), "display": allergy.get("display", "Alergia")}]},
        "patient": {"reference": f"Patient/{patient_id}"},
        "recordedDate": date_str,
        "reaction": [{"manifestation": [{"coding": [{"system": "http://snomed.info/sct", "code": "247472004", "display": "Hipersensibilidade"}]}]}],
    }


def make_goal(patient_id: str, description: str, target_value: str, goal_id: str, date_str: str) -> dict:
    """Cria FHIR Goal."""
    return {
        "resourceType": "Goal",
        "id": goal_id,
        "lifecycleStatus": "active",
        "description": {"text": description},
        "subject": {"reference": f"Patient/{patient_id}"},
        "target": [{"measure": {"coding": [{"display": description}]}, "detailString": target_value, "dueDate": date_str[:10]}],
        "startDate": date_str[:10],
    }


def make_care_plan(patient_id: str, conditions: list[str], goals: list[dict], plan_id: str, date_str: str) -> dict:
    """Cria FHIR CarePlan."""
    return {
        "resourceType": "CarePlan",
        "id": plan_id,
        "status": "active",
        "intent": "plan",
        "title": f"Plano de Cuidado - {', '.join(conditions[:2])}",
        "description": f"Condições: {', '.join(conditions)}",
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {"start": date_str[:10]},
        "category": [{"coding": [{"system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category", "code": "assess-plan"}]}],
        "goal": [{"reference": f"Goal/{g['id']}"} for g in goals],
        "activity": [{"detail": {"kind": "MedicationRequest", "description": "Seguir prescrição médica", "status": "in-progress"}}],
    }


def make_procedure(patient_id: str, proc_code: str, display: str, date_str: str, proc_id: str, practitioner_id: str = None, org_id: str = None) -> dict:
    """Cria FHIR Procedure."""
    proc = {
        "resourceType": "Procedure",
        "id": proc_id,
        "status": "completed",
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": proc_code, "display": display}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "performedDateTime": date_str,
    }
    if practitioner_id:
        proc["performer"] = [{"actor": {"reference": f"Practitioner/{practitioner_id}"}}]
    if org_id:
        proc.setdefault("performer", []).append({"actor": {"reference": f"Organization/{org_id}"}})
    return proc


def make_diagnostic_report(patient_id: str, obs_refs: list[str], date_str: str, report_id: str, practitioner_id: str = None) -> dict:
    """Cria FHIR DiagnosticReport."""
    rep = {
        "resourceType": "DiagnosticReport",
        "id": report_id,
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2", "display": "Painel metabólico básico"}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": date_str,
        "result": [{"reference": ref} for ref in obs_refs],
    }
    if practitioner_id:
        rep["resultsInterpreter"] = [{"reference": f"Practitioner/{practitioner_id}"}]
    return rep


def make_observation_bp(patient_id: str, systolic: float, diastolic: float, date_str: str, obs_id: str) -> dict:
    """Cria FHIR Observation para pressão arterial (LOINC 85354-9)."""
    return {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Pressão arterial"}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": date_str,
        "component": [
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "PAS"}]}, "valueQuantity": {"value": systolic, "unit": "mmHg", "code": "mm[Hg]"}},
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "PAD"}]}, "valueQuantity": {"value": diastolic, "unit": "mmHg", "code": "mm[Hg]"}},
        ],
    }


def make_related_person(patient_id: str, name: str, relationship: str, phone: str, rel_id: str) -> dict:
    """Cria FHIR RelatedPerson (contato de emergência)."""
    parts = name.split()
    return {
        "resourceType": "RelatedPerson",
        "id": rel_id,
        "patient": {"reference": f"Patient/{patient_id}"},
        "relationship": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": relationship, "display": relationship}]}],
        "name": [{"family": parts[-1] if parts else "", "given": parts[:-1] if len(parts) > 1 else parts}],
        "telecom": [{"system": "phone", "value": phone, "use": "mobile"}] if phone else [],
    }


def random_date_in_past(days_back: int = 365) -> str:
    """Data aleatória no passado (ISO)."""
    d = datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back))
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera carga de dados para staging IntelliCare")
    parser.add_argument("--approach", default="V2.0.0-KEYCLOAK", help="Abordagem (pasta em data/)")
    parser.add_argument("--limit", type=int, default=0, help="Limite de pacientes por cidade (0=all)")
    parser.add_argument("--only", choices=[
        "patients", "conditions", "observations", "encounters", "medications", "organizations",
        "practitioners", "allergies", "careplans", "procedures", "diagnosticreports", "relatedpersons",
    ], help="Gerar apenas um tipo")
    args = parser.parse_args()

    approach_dir = DATA_ROOT / args.approach
    if not approach_dir.exists():
        print(f"Abordagem não encontrada: {approach_dir}")
        sys.exit(1)

    fhir_dir = approach_dir / "fhir"
    for d in ["patients", "conditions", "observations", "encounters", "medications", "organizations",
              "locations", "practitioners", "practitionerroles", "allergies", "goals", "careplans",
              "procedures", "diagnosticreports", "relatedpersons"]:
        (fhir_dir / d).mkdir(parents=True, exist_ok=True)

    print(f"=== Carga de dados: {args.approach} ===\n")

    # 1. Organizations
    if not args.only or args.only == "organizations":
        org_path = approach_dir / "establishments" / "organizacoes.json"
        if org_path.exists():
            with open(org_path, encoding="utf-8") as f:
                orgs = json.load(f)
            for org in orgs:
                out = fhir_dir / "organizations" / f"{org['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(org, fp, ensure_ascii=False, indent=2)
            print(f"Organizations: {len(orgs)}")

    # 1b. Locations (unidades físicas dos estabelecimentos)
    if not args.only or args.only == "organizations":
        loc_path = approach_dir / "establishments" / "locations.json"
        if loc_path.exists():
            with open(loc_path, encoding="utf-8") as f:
                locs = json.load(f)
            for loc in locs:
                lr = make_location(loc)
                out = fhir_dir / "locations" / f"{lr['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(lr, fp, ensure_ascii=False, indent=2)
            print(f"Locations: {len(locs)}")

    # 2. Patients
    patients = []
    reg_files = [
        (DATA_ROOT / "REG-brasilia.csv", "Brasília"),
        (DATA_ROOT / "REG-montesClaros.csv", "Montes Claros"),
    ]
    for reg_path, city in reg_files:
        if not reg_path.exists():
            print(f"Arquivo não encontrado: {reg_path}")
            continue
        rows = parse_csv_reg(reg_path)
        if args.limit:
            rows = rows[: args.limit]
        for i, row in enumerate(rows):
            pid = f"pat-{city.lower().replace(' ', '-')}-{i+1:05d}"
            p = reg_to_fhir_patient(row, pid, city)
            if p:
                patients.append((pid, p, city))
                out = fhir_dir / "patients" / f"{pid}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(p, fp, ensure_ascii=False, indent=2)
        print(f"Patients {city}: {len(rows)}")

    if not patients and (not args.only or args.only == "patients"):
        print("Nenhum paciente gerado.")
        sys.exit(0)

    # 3. Conditions (anonimizadas -> associação aleatória)
    if not args.only or args.only == "conditions":
        cond_anon = load_conditions_anon(approach_dir)
        org_ids = ["org-hran", "org-hbdf", "org-santacasa-mc", "org-ubs-asa-sul", "org-ubs-mc-centro"]
        # ~15% dos pacientes com DRC
        sample = random.sample(patients, min(len(patients) // 10, len(patients)))
        for pid, _, _ in sample:
            if not cond_anon:
                break
            cond = random.choice(cond_anon)
            if "cid" in cond:
                date_str = random_date_in_past(365)
                c = make_condition_fhir(cond, pid, date_str)
                out = fhir_dir / "conditions" / f"{c['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(c, fp, ensure_ascii=False, indent=2)
        print(f"Conditions: ~{len(sample)}")

    # 4. Observations (creatinina, eGFR, PA — incluindo valores críticos para AlertHub)
    if not args.only or args.only == "observations":
        total_obs = 0
        for i, (pid, _, _) in enumerate(patients[: min(len(patients), 600)]):
            date_str = random_date_in_past(180)
            # ~15% com eGFR baixo (alerta DRC), ~10% com PA alta
            if random.random() < 0.15:
                eGFR = random.uniform(12, 35)  # Crítico para alertas
            else:
                eGFR = random.uniform(45, 110)
            creat = creatinine_from_egfr(eGFR)
            o1 = make_observation_creatinine(pid, creat, date_str, f"obs-{pid}-creat-{i}")
            o2 = make_observation_egfr(pid, eGFR, date_str, f"obs-{pid}-egfr-{i}")
            for obs in [o1, o2]:
                out = fhir_dir / "observations" / f"{obs['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(obs, fp, ensure_ascii=False, indent=2)
                total_obs += 1
            # Pressão arterial (~30% dos pacientes)
            if random.random() < 0.3:
                pas = random.uniform(140, 180) if random.random() < 0.2 else random.uniform(110, 135)
                pad = random.uniform(90, 110) if pas > 140 else random.uniform(70, 85)
                o3 = make_observation_bp(pid, round(pas, 0), round(pad, 0), date_str, f"obs-{pid}-pa-{i}")
                out = fhir_dir / "observations" / f"{o3['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(o3, fp, ensure_ascii=False, indent=2)
                total_obs += 1
        print(f"Observations: {total_obs}")

    # 4b. Practitioners e PractitionerRoles (com location = unidade)
    practitioners = []
    if not args.only or args.only == "practitioners":
        prac_path = approach_dir / "practitioners" / "profissionais.json"
        if prac_path.exists():
            with open(prac_path, encoding="utf-8") as f:
                prac_list = json.load(f)
            for prac in prac_list:
                p = make_practitioner(prac)
                practitioners.append(prac)
                out = fhir_dir / "practitioners" / f"{p['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(p, fp, ensure_ascii=False, indent=2)
                loc_id = prac.get("location")
                pr = make_practitioner_role(
                    prac["id"], prac["org"],
                    "doctor" if prac.get("crm") else "nurse",
                    location_id=loc_id,
                )
                out = fhir_dir / "practitionerroles" / f"{pr['id']}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(pr, fp, ensure_ascii=False, indent=2)
            print(f"Practitioners: {len(practitioners)}, PractitionerRoles: {len(practitioners)} (com unidades)")

    # 5. Encounters (com practitioner quando disponível)
    if not args.only or args.only == "encounters":
        org_ids = ["org-hran", "org-hbdf", "org-santacasa-mc", "org-ubs-asa-sul", "org-ubs-mc-centro"]
        enc_types = ["ambulatorio"] * 7 + ["emergencia"] * 2 + ["internacao"]
        if not practitioners:
            prac_path = approach_dir / "practitioners" / "profissionais.json"
            if prac_path.exists():
                with open(prac_path, encoding="utf-8") as f:
                    practitioners = json.load(f)
        prac_ids = [p["id"] for p in practitioners] if practitioners else [None]
        count_enc = 0
        for pid, _, _ in patients[: min(len(patients), 300)]:
            for _ in range(random.randint(1, 3)):
                enc_id = f"enc-{pid}-{count_enc}"
                prac = random.choice(prac_ids) if prac_ids else None
                enc = make_encounter(pid, random.choice(org_ids), random.choice(enc_types), random_date_in_past(90), enc_id, prac)
                out = fhir_dir / "encounters" / f"{enc_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(enc, fp, ensure_ascii=False, indent=2)
                count_enc += 1
        print(f"Encounters: {count_enc}")

    # 6. Medications
    if not args.only or args.only == "medications":
        meds = ["Losartana 50mg", "Metformina 850mg", "Hidroclorotiazida 25mg", "Omeprazol 20mg", "AAS 100mg", "Insulina NPH"]
        count_med = 0
        for pid, _, _ in patients[: min(len(patients), 400)]:
            if random.random() < 0.4:
                med_id = f"med-{pid}-{count_med}"
                m = make_medication_request(pid, random.choice(meds), random_date_in_past(60), med_id)
                out = fhir_dir / "medications" / f"{med_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(m, fp, ensure_ascii=False, indent=2)
                count_med += 1
        print(f"Medications: {count_med}")

    # 7. AllergyIntolerance (~10% dos pacientes)
    if not args.only or args.only == "allergies":
        all_path = approach_dir / "conditions_anon" / "alergias_comuns.json"
        allergies_data = []
        if all_path.exists():
            with open(all_path, encoding="utf-8") as f:
                allergies_data = json.load(f)
        if allergies_data:
            sample = random.sample(patients, min(len(patients) // 10, len(patients)))
            for i, (pid, _, _) in enumerate(sample):
                all_id = f"all-{pid}-{i}"
                a = make_allergy_intolerance(pid, random.choice(allergies_data), random_date_in_past(365), all_id)
                out = fhir_dir / "allergies" / f"{all_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(a, fp, ensure_ascii=False, indent=2)
            print(f"AllergyIntolerance: {len(sample)}")

    # 8. CarePlan + Goal (pacientes com DRC/DM2/HAS)
    if not args.only or args.only == "careplans":
        cond_anon = load_conditions_anon(approach_dir)
        chronic = [c for c in cond_anon if c.get("cid") in ("N18.3", "N18.4", "N18.5", "E11", "I10")]
        if chronic:
            sample = random.sample(patients, min(len(patients) // 5, len(patients)))
            for i, (pid, _, _) in enumerate(sample):
                conds = [random.choice(chronic)["display"] for _ in range(random.randint(1, 2))]
                date_str = random_date_in_past(180)
                goal_id = f"goal-{pid}-{i}"
                g = make_goal(pid, "Manter eGFR estável", "eGFR > 45 mL/min", goal_id, date_str)
                out = fhir_dir / "goals" / f"{goal_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(g, fp, ensure_ascii=False, indent=2)
                plan_id = f"cp-{pid}-{i}"
                cp = make_care_plan(pid, conds, [g], plan_id, date_str)
                out = fhir_dir / "careplans" / f"{plan_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(cp, fp, ensure_ascii=False, indent=2)
            print(f"CarePlans: {len(sample)}, Goals: {len(sample)}")

    # 9. Procedure (diálise para DRC 5, etc.)
    if not args.only or args.only == "procedures":
        prac_ids = [p["id"] for p in practitioners] if practitioners else []
        if not prac_ids:
            prac_path = approach_dir / "practitioners" / "profissionais.json"
            if prac_path.exists():
                with open(prac_path, encoding="utf-8") as f:
                    prac_ids = [p["id"] for p in json.load(f)]
        procs = [
            ("183452005", "Hemodiálise", "org-hran"),
            ("302497006", "Consulta nefrológica", "org-santacasa-mc"),
            ("185349003", "Consulta médica", "org-ubs-asa-sul"),
        ]
        sample = random.sample(patients, min(len(patients) // 8, len(patients)))
        for i, (pid, _, _) in enumerate(sample):
            proc_code, display, org = random.choice(procs)
            proc_id = f"proc-{pid}-{i}"
            prac = random.choice(prac_ids) if prac_ids else None
            p = make_procedure(pid, proc_code, display, random_date_in_past(90), proc_id, prac, org)
            out = fhir_dir / "procedures" / f"{proc_id}.json"
            with open(out, "w", encoding="utf-8") as fp:
                json.dump(p, fp, ensure_ascii=False, indent=2)
        print(f"Procedures: {len(sample)}")

    # 10. DiagnosticReport (agrega Observations)
    if not args.only or args.only == "diagnosticreports":
        prac_ids = [p["id"] for p in practitioners] if practitioners else []
        if not prac_ids and (approach_dir / "practitioners" / "profissionais.json").exists():
            with open(approach_dir / "practitioners" / "profissionais.json", encoding="utf-8") as f:
                prac_ids = [p["id"] for p in json.load(f)]
        obs_dir = fhir_dir / "observations"
        obs_files = list(obs_dir.glob("*.json")) if obs_dir.exists() else []
        # Agrupa obs por paciente (obs-{pid}-creat/egfr/pa-*)
        by_patient: dict[str, list[str]] = {}
        for of in obs_files[: min(400, len(obs_files))]:
            stem = of.stem
            for suffix in ["-creat-", "-egfr-", "-pa-"]:
                if stem.startswith("obs-") and suffix in stem:
                    pid = stem[4 : stem.find(suffix)]
                    by_patient.setdefault(pid, []).append(f"Observation/{stem}")
                    break
        count_rep = 0
        for pid, refs in list(by_patient.items())[: min(150, len(by_patient))]:
            if len(refs) >= 1:
                report_id = f"dr-{pid}-{count_rep}"
                prac = random.choice(prac_ids) if prac_ids else None
                dr = make_diagnostic_report(pid, refs[:5], random_date_in_past(90), report_id, prac)
                out = fhir_dir / "diagnosticreports" / f"{report_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(dr, fp, ensure_ascii=False, indent=2)
                count_rep += 1
        print(f"DiagnosticReports: {count_rep}")

    # 11. RelatedPerson (contatos de emergência)
    if not args.only or args.only == "relatedpersons":
        parent_names = ["Maria Silva", "José Santos", "Ana Oliveira", "Carlos Souza", "Fernanda Lima", "Pedro Costa"]
        count_rel = 0
        for i, (pid, p_data, _) in enumerate(patients[: min(len(patients), 200)]):
            if random.random() < 0.5:
                rel_id = f"rel-{pid}-{i}"
                name = random.choice(parent_names)
                rel = random.choice(["MTH", "FTH", "FAMMEMB"])
                tel = p_data.get("telecom", [{}])[0].get("value", "11999999999") if p_data.get("telecom") else "11999999999"
                rp = make_related_person(pid, name, "Mãe" if rel == "MTH" else "Pai" if rel == "FTH" else "Familiar", tel, rel_id)
                out = fhir_dir / "relatedpersons" / f"{rel_id}.json"
                with open(out, "w", encoding="utf-8") as fp:
                    json.dump(rp, fp, ensure_ascii=False, indent=2)
                count_rel += 1
        print(f"RelatedPersons: {count_rel}")

    print(f"\nDados salvos em: {fhir_dir}")


if __name__ == "__main__":
    main()
