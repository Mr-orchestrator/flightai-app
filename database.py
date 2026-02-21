"""
FlightAI Database Models + Async Connection
PostgreSQL with SQLAlchemy async ORM
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/flightai"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    interests = Column(JSON, default=list)
    budget_level = Column(String(20), default="moderate")
    travel_style = Column(String(20), default="mixed")

    user = relationship("User", back_populates="preferences")


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get an async database session."""
    async with async_session() as session:
        yield session
