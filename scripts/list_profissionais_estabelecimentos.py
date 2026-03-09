#!/usr/bin/env python3
"""
Script para obter relação de profissionais de saúde associados a estabelecimentos
de Montes Claros (MG) e Brasília (DF).

OPÇÕES DISPONÍVEIS:
1. Via API Zilda (se rodando): GET http://localhost:8007/api/v1/establishments
2. Via Portal CNES: extração manual de profissionais por município (RECOMENDADO)
3. Via API Dados Abertos: apidadosabertos.saude.gov.br (pode estar instável)
"""

import csv
import json
import sys
from pathlib import Path

# Códigos IBGE
BRASILIA = {"city_code": "5300108", "state_code": "53", "nome": "Brasília"}
MONTES_CLAROS = {"city_code": "3143302", "state_code": "31", "nome": "Montes Claros"}

API_BASE = "https://apidadosabertos.saude.gov.br"
ZILDA_BASE = "http://localhost:8007"  # intellicare-zilda


def fetch_via_zilda(city_code: str, state_code: str | None = None, limit: int = 100) -> list[dict]:
    """Busca estabelecimentos via API do Zilda (se o serviço estiver rodando)."""
    import httpx

    url = f"{ZILDA_BASE}/api/v1/establishments"
    params: dict = {"city_code": city_code, "limit": limit}
    if state_code:
        params["state_code"] = state_code
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        return []


def fetch_establishments(city_code: str, state_code: str, limit: int = 100) -> list[dict]:
    """Busca estabelecimentos via API de Dados Abertos."""
    import httpx

    url = f"{API_BASE}/cnes/estabelecimentos"
    params = {
        "codigo_municipio": city_code,
        "codigo_uf": state_code,
        "status": 1,
        "limit": limit,
    }
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("data", data.get("estabelecimentos", []))
    except Exception as e:
        print(f"  API Dados Abertos: {e}", file=sys.stderr)
        return []


def main() -> None:
    """Executa extração de estabelecimentos e gera relatório."""
    output_dir = Path(__file__).parent.parent / "data" / "estabelecimentos"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Relação de Profissionais x Estabelecimentos")
    print("Montes Claros (MG) e Brasília (DF)")
    print("=" * 60)

    all_establishments = []
    for city in [BRASILIA, MONTES_CLAROS]:
        print(f"\nBuscando estabelecimentos em {city['nome']}...")
        # Tenta primeiro via Zilda (se docker estiver rodando)
        establishments = fetch_via_zilda(
            city_code=city["city_code"],
            state_code=city["state_code"],
            limit=200,
        )
        if not establishments:
            establishments = fetch_establishments(
                city_code=city["city_code"],
                state_code=city["state_code"],
                limit=200,
            )
            # Normaliza formato API Dados Abertos -> formato unificado
            for est in establishments:
                est.setdefault("codigo_cnes", est.get("codigo_cnes_estabelecimento", ""))
                est.setdefault("nome_fantasia", est.get("nome_fantasia"))
                est.setdefault("nome_razao_social", est.get("nome_razao_social", ""))
        else:
            # Zilda retorna cnes_code, legal_name, fantasy_name, etc.
            for est in establishments:
                est["codigo_cnes"] = est.get("cnes_code", est.get("codigo_cnes", ""))
                est["nome_fantasia"] = est.get("fantasy_name", est.get("nome_fantasia"))
                est["nome_razao_social"] = est.get("legal_name", est.get("nome_razao_social", ""))
        for est in establishments:
            est["_cidade_nome"] = city["nome"]
            est["_cidade_codigo"] = city["city_code"]
            all_establishments.append(est)
        print(f"  -> {len(establishments)} estabelecimentos encontrados")

    if not all_establishments:
        print("\nNenhum estabelecimento encontrado.")
        print("  Dica: inicie o Zilda com 'docker compose up -d' e rode novamente.")
        print("  Ou use o Portal CNES (veja instruções abaixo).")
    else:
        # Salva CSV de estabelecimentos
        csv_path = output_dir / "estabelecimentos_brasilia_montesclaros.csv"
        fieldnames = [
            "codigo_cnes",
            "nome_fantasia",
            "nome_razao_social",
            "cnpj",
            "descricao_tipo_unidade",
            "unit_type_description",
            "endereco_estabelecimento",
            "address",
            "bairro_estabelecimento",
            "neighborhood",
            "nome_municipio",
            "city_name",
            "_cidade_nome",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for est in all_establishments:
                row = {}
                for k in fieldnames:
                    row[k] = est.get(k, "")
                row["codigo_cnes"] = est.get("codigo_cnes", est.get("cnes_code", ""))
                writer.writerow(row)

        print(f"\nEstabelecimentos salvos em: {csv_path}")

        # Salva JSON completo
        json_path = output_dir / "estabelecimentos_brasilia_montesclaros.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_establishments, f, ensure_ascii=False, indent=2)
        print(f"Dados completos em: {json_path}")

    # Instruções para obter profissionais
    print("\n" + "=" * 60)
    print("COMO OBTER OS PROFISSIONAIS DE SAÚDE")
    print("=" * 60)
    print("""
O endpoint de profissionais na API de Dados Abertos pode não estar disponível.
Use o PORTAL CNES para extração:

1. Acesse: https://cnes.datasus.gov.br/pages/profissionais/extracao.jsp

2. Para BRASÍLIA (DF):
   - Selecione UF: Distrito Federal (53)
   - Selecione Município: Brasília (5300108)
   - Clique em "Pesquisar" e depois "Exportar CSV"

3. Para MONTES CLAROS (MG):
   - Selecione UF: Minas Gerais (31)
   - Selecione Município: Montes Claros (3143302)
   - Clique em "Pesquisar" e depois "Exportar CSV"

4. O CSV inclui: nome, CNS, CPF, CBO (ocupação), CNES do estabelecimento,
   município, vínculos, carga horária, etc.

5. Para cruzar com os estabelecimentos deste script, use a coluna
   "codigo_cnes" ou "CNES" do CSV de profissionais.
""")


if __name__ == "__main__":
    main()
