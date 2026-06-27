from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from database import Base


class VehicleStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    maintenance = "maintenance"
    breakdown = "breakdown"


class VehicleType(str, enum.Enum):
    truck = "truck"
    mini_truck = "mini_truck"
    tempo = "tempo"
    container = "container"
    tanker = "tanker"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=True)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), default="truck")
    make_model: Mapped[str] = mapped_column(String(100))
    capacity_tons: Mapped[float] = mapped_column(Float, default=10.0)
    status: Mapped[str] = mapped_column(String(20), default="idle")
    current_lat: Mapped[float] = mapped_column(Float, nullable=True)
    current_lng: Mapped[float] = mapped_column(Float, nullable=True)
    current_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    fuel_level_pct: Mapped[float] = mapped_column(Float, default=80.0)
    odometer_km: Mapped[float] = mapped_column(Float, default=0.0)
    insurance_expiry: Mapped[date] = mapped_column(Date, nullable=True)
    fitness_expiry: Mapped[date] = mapped_column(Date, nullable=True)
    road_tax_expiry: Mapped[date] = mapped_column(Date, nullable=True)
    puc_expiry: Mapped[date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
