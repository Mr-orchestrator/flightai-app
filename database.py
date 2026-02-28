"""
FlightAI Database Models + Async Connection
SQLite (aiosqlite) for zero-setup dev, can swap to PostgreSQL via DATABASE_URL
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean, event
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship


# Default to SQLite file in project root — zero config needed
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./flightai.db"
)

# If someone passes a postgres:// URL, convert to postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # SQLite needs check_same_thread=False for async
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    home_airport = Column(String(3), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    travel_history = relationship("TravelHistory", back_populates="user", lazy="selectin")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, lazy="selectin")


class TravelHistory(Base):
    __tablename__ = "travel_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    origin_iata = Column(String(3), nullable=False)
    destination_iata = Column(String(3), nullable=False)
    destination_city = Column(String(255), nullable=True)
    duration_days = Column(Integer, nullable=True)
    query_text = Column(Text, nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="travel_history")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    interests = Column(JSON, default=list)
    budget_level = Column(String(20), default="moderate")
    travel_style = Column(String(20), default="mixed")
    preferred_destinations = Column(JSON, default=list)
    travel_companions = Column(String(20), nullable=True)  # solo/couple/family/friends
    accommodation_preference = Column(String(20), default="hotel")  # hotel/resort/hostel
    onboarding_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="preferences")


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get an async database session."""
    async with async_session() as session:
        yield session
