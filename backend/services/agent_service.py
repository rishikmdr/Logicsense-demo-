"""
LogiSense AI Agent — a tool-using assistant that answers questions about the
fleet by calling real data tools against the database.

Supports BOTH providers:
  - Anthropic (Claude)  -> used when ANTHROPIC_API_KEY is set
  - OpenAI (GPT)        -> used when OPENAI_API_KEY is set (and no Anthropic key)
  - Offline demo mode   -> when neither key is set, returns a helpful canned reply

The agent is given a set of tools (get_fleet_summary, get_trip_kpis, ...).
It runs an agentic loop: think -> call tool(s) -> observe -> repeat -> answer.
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from config import get_settings
from models.trip import Trip
from models.vehicle import Vehicle
from models.alert import Alert
from models.driver import Driver

settings = get_settings()

SYSTEM_PROMPT = (
    "You are LogiSense AI, an expert logistics operations analyst for an Indian "
    "mid-market logistics company. You help managers understand fleet performance, "
    "costs, compliance, and risks. Use the provided tools to fetch real data before "
    "answering — never invent numbers. Think step by step and call multiple tools if "
    "needed. Use Indian context: amounts in INR (₹), distances in km, IST timezone, "
    "Indian cities and national highways. Be concise, specific, and action-oriented. "
    "Format answers in markdown with bold key figures."
)

# ── Tool definitions (provider-neutral) ───────────────────────────────────────
TOOL_SPECS = [
    {
        "name": "get_fleet_summary",
        "description": "Get fleet vehicle counts by status (total, active, idle, maintenance, breakdown) and utilization %.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_trip_kpis",
        "description": "Get trip KPIs: total trips, delivered trips, total revenue (INR), total profit (INR), average cost per km, and OTIF %.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_active_trips",
        "description": "List currently active trips (dispatched or in_transit) with origin, destination, progress and vehicle.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_alert_summary",
        "description": "Get counts of unresolved alerts by severity (critical, high, medium, low).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_route_performance",
        "description": "Get per-route performance: trips count, average revenue (INR), average cost per km, average distance. Top routes by volume.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_cost_breakdown",
        "description": "Get total cost split across fuel, driver, toll and maintenance (INR).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_drivers",
        "description": "Get top drivers ranked by performance score, with trip counts and incidents.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "How many drivers to return (default 5)."}},
            "required": [],
        },
    },
]

OFFLINE_REPLY = (
    "**Demo mode (no AI key configured).**\n\n"
    "I'm the LogiSense AI Agent. With an `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in "
    "your `.env`, I can reason over your live fleet data and answer questions like:\n\n"
    "- *Which routes have the worst cost per km, and why?*\n"
    "- *Summarize today's risks and what I should act on first.*\n"
    "- *Compare revenue vs profit and flag low-margin routes.*\n\n"
    "Here's a sample of what I'd return: your fleet is running at **~38% utilization** "
    "with OTIF around **87%**. The **Mumbai → Pune** corridor is your most efficient at "
    "~₹15/km, while long-haul **Delhi → Lucknow** trips carry the highest cost per km. "
    "Two vehicles have fitness certificates expiring within 7 days — prioritise renewals."
)


class AgentService:
    def __init__(self):
        self.provider = None
        self.anthropic_client = None
        self.openai_client = None

        if settings.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.provider = "anthropic"
            except Exception:
                self.anthropic_client = None
        elif settings.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                self.provider = "openai"
            except Exception:
                self.openai_client = None

    # ── Tool implementations ──────────────────────────────────────────────────
    async def _execute_tool(self, name: str, args: dict, db: AsyncSession, company_id: int) -> dict:
        try:
            if name == "get_fleet_summary":
                res = await db.execute(
                    select(Vehicle.status, func.count(Vehicle.id))
                    .where(Vehicle.company_id == company_id)
                    .group_by(Vehicle.status)
                )
                counts = {r[0]: r[1] for r in res.all()}
                total = sum(counts.values()) or 1
                return {
                    "total": sum(counts.values()),
                    "active": counts.get("active", 0),
                    "idle": counts.get("idle", 0),
                    "maintenance": counts.get("maintenance", 0),
                    "breakdown": counts.get("breakdown", 0),
                    "utilization_pct": round(counts.get("active", 0) / total * 100, 1),
                }

            if name == "get_trip_kpis":
                res = await db.execute(
                    select(
                        func.count(Trip.id),
                        func.sum(Trip.revenue_inr),
                        func.sum(Trip.profit_inr),
                        func.avg(Trip.cost_per_km),
                    ).where(Trip.company_id == company_id)
                )
                total, revenue, profit, cpk = res.one()
                delivered = await db.execute(
                    select(func.count(Trip.id)).where(
                        Trip.company_id == company_id, Trip.status == "delivered"
                    )
                )
                d = delivered.scalar() or 0
                return {
                    "total_trips": total or 0,
                    "delivered_trips": d,
                    "total_revenue_inr": round(revenue or 0),
                    "total_profit_inr": round(profit or 0),
                    "avg_cost_per_km": round(cpk or 0, 2),
                    "otif_pct": round(d / (total or 1) * 100, 1),
                }

            if name == "get_active_trips":
                res = await db.execute(
                    select(Trip).where(
                        Trip.company_id == company_id,
                        Trip.status.in_(["dispatched", "in_transit"]),
                    ).limit(25)
                )
                trips = res.scalars().all()
                return {
                    "count": len(trips),
                    "trips": [
                        {
                            "trip_number": t.trip_number,
                            "route": f"{t.origin_city} -> {t.destination_city}",
                            "status": t.status,
                            "progress_pct": round(t.progress_pct, 1),
                            "cargo": t.cargo_type,
                        }
                        for t in trips
                    ],
                }

            if name == "get_alert_summary":
                res = await db.execute(
                    select(Alert.severity, func.count(Alert.id))
                    .where(Alert.company_id == company_id, Alert.is_resolved == False)
                    .group_by(Alert.severity)
                )
                counts = {r[0]: r[1] for r in res.all()}
                return {
                    "total_active": sum(counts.values()),
                    "critical": counts.get("critical", 0),
                    "high": counts.get("high", 0),
                    "medium": counts.get("medium", 0),
                    "low": counts.get("low", 0),
                }

            if name == "get_route_performance":
                res = await db.execute(
                    select(
                        Trip.origin_city,
                        Trip.destination_city,
                        func.count(Trip.id),
                        func.avg(Trip.revenue_inr),
                        func.avg(Trip.cost_per_km),
                        func.avg(Trip.distance_km),
                    )
                    .where(Trip.company_id == company_id)
                    .group_by(Trip.origin_city, Trip.destination_city)
                    .order_by(func.count(Trip.id).desc())
                    .limit(10)
                )
                return {
                    "routes": [
                        {
                            "route": f"{r[0]} -> {r[1]}",
                            "trips": r[2],
                            "avg_revenue_inr": round(r[3] or 0),
                            "avg_cost_per_km": round(r[4] or 0, 2),
                            "avg_distance_km": round(r[5] or 0),
                        }
                        for r in res.all()
                    ]
                }

            if name == "get_cost_breakdown":
                res = await db.execute(
                    select(
                        func.sum(Trip.fuel_cost_inr),
                        func.sum(Trip.driver_cost_inr),
                        func.sum(Trip.toll_cost_inr),
                        func.sum(Trip.maintenance_cost_inr),
                    ).where(Trip.company_id == company_id)
                )
                fuel, driver, toll, maint = res.one()
                return {
                    "fuel_inr": round(fuel or 0),
                    "driver_inr": round(driver or 0),
                    "toll_inr": round(toll or 0),
                    "maintenance_inr": round(maint or 0),
                }

            if name == "get_top_drivers":
                limit = int(args.get("limit", 5))
                res = await db.execute(
                    select(Driver)
                    .where(Driver.company_id == company_id)
                    .order_by(Driver.performance_score.desc())
                    .limit(limit)
                )
                return {
                    "drivers": [
                        {
                            "name": d.full_name,
                            "performance_score": round(d.performance_score, 1),
                            "total_trips": d.total_trips,
                            "incidents": d.incidents,
                        }
                        for d in res.scalars().all()
                    ]
                }

            return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}

    # ── Provider loops ────────────────────────────────────────────────────────
    async def run(self, message: str, db: AsyncSession, company_id: int, history: list | None = None) -> dict:
        history = history or []
        if self.provider == "anthropic":
            return await self._run_anthropic(message, db, company_id, history)
        if self.provider == "openai":
            return await self._run_openai(message, db, company_id, history)
        return {"response": OFFLINE_REPLY, "provider": "offline", "steps": []}

    async def _run_anthropic(self, message, db, company_id, history) -> dict:
        tools = [
            {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
            for t in TOOL_SPECS
        ]
        messages = list(history) + [{"role": "user", "content": message}]
        steps = []

        for _ in range(6):
            resp = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=settings.agent_model_anthropic,
                max_tokens=1200,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
            if resp.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": resp.content})
                tool_results = []
                for block in resp.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input or {}, db, company_id)
                        steps.append({"tool": block.name, "input": block.input, "output": result})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
                continue

            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"response": text, "provider": "anthropic", "steps": steps}

        return {"response": "The agent reached its step limit. Please refine your question.",
                "provider": "anthropic", "steps": steps}

    async def _run_openai(self, message, db, company_id, history) -> dict:
        tools = [
            {"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["parameters"],
            }}
            for t in TOOL_SPECS
        ]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history) + [
            {"role": "user", "content": message}
        ]
        steps = []

        for _ in range(6):
            resp = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=settings.agent_model_openai,
                max_tokens=1200,
                tools=tools,
                messages=messages,
            )
            choice = resp.choices[0].message
            if choice.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in choice.tool_calls
                    ],
                })
                for tc in choice.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except Exception:
                        args = {}
                    result = await self._execute_tool(tc.function.name, args, db, company_id)
                    steps.append({"tool": tc.function.name, "input": args, "output": result})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })
                continue

            return {"response": choice.content or "", "provider": "openai", "steps": steps}

        return {"response": "The agent reached its step limit. Please refine your question.",
                "provider": "openai", "steps": steps}

    def status(self) -> dict:
        return {
            "provider": self.provider or "offline",
            "live": self.provider is not None,
            "tools": [t["name"] for t in TOOL_SPECS],
        }
