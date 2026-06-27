from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from database import get_db
from models.alert import Alert
from auth.rbac import require_permission, CurrentUser

router = APIRouter(prefix="/alerts", tags=["alerts"])


def alert_dict(a: Alert) -> dict:
    return {
        "id": a.id,
        "alert_type": a.alert_type,
        "severity": a.severity,
        "title": a.title,
        "description": a.description,
        "ai_analysis": a.ai_analysis,
        "is_resolved": a.is_resolved,
        "vehicle_id": a.vehicle_id,
        "trip_id": a.trip_id,
        "driver_id": a.driver_id,
        "created_at": str(a.created_at),
        "resolved_at": str(a.resolved_at) if a.resolved_at else None,
    }


@router.get("")
async def list_alerts(
    severity: str = None,
    resolved: bool = False,
    limit: int = Query(default=50, le=200),
    current_user: CurrentUser = require_permission("alerts:read"),
    db: AsyncSession = Depends(get_db),
):
    q = select(Alert).where(
        Alert.company_id == current_user.company_id,
        Alert.is_resolved == resolved,
    )
    if severity:
        q = q.where(Alert.severity == severity)
    q = q.order_by(Alert.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return [alert_dict(a) for a in result.scalars().all()]


@router.get("/summary")
async def alert_summary(
    current_user: CurrentUser = require_permission("alerts:read"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.company_id == current_user.company_id, Alert.is_resolved == False)
        .group_by(Alert.severity)
    )
    rows = result.all()
    summary = {r[0]: r[1] for r in rows}
    return {
        "total_active": sum(summary.values()),
        "critical": summary.get("critical", 0),
        "high": summary.get("high", 0),
        "medium": summary.get("medium", 0),
        "low": summary.get("low", 0),
    }


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: CurrentUser = require_permission("alerts:write"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.company_id == current_user.company_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    return {"success": True, "alert_id": alert_id}
