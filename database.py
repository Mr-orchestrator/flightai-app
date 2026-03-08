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
    booking_history = relationship("BookingHistory", back_populates="user", lazy="selectin")
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


class BookingHistory(Base):
    """Explicit booking signals — primary source for personalization inference."""
    __tablename__ = "booking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    origin_iata = Column(String(3), nullable=False)
    destination_iata = Column(String(3), nullable=False)
    destination_city = Column(String(255), nullable=True)
    duration_days = Column(Integer, nullable=True)
    cabin_class = Column(String(20), nullable=True)           # ECONOMY / BUSINESS
    hotel_star_rating = Column(Integer, nullable=True)         # 3 / 4 / 5
    carrier_codes = Column(JSON, default=list)                 # ["EK", "QR"]
    hotel_name = Column(String(255), nullable=True)
    total_price_inr = Column(Integer, nullable=True)
    tier_selected = Column(String(20), nullable=True)          # budget / standard / premium
    package_snapshot_id = Column(String(36), ForeignKey("package_snapshots.id"), nullable=True)
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="booking_history")


class EngagementSignal(Base):
    """Implicit behavioral signals — secondary source for personalization (weight: 0.4)."""
    __tablename__ = "engagement_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)           # "tier_expand" | "tier_view"
    destination_iata = Column(String(3), nullable=True)
    tier = Column(String(20), nullable=True)                   # budget / standard / premium
    cabin_class = Column(String(20), nullable=True)            # from the tier they expanded
    hotel_star_rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    # Extended personalization fields
    budget_range_min = Column(Integer, nullable=True)
    budget_range_max = Column(Integer, nullable=True)
    travel_frequency = Column(String(20), nullable=True)  # monthly/quarterly/yearly/rarely
    dietary_needs = Column(JSON, default=list)
    accessibility_needs = Column(JSON, default=list)
    preferred_airlines = Column(JSON, default=list)  # carrier codes e.g. ["AI", "6E", "EK"]
    onboarding_step = Column(Integer, default=0)

    user = relationship("User", back_populates="preferences")


class PackageSnapshot(Base):
    """Stores selected offer IDs + full package JSON for My Trips."""
    __tablename__ = "package_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tier = Column(String(20), nullable=False)
    destination_iata = Column(String(3), nullable=False)
    destination_city = Column(String(255), nullable=True)
    departure_date = Column(String(10), nullable=True)
    return_date = Column(String(10), nullable=True)
    flight_offer_id = Column(String(100), nullable=True)
    hotel_offer_id = Column(String(100), nullable=True)
    activity_ids = Column(JSON, default=list)
    flight_price_inr = Column(Integer, nullable=True)
    hotel_total_inr = Column(Integer, nullable=True)
    total_package_inr = Column(Integer, nullable=True)
    package_json = Column(JSON, nullable=True)  # Full package data for trip detail
    fx_rate_used = Column(String(50), nullable=True)  # e.g. "USD_TO_INR=83.5"
    created_at = Column(DateTime, default=datetime.utcnow)
    flight_expires_at = Column(DateTime, nullable=True)   # +15 min
    hotel_expires_at = Column(DateTime, nullable=True)    # +2 hours

    user = relationship("User")


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get an async database session."""
    async with async_session() as session:
        yield session
