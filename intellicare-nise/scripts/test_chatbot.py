"""Script para testar chatbot Dr. Nise."""

import httpx
import asyncio
import json
from typing import List, Dict


NISE_BASE_URL = "http://localhost:8000"


async def test_chatbot_health():
    """Testa health check do chatbot."""
    print("\n🔍 Testando health check do chatbot...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NISE_BASE_URL}/api/v1/chatbot/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"✅ Flowise disponível: {data['flowise_available']}")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False


async def test_list_chatflows():
    """Testa listagem de chatflows."""
    print("\n📋 Listando chatflows...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NISE_BASE_URL}/api/v1/chatbot/chatflows")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de chatflows: {data['total']}")
            
            for chatflow in data.get('chatflows', []):
                print(f"  • {chatflow.get('name', chatflow.get('id'))}")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False


async def test_chat_question(question: str, chatflow_id: str = "dr-nise-default"):
    """Testa uma pergunta no chatbot."""
    print(f"\n💬 Pergunta: {question}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "question": question,
            "chatflow_id": chatflow_id
        }
        
        response = await client.post(
            f"{NISE_BASE_URL}/api/v1/chatbot/chat",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resposta: {data['text'][:200]}...")
            print(f"   Session ID: {data['session_id']}")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_chatbot_automated(paciente_id: str = "pac-123"):
    """Testa chatbot com perguntas pré-definidas."""
    print(f"\n🤖 Teste automatizado para paciente: {paciente_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{NISE_BASE_URL}/api/v1/chatbot/test?paciente_id={paciente_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de perguntas testadas: {data['total_perguntas']}")
            
            for i, resultado in enumerate(data['resultados'], 1):
                print(f"\n  {i}. {resultado['pergunta']}")
                print(f"     Resposta: {resultado['resposta'][:150]}...")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False


async def main():
    """Executa todos os testes."""
    print("=" * 70)
    print("🧪 TESTE DO CHATBOT DR. NISE")
    print("=" * 70)
    
    # Teste 1: Health check
    health_ok = await test_chatbot_health()
    
    if not health_ok:
        print("\n❌ Chatbot não está disponível. Verifique se Flowise está rodando.")
        return
    
    # Teste 2: Listar chatflows
    await test_list_chatflows()
    
    # Teste 3: Perguntas individuais
    perguntas = [
        "Qual o diagnóstico de diabetes do paciente pac-123?",
        "Quais alertas ativos para o paciente pac-123?",
        "Me dê um resumo do paciente pac-123"
    ]
    
    print("\n" + "=" * 70)
    print("📝 TESTANDO PERGUNTAS INDIVIDUAIS")
    print("=" * 70)
    
    for pergunta in perguntas:
        await test_chat_question(pergunta)
        await asyncio.sleep(1)  # Delay entre perguntas
    
    # Teste 4: Teste automatizado
    print("\n" + "=" * 70)
    print("🔄 TESTE AUTOMATIZADO")
    print("=" * 70)
    
    await test_chatbot_automated("pac-123")
    
    print("\n" + "=" * 70)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

