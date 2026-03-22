"""
Provisiona os flows do CarePlanner no Kestra via API.
Idempotente: usa PUT /api/v1/flows (cria ou atualiza).

Uso:
    python infra/kestra/seed_flows.py
    # ou com variáveis de ambiente:
    KESTRA_URL=http://localhost:8080 python infra/kestra/seed_flows.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import re

import httpx

KESTRA_URL = os.getenv("KESTRA_URL", "http://localhost:8080").rstrip("/")
FLOWS_DIR = Path(__file__).parent / "flows"

FLOW_FILES = [
    "careplanner_jornada_basica.yml",
    "careplanner_jornada_video.yml",
    "careplanner_jornada_whatsapp.yml",
    "careplanner_jornada_email.yml",
    "careplanner_jornada_sms.yml",
    "careplanner_jornada_com_fallback.yml",
    "careplanner_resposta_confirmacao.yml",
    "careplanner_retry_com_backoff.yml",
    "careplanner_urgencia_clinica.yml",
]


def provision_flows() -> None:
    for filename in FLOW_FILES:
        flow_path = FLOWS_DIR / filename
        if not flow_path.exists():
            print(f"[ERRO] Flow não encontrado: {flow_path}")
            sys.exit(1)

        flow_yaml = flow_path.read_text(encoding="utf-8")
        namespace = re.search(r"^namespace:\s*(.+)$", flow_yaml, re.MULTILINE).group(1).strip()
        flow_id = re.search(r"^id:\s*(.+)$", flow_yaml, re.MULTILINE).group(1).strip()

        response = httpx.post(
            f"{KESTRA_URL}/api/v1/flows",
            content=flow_yaml,
            headers={"Content-Type": "application/x-yaml"},
            timeout=30,
        )

        if response.status_code in (200, 201):
            print(f"[OK] {filename} provisionado (HTTP {response.status_code})")
        else:
            print(f"[ERRO] {filename} — HTTP {response.status_code}: {response.text[:200]}")
            sys.exit(1)


if __name__ == "__main__":
    print(f"Kestra URL: {KESTRA_URL}")
    provision_flows()
    print("Todos os flows provisionados com sucesso.")
