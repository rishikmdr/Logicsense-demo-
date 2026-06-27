from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from database import get_db
from models.trip import Trip
from auth.rbac import require_permission, CurrentUser

router = APIRouter(prefix="/trips", tags=["trips"])


def trip_dict(t: Trip) -> dict:
    return {
        "id": t.id,
        "trip_number": t.trip_number,
        "status": t.status,
        "vehicle_id": t.vehicle_id,
        "driver_id": t.driver_id,
        "origin_city": t.origin_city,
        "destination_city": t.destination_city,
        "distance_km": t.distance_km,
        "cargo_type": t.cargo_type,
        "cargo_weight_tons": t.cargo_weight_tons,
        "planned_departure": str(t.planned_departure) if t.planned_departure else None,
        "actual_departure": str(t.actual_departure) if t.actual_departure else None,
        "planned_arrival": str(t.planned_arrival) if t.planned_arrival else None,
        "actual_arrival": str(t.actual_arrival) if t.actual_arrival else None,
        "revenue_inr": t.revenue_inr,
        "total_cost_inr": t.total_cost_inr,
        "profit_inr": t.profit_inr,
        "cost_per_km": t.cost_per_km,
        "progress_pct": t.progress_pct,
        "origin_lat": t.origin_lat,
        "origin_lng": t.origin_lng,
        "destination_lat": t.destination_lat,
        "destination_lng": t.destination_lng,
    }


@router.get("")
async def list_trips(
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: CurrentUser = require_permission("trips:read"),
    db: AsyncSession = Depends(get_db),
):
    q = select(Trip).where(Trip.company_id == current_user.company_id)
    if status:
        q = q.where(Trip.status == status)
    q = q.order_by(Trip.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [trip_dict(t) for t in result.scalars().all()]


@router.get("/active")
async def active_trips(
    current_user: CurrentUser = require_permission("trips:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trip).where(
            Trip.company_id == current_user.company_id,
            Trip.status.in_(["dispatched", "in_transit"]),
        )
    )
    return [trip_dict(t) for t in result.scalars().all()]


@router.get("/kpis")
async def trip_kpis(
    current_user: CurrentUser = require_permission("trips:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(Trip.id).label("total"),
            func.sum(Trip.revenue_inr).label("total_revenue"),
            func.sum(Trip.profit_inr).label("total_profit"),
            func.avg(Trip.cost_per_km).label("avg_cost_per_km"),
        ).where(Trip.company_id == current_user.company_id)
    )
    row = result.one()

    delivered = await db.execute(
        select(func.count(Trip.id)).where(
            Trip.company_id == current_user.company_id,
            Trip.status == "delivered",
        )
    )
    delivered_count = delivered.scalar() or 0
    total = row.total or 1

    return {
        "total_trips": row.total or 0,
        "delivered_trips": delivered_count,
        "total_revenue_inr": round(row.total_revenue or 0, 2),
        "total_profit_inr": round(row.total_profit or 0, 2),
        "avg_cost_per_km": round(row.avg_cost_per_km or 0, 2),
        "otif_pct": round(delivered_count / total * 100, 1),
    }
