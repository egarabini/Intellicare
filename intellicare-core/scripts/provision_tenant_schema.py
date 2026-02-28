"""Script de provisionamento de schema para novo tenant.

Cria o schema PostgreSQL para um novo tenant, copiando a estrutura
de tabelas de um schema template.

Uso:
    python provision_tenant_schema.py --tenant-id hospital_einstein
    python provision_tenant_schema.py --tenant-id hospital_einstein --template tenant_template

Requisitos:
    - psycopg2 ou asyncpg
    - DATABASE_URL configurado

Este script e chamado pelo ProvisioningService do intellicare-admin (F1)
durante o cadastro de um novo tenant.
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2
from psycopg2 import sql


def get_connection():
    """Cria conexao com o banco PostgreSQL."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://intellicare:intellicare@localhost:5432/intellicare",
    )
    return psycopg2.connect(database_url)


def create_tenant_schema(
    conn,
    tenant_id: str,
    template_schema: str = "tenant_template",
) -> None:
    """Cria schema para um novo tenant.

    Args:
        conn: Conexao psycopg2
        tenant_id: ID do tenant (slug)
        template_schema: Schema base para copiar a estrutura

    Raises:
        ValueError: Se tenant_id invalido
        RuntimeError: Se schema ja existe ou template nao encontrado
    """
    schema_name = f"tenant_{tenant_id}"

    with conn.cursor() as cur:
        # Verificar se schema ja existe
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
            (schema_name,),
        )
        if cur.fetchone():
            raise RuntimeError(f"Schema '{schema_name}' já existe!")

        # Verificar se template existe
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
            (template_schema,),
        )
        if not cur.fetchone():
            print(f"⚠️  Template '{template_schema}' não encontrado. Criando schema vazio.")
            cur.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
            )
            conn.commit()
            print(f"✅ Schema '{schema_name}' criado (vazio)")
            return

        # Criar schema
        cur.execute(
            sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
        )

        # Listar tabelas do template
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (template_schema,),
        )
        tables = [row[0] for row in cur.fetchall()]

        if not tables:
            print(f"⚠️  Template '{template_schema}' não tem tabelas.")
            conn.commit()
            print(f"✅ Schema '{schema_name}' criado (vazio)")
            return

        # Copiar estrutura de cada tabela (sem dados)
        for table in tables:
            cur.execute(
                sql.SQL("CREATE TABLE {target} (LIKE {source} INCLUDING ALL)").format(
                    target=sql.SQL("{}.{}").format(
                        sql.Identifier(schema_name),
                        sql.Identifier(table),
                    ),
                    source=sql.SQL("{}.{}").format(
                        sql.Identifier(template_schema),
                        sql.Identifier(table),
                    ),
                )
            )
            print(f"  📋 Tabela {schema_name}.{table} criada")

        conn.commit()
        print(f"\n✅ Schema '{schema_name}' provisionado com {len(tables)} tabelas")


def create_platform_schema(conn) -> None:
    """Cria schema da plataforma (se nao existir).

    O schema 'platform' e usado pelo intellicare-admin para
    dados globais: tenants, plans, billing, audit.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'platform'"
        )
        if cur.fetchone():
            print("ℹ️  Schema 'platform' já existe")
            return

        cur.execute("CREATE SCHEMA platform")
        conn.commit()
        print("✅ Schema 'platform' criado")


def create_template_schema(conn) -> None:
    """Cria schema template (se nao existir).

    O template e o modelo base de onde novos tenants copiam suas tabelas.
    As tabelas devem ser criadas via Alembic migrations.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'tenant_template'"
        )
        if cur.fetchone():
            print("ℹ️  Schema 'tenant_template' já existe")
            return

        cur.execute("CREATE SCHEMA tenant_template")
        conn.commit()
        print("✅ Schema 'tenant_template' criado")
        print("   ℹ️  Execute Alembic migrations no tenant_template para criar as tabelas base")


def main() -> None:
    """Ponto de entrada do script."""
    parser = argparse.ArgumentParser(
        description="Provisiona schema PostgreSQL para um novo tenant IntelliCare"
    )
    parser.add_argument(
        "--tenant-id",
        help="ID do tenant (slug alfanumerico, ex: hospital_einstein)",
    )
    parser.add_argument(
        "--template",
        default="tenant_template",
        help="Schema template (default: tenant_template)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Criar schemas base (platform + tenant_template)",
    )

    args = parser.parse_args()

    conn = get_connection()

    try:
        if args.init:
            print("🔧 Inicializando schemas base para multi-tenancy...")
            print()
            create_platform_schema(conn)
            create_template_schema(conn)
            print()
            print("✅ Schemas base criados!")
            print("   Próximo passo: execute Alembic migrations em tenant_template")
            return

        if not args.tenant_id:
            parser.print_help()
            print("\n❌ Especifique --tenant-id ou --init")
            sys.exit(1)

        print(f"🔧 Provisionando schema para tenant '{args.tenant_id}'...")
        print()
        create_tenant_schema(conn, args.tenant_id, args.template)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
