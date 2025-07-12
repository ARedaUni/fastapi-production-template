#!/usr/bin/env python3
"""
Database seeding script for initial data setup.

This script creates the initial user and any other required data
for the application to function properly.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import create_user, user_exists
from app.models.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_user(session: AsyncSession) -> None:
    """Create the initial user if it doesn't exist."""
    logger.info("Checking if initial user exists...")

    # Check if user already exists
    existing = await user_exists(
        session,
        settings.FIRST_USERNAME,
        f"{settings.FIRST_USERNAME}@example.com"
    )

    if existing["username_exists"]:
        logger.info(f"User '{settings.FIRST_USERNAME}' already exists, skipping creation")
        return

    logger.info(f"Creating initial user: {settings.FIRST_USERNAME}")

    try:
        user = await create_user(
            session=session,
            username=settings.FIRST_USERNAME,
            email=f"{settings.FIRST_USERNAME}@example.com",
            full_name="Initial User",
            password=settings.FIRST_PASSWORD.get_secret_value(),
        )

        logger.info(f"✅ Successfully created user: {user.username}")

    except Exception as e:
        logger.error(f"❌ Failed to create initial user: {e}")
        raise


async def create_tables() -> None:
    """Create all database tables."""
    logger.info("Creating database tables...")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def seed_database() -> None:
    """Main seeding function."""
    logger.info("🌱 Starting database seeding...")

    try:
        # Create tables first
        await create_tables()

        # Create initial data
        async with AsyncSessionLocal() as session:
            await create_initial_user(session)
            await session.commit()

        logger.info("✅ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        raise
    finally:
        # Close the engine
        await engine.dispose()


async def main() -> None:
    """Entry point for the seeding script."""
    try:
        await seed_database()
    except Exception as e:
        logger.error(f"Seeding script failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
