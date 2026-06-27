from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from database import get_db
from models.trip import Trip
from models.vehicle import Vehicle
from auth.rbac import require_permission, CurrentUser

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/kpis/summary")
async def kpi_summary(
    current_user: CurrentUser = require_permission("analytics:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(Trip.id).label("total"),
            func.sum(Trip.revenue_inr).label("revenue"),
            func.sum(Trip.profit_inr).label("profit"),
            func.avg(Trip.cost_per_km).label("cost_per_km"),
        ).where(Trip.company_id == current_user.company_id)
    )
    row = result.one()

    delivered = await db.execute(
        select(func.count(Trip.id)).where(
            Trip.company_id == current_user.company_id,
            Trip.status == "delivered",
            Trip.actual_arrival <= Trip.planned_arrival,
        )
    )
    on_time = delivered.scalar() or 0
    total = row.total or 1

    fleet = await db.execute(
        select(
            func.count(Vehicle.id).label("total"),
            func.count(Vehicle.id).filter(Vehicle.status == "active").label("active"),
        ).where(Vehicle.company_id == current_user.company_id)
    )
    frow = fleet.one()

    return {
        "total_trips": row.total or 0,
        "total_revenue_inr": round(row.revenue or 0),
        "total_profit_inr": round(row.profit or 0),
        "avg_cost_per_km": round(row.cost_per_km or 0, 2),
        "otif_pct": round(on_time / total * 100, 1),
        "fleet_utilization_pct": round((frow.active or 0) / max(frow.total, 1) * 100, 1),
    }


@router.get("/kpis/trends")
async def kpi_trends(
    current_user: CurrentUser = require_permission("analytics:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.date_trunc("week", Trip.planned_departure).label("week"),
            func.count(Trip.id).label("trips"),
            func.sum(Trip.revenue_inr).label("revenue"),
            func.avg(Trip.cost_per_km).label("cost_per_km"),
        )
        .where(Trip.company_id == current_user.company_id, Trip.planned_departure.isnot(None))
        .group_by("week")
        .order_by("week")
        .limit(12)
    )
    rows = result.all()
    return [
        {
            "week": str(r.week)[:10] if r.week else None,
            "trips": r.trips,
            "revenue_inr": round(r.revenue or 0),
            "cost_per_km": round(r.cost_per_km or 0, 2),
        }
        for r in rows
    ]


@router.get("/routes/performance")
async def route_performance(
    current_user: CurrentUser = require_permission("analytics:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Trip.origin_city,
            Trip.destination_city,
            func.count(Trip.id).label("trips"),
            func.avg(Trip.revenue_inr).label("avg_revenue"),
            func.avg(Trip.cost_per_km).label("avg_cost_per_km"),
            func.avg(Trip.distance_km).label("avg_distance"),
        )
        .where(Trip.company_id == current_user.company_id)
        .group_by(Trip.origin_city, Trip.destination_city)
        .order_by(func.count(Trip.id).desc())
        .limit(10)
    )
    rows = result.all()
    return [
        {
            "route": f"{r.origin_city} → {r.destination_city}",
            "trips": r.trips,
            "avg_revenue_inr": round(r.avg_revenue or 0),
            "avg_cost_per_km": round(r.avg_cost_per_km or 0, 2),
            "avg_distance_km": round(r.avg_distance or 0),
        }
        for r in rows
    ]


@router.get("/cost/breakdown")
async def cost_breakdown(
    current_user: CurrentUser = require_permission("analytics:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.sum(Trip.fuel_cost_inr).label("fuel"),
            func.sum(Trip.driver_cost_inr).label("driver"),
            func.sum(Trip.toll_cost_inr).label("toll"),
            func.sum(Trip.maintenance_cost_inr).label("maintenance"),
        ).where(Trip.company_id == current_user.company_id)
    )
    row = result.one()
    return {
        "fuel_inr": round(row.fuel or 0),
        "driver_inr": round(row.driver or 0),
        "toll_inr": round(row.toll or 0),
        "maintenance_inr": round(row.maintenance or 0),
    }
