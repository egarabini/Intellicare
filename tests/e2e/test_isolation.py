"""AC-6: Isolamento de schema entre tenants."""
from __future__ import annotations

import os

import asyncpg
import pytest

pytestmark = pytest.mark.e2e

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://intellicare:intellicare@localhost:5432/intellicare",
)


@pytest.mark.asyncio
async def test_dados_isolados_entre_tenants():
    """Inserir em tenant_dev não aparece em tenant_e2e_test e vice-versa."""
    conn = await asyncpg.connect(DB_URL)
    try:
        # Inserir na knowledge_base do tenant_dev
        await conn.execute("SET search_path TO tenant_dev, public")
        await conn.execute("""
            INSERT INTO knowledge_base (title, content, source_path)
            VALUES ('Doc Isolamento', 'Conteúdo exclusivo tenant_dev', 'test/isolamento.txt')
        """)

        # Verificar que NÃO aparece em tenant_e2e_test
        await conn.execute("SET search_path TO tenant_e2e_test, public")
        row = await conn.fetchrow(
            "SELECT * FROM knowledge_base WHERE title = 'Doc Isolamento'"
        )
        assert row is None, "FALHA: dado do tenant_dev vazou para tenant_e2e_test!"

        # Cleanup
        await conn.execute("SET search_path TO tenant_dev, public")
        await conn.execute(
            "DELETE FROM knowledge_base WHERE title = 'Doc Isolamento'"
        )
    finally:
        await conn.close()

