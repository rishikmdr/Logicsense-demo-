from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database import get_db
from services.ai_service import AIService
from auth.rbac import require_permission, CurrentUser

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = AIService()


class QueryRequest(BaseModel):
    question: str


@router.get("/brief")
async def daily_brief(
    current_user: CurrentUser = require_permission("ai:read"),
    db: AsyncSession = Depends(get_db),
):
    brief = await ai_service.get_daily_brief(db, current_user.company_id)
    return {"brief": brief}


@router.post("/query")
async def nl_query(
    request: QueryRequest,
    current_user: CurrentUser = require_permission("ai:read"),
    db: AsyncSession = Depends(get_db),
):
    answer = await ai_service.answer_question(request.question, db, current_user.company_id)
    return {"answer": answer, "question": request.question}


@router.get("/anomalies")
async def detect_anomalies(
    current_user: CurrentUser = require_permission("ai:read"),
    db: AsyncSession = Depends(get_db),
):
    anomalies = await ai_service.detect_anomalies(db, current_user.company_id)
    return {"anomalies": anomalies}


@router.post("/handover-report")
async def handover_report(
    current_user: CurrentUser = require_permission("ai:read"),
    db: AsyncSession = Depends(get_db),
):
    report = await ai_service.generate_handover_report(db, current_user.company_id)
    return {"report": report}
