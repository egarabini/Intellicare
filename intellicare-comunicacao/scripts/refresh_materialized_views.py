#!/usr/bin/env python3
"""
Script Python para refresh de materialized views do módulo de comunicação.
Pode ser executado via cron ou como task agendada.

Uso:
    python refresh_materialized_views.py

Variáveis de ambiente:
    DATABASE_URL: URL de conexão do PostgreSQL
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def refresh_materialized_views() -> None:
    """Refresh all materialized views."""
    
    # Obter DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL não configurada!")
        sys.exit(1)
    
    # Criar engine
    engine = create_async_engine(database_url, echo=False)
    
    try:
        logger.info("Conectando ao banco de dados...")
        
        async with engine.begin() as conn:
            logger.info("Executando refresh de materialized views...")
            
            # Executar função de refresh
            await conn.execute(
                text("SELECT comunicacao_analitico.refresh_materialized_views();")
            )
            
            logger.info("Refresh concluído com sucesso!")
    
    except Exception as exc:
        logger.error("Erro ao executar refresh: %s", exc, exc_info=True)
        sys.exit(1)
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(refresh_materialized_views())

