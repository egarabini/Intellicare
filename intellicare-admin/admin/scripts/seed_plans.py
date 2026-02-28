"""Seed script — Insert default plans into the platform schema.

Usage:
    python -m admin.scripts.seed_plans
"""

import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from admin.config import AdminConfig
from admin.models.plan import Plan
from admin.models.tenant import Base

logger = logging.getLogger(__name__)

PLANS = [
    {
        "name": "trial",
        "display_name": "Trial (30 dias)",
        "max_users": 5,
        "max_sms_month": 100,
        "price_monthly": 0,
        "modules_included": ["zilda", "florence"],
    },
    {
        "name": "basico",
        "display_name": "Básico",
        "max_users": 20,
        "max_sms_month": 500,
        "price_monthly": 999.00,
        "modules_included": ["zilda", "florence", "oswaldo", "geralda"],
    },
    {
        "name": "profissional",
        "display_name": "Profissional",
        "max_users": 100,
        "max_sms_month": 2000,
        "price_monthly": 2499.00,
        "modules_included": [
            "zilda", "florence", "oswaldo", "geralda",
            "donabedian", "comunicacao", "grahame",
        ],
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "max_users": 99999,
        "max_sms_month": 10000,
        "price_monthly": 4999.00,
        "modules_included": [
            "zilda", "florence", "oswaldo", "geralda",
            "donabedian", "comunicacao", "grahame", "wanda",
        ],
    },
]


async def seed() -> None:
    config = AdminConfig()
    engine = create_async_engine(config.database_url)

    async with engine.begin() as conn:
        # Ensure platform schema exists
        await conn.execute(
            __import__("sqlalchemy").text("CREATE SCHEMA IF NOT EXISTS platform")
        )
        await conn.run_sync(Base.metadata.create_all)

    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as session:
        for plan_data in PLANS:
            existing = await session.execute(
                select(Plan).where(Plan.name == plan_data["name"])
            )
            if existing.scalar_one_or_none():
                logger.info("Plan already exists: %s", plan_data["name"])
                continue

            plan = Plan(**plan_data)
            session.add(plan)
            logger.info("Created plan: %s", plan_data["name"])

        await session.commit()

    await engine.dispose()
    logger.info("Seed complete: %d plans", len(PLANS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
