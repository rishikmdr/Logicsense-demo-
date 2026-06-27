import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from config import get_settings
from models.trip import Trip
from models.alert import Alert
from models.vehicle import Vehicle

settings = get_settings()

OFFLINE_BRIEF = """**Daily Operations Brief — LogiSense 360**

Good morning! Here's your fleet intelligence summary:

**Fleet Status**: 42 vehicles active across 8 routes. 3 vehicles in scheduled maintenance.

**Today's Highlights**:
- On-Time-In-Full (OTIF): 87.3% — 2.1% above weekly average
- Cost per km: ₹28.40 — within target range
- 12 active trips en route, estimated on-time delivery rate: 91%

**Alerts Requiring Attention**:
- 2 vehicles approaching document expiry (fitness certificate) in next 7 days
- 1 overspeed incident reported on NH-48 near Pune (driver: Ramesh Kumar)
- SLA breach risk: Mumbai→Ahmedabad shipment delayed by ~2 hours due to traffic

**Revenue Forecast**:
Today's projected revenue: ₹4.2L | Weekly target: ₹28L (on track at 94%)

**Recommendation**: Deploy Vehicle MH-12-AB-3456 from Pune depot for backlog clearance on the Nashik route.

*Powered by LogiSense AI | Data refreshed: real-time*"""

OFFLINE_ANOMALIES = [
    {
        "type": "fuel_anomaly",
        "severity": "high",
        "description": "Vehicle MH-04-CD-7890: Fuel consumption 34% above route average on Delhi-Jaipur corridor. Possible fuel theft or engine issue.",
        "recommendation": "Immediate inspection and fuel sensor calibration check.",
    },
    {
        "type": "route_deviation",
        "severity": "medium",
        "description": "Trip TRP-2847 deviated 45km from planned NH-48 route near Surat without authorization.",
        "recommendation": "Driver debrief required. Check for toll evasion pattern.",
    },
    {
        "type": "idle_time",
        "severity": "low",
        "description": "3 vehicles idling >4 hours at Nagpur depot — above threshold.",
        "recommendation": "Review dispatch scheduling for Nagpur branch.",
    },
]

OFFLINE_HANDOVER = """**Shift Handover Report — LogiSense 360**
*Generated: End of Day Shift*

**Active Trips (Carry-forward)**:
- 8 trips currently in transit
- Next delivery due: 06:00 IST — Mumbai→Pune (TRP-3021)
- Critical: Bangalore→Chennai shipment (TRP-3008) — SLA at risk, monitor closely

**Incidents This Shift**:
- 1 breakdown (MH-09-KL-2341 — tyre puncture on NH-44, recovery dispatched)
- 2 overspeed alerts (resolved with driver communication)

**Tomorrow's Priorities**:
1. 14 dispatches scheduled, 11 vehicles ready
2. Renew fitness certificate for GJ-01-AB-5678 (expires in 3 days)
3. Driver Suresh Nair — mandatory rest day (180+ hours this month)

**Handover to Night Supervisor**: All critical loads covered. Escalate TRP-3008 if delay exceeds 60 min."""


class AIService:
    def __init__(self):
        self.client = None
        if settings.anthropic_api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            except Exception:
                self.client = None

    async def _get_fleet_context(self, db: AsyncSession, company_id: int) -> str:
        trips_result = await db.execute(
            select(
                func.count(Trip.id).label("total"),
                func.sum(Trip.revenue_inr).label("revenue"),
                func.avg(Trip.cost_per_km).label("cost_per_km"),
            ).where(Trip.company_id == company_id)
        )
        tr = trips_result.one()

        alerts_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.company_id == company_id, Alert.is_resolved == False
            )
        )
        active_alerts = alerts_result.scalar() or 0

        fleet_result = await db.execute(
            select(
                func.count(Vehicle.id).label("total"),
                func.count(Vehicle.id).filter(Vehicle.status == "active").label("active"),
            ).where(Vehicle.company_id == company_id)
        )
        fr = fleet_result.one()

        return (
            f"Fleet: {fr.total} vehicles total, {fr.active} active. "
            f"Trips: {tr.total or 0} total, revenue ₹{round((tr.revenue or 0)/100000, 1)}L. "
            f"Avg cost/km: ₹{round(tr.cost_per_km or 0, 2)}. "
            f"Active alerts: {active_alerts}."
        )

    async def get_daily_brief(self, db: AsyncSession, company_id: int) -> str:
        if not self.client:
            return OFFLINE_BRIEF
        context = await self._get_fleet_context(db, company_id)
        try:
            msg = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": (
                        f"You are an AI logistics analyst for an Indian logistics company. "
                        f"Generate a concise daily operations brief based on this data: {context}. "
                        f"Use Indian context (INR, IST, Indian routes). Keep it under 300 words. "
                        f"Format with markdown headers."
                    ),
                }],
            )
            return msg.content[0].text
        except Exception:
            return OFFLINE_BRIEF

    async def answer_question(self, question: str, db: AsyncSession, company_id: int) -> str:
        if not self.client:
            return (
                f"Demo mode: Your question was '{question}'. "
                "In production with an API key, I would analyze your fleet data and provide "
                "a detailed answer. For now, here's a sample: Your fleet shows 87% OTIF rate "
                "this week, with the Mumbai-Pune corridor performing best at ₹24/km cost efficiency."
            )
        context = await self._get_fleet_context(db, company_id)
        try:
            msg = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": (
                        f"You are an AI logistics analyst. Fleet context: {context}. "
                        f"Answer this question concisely: {question}. "
                        f"Use Indian logistics context (INR, Indian routes, IST timezone)."
                    ),
                }],
            )
            return msg.content[0].text
        except Exception:
            return "Unable to process query at this time. Please try again."

    async def detect_anomalies(self, db: AsyncSession, company_id: int) -> list:
        if not self.client:
            return OFFLINE_ANOMALIES
        context = await self._get_fleet_context(db, company_id)
        try:
            msg = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Fleet context: {context}. "
                        "Identify 3 potential anomalies in this logistics fleet. "
                        "Return JSON array with fields: type, severity, description, recommendation. "
                        "Focus on fuel, route, idle time, SLA anomalies."
                    ),
                }],
            )
            import re
            text = msg.content[0].text
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return OFFLINE_ANOMALIES
        except Exception:
            return OFFLINE_ANOMALIES

    async def generate_handover_report(self, db: AsyncSession, company_id: int) -> str:
        if not self.client:
            return OFFLINE_HANDOVER
        context = await self._get_fleet_context(db, company_id)
        try:
            msg = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=700,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Fleet context: {context}. "
                        "Generate a shift handover report for Indian logistics operations. "
                        "Include: active trips, incidents, tomorrow's priorities. "
                        "Use markdown formatting. Keep under 400 words."
                    ),
                }],
            )
            return msg.content[0].text
        except Exception:
            return OFFLINE_HANDOVER
