from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    full_name: Mapped[str] = mapped_column(String(200))
    license_number: Mapped[str] = mapped_column(String(50), unique=True)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(20))
    performance_score: Mapped[float] = mapped_column(Float, default=85.0)
    total_trips: Mapped[int] = mapped_column(Integer, default=0)
    incidents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
