from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, fleet, trips, analytics, alerts, ai_router
from seed.seed_data import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    await init_db()
    print("Seeding demo data...")
    try:
        await seed_if_empty()
    except Exception as e:
        print(f"Seed warning (non-fatal): {e}")
    print("Backend ready.")
    yield
    print("Backend shutting down.")


app = FastAPI(
    title="LogiSense 360 API",
    description="Logistics Intelligence Platform for Indian Mid-Market",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(fleet.router)
app.include_router(trips.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(ai_router.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "logisense-backend"}
