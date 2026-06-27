from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    origin_city: Mapped[str] = mapped_column(String(100))
    destination_city: Mapped[str] = mapped_column(String(100))
    sla_hours: Mapped[float] = mapped_column(Float, default=48.0)
    promised_delivery: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    actual_delivery: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    value_inr: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
