import asyncio
import os
import sys

# Garante que o diretorio atual do container esta no PYTHONPATH
sys.path.insert(0, "/app")

from modules.identity.schemas import PessoaFisicaIn
from modules.identity.services import find_or_create_by_cpf

async def run_idempotency():
    cpf = "99988877766"
    payload = PessoaFisicaIn(nome_completo="DR TESTE IDEMPOTENCIA", cpf=cpf)
    
    print(f"Executando Smoke Test Idempotencia para CPF {cpf}...")
    
    # 1. Primeira criacao
    p1 = await find_or_create_by_cpf(payload)
    print(f"Pessoa 1 Criada: ID={p1['id']}")
    
    # 2. Segunda criacao (deve retornar o mesmo ID)
    p2 = await find_or_create_by_cpf(payload)
    print(f"Pessoa 2 Retornada: ID={p2['id']}")
    
    if p1["id"] == p2["id"]:
        print(f"\n[OK] IDEMPOTENCIA CONFIRMADA: O mesmo uuid {p1['id']} foi retornado.")
    else:
        print(f"\n[FALHA] IDs diferentes: {p1['id']} != {p2['id']}")

if __name__ == "__main__":
    asyncio.run(run_idempotency())
