# database.py
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

# --- SQLAlchemy and SQLModel Imports ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
# FIX: Import AsyncSession from SQLModel to get the .exec() method
from sqlmodel.ext.asyncio.session import AsyncSession
from schema import SQLModel # Use your own models file

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

# The DATABASE_URL from Neon uses postgres://.
# SQLAlchemy's async engine needs postgresql+asyncpg://
engine_url = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")

# Remove the 'sslmode' query parameter if it exists
if '?' in engine_url:
    engine_url = engine_url.split('?')[0]

# Create the async engine
engine: AsyncEngine = create_async_engine(engine_url, echo=True, future=True)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a SQLModel-specific asynchronous database session.
    """
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session