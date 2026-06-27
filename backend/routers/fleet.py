from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models.vehicle import Vehicle
from auth.rbac import require_permission, CurrentUser

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/vehicles")
async def list_vehicles(
    status: str = None,
    limit: int = Query(default=200, le=500),
    current_user: CurrentUser = require_permission("fleet:read"),
    db: AsyncSession = Depends(get_db),
):
    q = select(Vehicle).where(Vehicle.company_id == current_user.company_id)
    if status:
        q = q.where(Vehicle.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    vehicles = result.scalars().all()
    return [
        {
            "id": v.id,
            "registration_number": v.registration_number,
            "vehicle_type": v.vehicle_type,
            "make_model": v.make_model,
            "status": v.status,
            "current_lat": v.current_lat,
            "current_lng": v.current_lng,
            "current_speed_kmh": v.current_speed_kmh,
            "fuel_level_pct": v.fuel_level_pct,
            "odometer_km": v.odometer_km,
            "capacity_tons": v.capacity_tons,
            "insurance_expiry": str(v.insurance_expiry) if v.insurance_expiry else None,
            "fitness_expiry": str(v.fitness_expiry) if v.fitness_expiry else None,
            "road_tax_expiry": str(v.road_tax_expiry) if v.road_tax_expiry else None,
            "puc_expiry": str(v.puc_expiry) if v.puc_expiry else None,
        }
        for v in vehicles
    ]


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: int,
    current_user: CurrentUser = require_permission("fleet:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.company_id == current_user.company_id)
    )
    v = result.scalar_one_or_none()
    if not v:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {
        "id": v.id,
        "registration_number": v.registration_number,
        "vehicle_type": v.vehicle_type,
        "make_model": v.make_model,
        "status": v.status,
        "current_lat": v.current_lat,
        "current_lng": v.current_lng,
        "current_speed_kmh": v.current_speed_kmh,
        "fuel_level_pct": v.fuel_level_pct,
        "odometer_km": v.odometer_km,
        "capacity_tons": v.capacity_tons,
    }


@router.get("/summary")
async def fleet_summary(
    current_user: CurrentUser = require_permission("fleet:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle.status, func.count(Vehicle.id))
        .where(Vehicle.company_id == current_user.company_id)
        .group_by(Vehicle.status)
    )
    rows = result.all()
    summary = {r[0]: r[1] for r in rows}
    total = sum(summary.values())
    return {
        "total": total,
        "active": summary.get("active", 0),
        "idle": summary.get("idle", 0),
        "maintenance": summary.get("maintenance", 0),
        "breakdown": summary.get("breakdown", 0),
        "utilization_pct": round(summary.get("active", 0) / total * 100, 1) if total else 0,
    }
