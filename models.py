"""
SQLAlchemy ORM models for the Public Transport Tracking system.
"""

from sqlalchemy import (
    Column, BigInteger, Float, Boolean, TIMESTAMP, String,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

from config import SCHEMA_NAME

Base = declarative_base()


class Bus(Base):
    """Represents a bus in the transport fleet."""
    __tablename__ = "buses"
    __table_args__ = {"schema": SCHEMA_NAME}

    bus_id = Column(BigInteger, primary_key=True, autoincrement=True)
    bus_number = Column(String(20), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    locations = relationship(
        "BusLocation", 
        back_populates="bus", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    route_assignments = relationship(
        "BusRoute", 
        back_populates="bus", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Bus(bus_id={self.bus_id}, bus_number=\'{self.bus_number}\')>"


class Route(Base):
    """Represents a bus route with multiple stops."""
    __tablename__ = "routes"
    __table_args__ = {"schema": SCHEMA_NAME}

    route_id = Column(BigInteger, primary_key=True, autoincrement=True)
    route_name = Column(String(100), nullable=False)
    route_number = Column(String(20), nullable=True, unique=True, index=True)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    stops = relationship(
        "Stop", 
        back_populates="route", 
        order_by="Stop.stop_order", 
        cascade="all, delete-orphan"
    )
    bus_assignments = relationship(
        "BusRoute", 
        back_populates="route", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Route(route_id={self.route_id}, route_name=\'{self.route_name}\')>"


class Stop(Base):
    """Represents a stop on a bus route."""
    __tablename__ = "stops"
    __table_args__ = (
        Index("idx_route_stop_order", "route_id", "stop_order"),
        {"schema": SCHEMA_NAME},
    )

    stop_id = Column(BigInteger, primary_key=True, autoincrement=True)
    route_id = Column(
        BigInteger, 
        ForeignKey(f"{SCHEMA_NAME}.routes.route_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    stop_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    stop_order = Column(BigInteger, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    route = relationship("Route", back_populates="stops")

    def __repr__(self):
        return f"<Stop(stop_id={self.stop_id}, stop_name=\'{self.stop_name}\')>"


class BusLocation(Base):
    """Records a bus location at a specific point in time."""
    __tablename__ = "bus_locations"
    __table_args__ = (
        Index("idx_bus_location_bus_time", "bus_id", "recorded_at"),
        Index("idx_bus_location_time", "recorded_at"),
        {"schema": SCHEMA_NAME},
    )

    location_id = Column(BigInteger, primary_key=True, autoincrement=True)
    bus_id = Column(
        BigInteger,
        ForeignKey(f"{SCHEMA_NAME}.buses.bus_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(
        TIMESTAMP(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    bus = relationship("Bus", back_populates="locations")

    def __repr__(self):
        return f"<BusLocation(bus_id={self.bus_id}, lat={self.latitude}, lon={self.longitude})>"


class BusRoute(Base):
    """Associates buses with routes (many-to-many relationship)."""
    __tablename__ = "bus_routes"
    __table_args__ = (
        Index("idx_bus_current_route", "bus_id", "is_current"),
        {"schema": SCHEMA_NAME}
    )

    bus_id = Column(
        BigInteger,
        ForeignKey(f"{SCHEMA_NAME}.buses.bus_id", ondelete="CASCADE"),
        primary_key=True
    )
    route_id = Column(
        BigInteger,
        ForeignKey(f"{SCHEMA_NAME}.routes.route_id", ondelete="CASCADE"),
        primary_key=True
    )
    assigned_at = Column(
        TIMESTAMP(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    is_current = Column(Boolean, default=True, nullable=False, index=True)

    bus = relationship("Bus", back_populates="route_assignments")
    route = relationship("Route", back_populates="bus_assignments")

    def __repr__(self):
        return f"<BusRoute(bus_id={self.bus_id}, route_id={self.route_id})>"
