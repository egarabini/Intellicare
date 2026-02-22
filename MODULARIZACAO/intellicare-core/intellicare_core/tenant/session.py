"""Factory de sessions SQLAlchemy com isolamento por schema de tenant.

O TenantAwareSessionFactory garante que toda query executada dentro
de uma session esteja automaticamente direcionada ao schema correto
do tenant, usando SET search_path do PostgreSQL.

Uso:
    factory = TenantAwareSessionFactory(database_url)
    session = await factory.get_session(ctx)
    # Todas as queries agora executam no schema tenant_{id}

Seguranca:
    - O schema name e sanitizado para prevenir SQL injection
    - Apenas schemas com prefixo 'tenant_' ou 'public' sao aceitos
"""

from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from intellicare_core.tenant.context import TenantContext


# Regex para validar nomes de schema (prevenir injection)
_SCHEMA_NAME_PATTERN = re.compile(r"^(tenant_[a-z0-9_]+|public|platform)$")


class TenantAwareSessionFactory:
    """Factory que cria sessions com search_path isolado por tenant.

    Cada session retornada tem o search_path configurado para
    o schema do tenant, garantindo isolamento de dados.

    Attributes:
        _engine: Engine SQLAlchemy compartilhado (connection pool)
        _sessionmaker: Factory de sessions pre-configurada
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ) -> None:
        """Inicializa a factory com conexao ao banco.

        Args:
            database_url: URL de conexao PostgreSQL (asyncpg)
            pool_size: Tamanho do pool de conexoes
            max_overflow: Conexoes extras alem do pool
            pool_pre_ping: Verificar conexao antes de usar
            echo: Log de SQL queries (debug)
        """
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        )
        self._sessionmaker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self, ctx: TenantContext) -> AsyncSession:
        """Cria uma session com search_path configurado para o tenant.

        Args:
            ctx: Contexto do tenant atual

        Returns:
            AsyncSession com search_path = tenant_schema, public

        Raises:
            ValueError: Se o schema name for invalido (prevencao de injection)
        """
        self._validate_schema(ctx.tenant_schema)

        session = self._sessionmaker()

        # SET search_path garante que todas as queries usem o schema do tenant
        # O 'public' e incluido como fallback para tabelas compartilhadas
        # (ex: extensions, tipos customizados)
        await session.execute(
            text(f"SET search_path TO {ctx.tenant_schema}, public")
        )

        return session

    async def get_platform_session(self) -> AsyncSession:
        """Cria uma session para o schema da plataforma (admin).

        Usado por intellicare-admin para queries no schema 'platform'.
        """
        session = self._sessionmaker()
        await session.execute(text("SET search_path TO platform, public"))
        return session

    @staticmethod
    def _validate_schema(schema_name: str) -> None:
        """Valida o nome do schema para prevenir SQL injection.

        Args:
            schema_name: Nome do schema a validar

        Raises:
            ValueError: Se o schema nao corresponde ao padrao esperado
        """
        if not _SCHEMA_NAME_PATTERN.match(schema_name):
            raise ValueError(
                f"Schema name invalido: '{schema_name}'. "
                "Apenas schemas com prefixo 'tenant_', 'public' ou 'platform' sao permitidos."
            )

    async def dispose(self) -> None:
        """Fecha todas as conexoes do pool."""
        await self._engine.dispose()

    @property
    def engine(self) -> AsyncEngine:
        """Acesso ao engine para operacoes administrativas."""
        return self._engine
