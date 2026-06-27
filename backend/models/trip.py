from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    trip_number: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="dispatched")
    origin_city: Mapped[str] = mapped_column(String(100))
    destination_city: Mapped[str] = mapped_column(String(100))
    origin_lat: Mapped[float] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=True)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=True)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    cargo_type: Mapped[str] = mapped_column(String(100))
    cargo_weight_tons: Mapped[float] = mapped_column(Float, default=5.0)
    planned_departure: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    actual_departure: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    planned_arrival: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    actual_arrival: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    revenue_inr: Mapped[float] = mapped_column(Float, default=0.0)
    fuel_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    driver_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    toll_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    maintenance_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    profit_inr: Mapped[float] = mapped_column(Float, default=0.0)
    cost_per_km: Mapped[float] = mapped_column(Float, default=0.0)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    gps_track: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
