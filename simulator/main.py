import asyncio
import os
import random
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "logisense")
POSTGRES_USER = os.getenv("POSTGRES_USER", "logisense")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "logisense_secure_2024")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def simulate_tick():
    try:
        async with SessionLocal() as db:
            result = await db.execute(text(
                "SELECT id, vehicle_id, origin_lat, origin_lng, destination_lat, destination_lng, "
                "progress_pct, status FROM trips WHERE status IN ('dispatched', 'in_transit') LIMIT 30"
            ))
            trips = result.fetchall()

            for row in trips:
                trip_id = row[0]
                vehicle_id = row[1]
                olat, olng = row[2], row[3]
                dlat, dlng = row[4], row[5]
                progress = row[6] or 0.0
                status = row[7]

                if olat is None or dlat is None:
                    continue

                new_progress = min(progress + random.uniform(1.5, 4.0), 100.0)
                new_status = status
                arr_actual = None

                if new_progress >= 95:
                    new_status = "delivered"
                    new_progress = 100.0
                    arr_actual = datetime.utcnow()
                elif status == "dispatched":
                    new_status = "in_transit"

                pct = new_progress / 100.0
                cur_lat = olat + (dlat - olat) * pct + random.uniform(-0.01, 0.01)
                cur_lng = olng + (dlng - olng) * pct + random.uniform(-0.01, 0.01)
                cur_speed = random.uniform(40, 80) if new_status == "in_transit" else 0
                cur_fuel = max(10, 80 - new_progress * 0.6 + random.uniform(-5, 5))

                await db.execute(text(
                    "UPDATE trips SET progress_pct=:prog, status=:st, "
                    "actual_arrival=COALESCE(:arr, actual_arrival) WHERE id=:tid"
                ), {"prog": new_progress, "st": new_status, "arr": arr_actual, "tid": trip_id})

                await db.execute(text(
                    "UPDATE vehicles SET current_lat=:lat, current_lng=:lng, current_speed_kmh=:spd, "
                    "fuel_level_pct=:fuel, status=:vst WHERE id=:vid"
                ), {
                    "lat": cur_lat, "lng": cur_lng, "spd": cur_speed, "fuel": cur_fuel,
                    "vst": "active" if new_status == "in_transit" else "idle",
                    "vid": vehicle_id,
                })

            await db.commit()
            print(f"Tick: updated {len(trips)} active trips")
    except Exception as e:
        print(f"Simulator tick error: {e}")


async def main():
    print("GPS Simulator starting...")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(simulate_tick, "interval", seconds=30, id="gps_tick")
    scheduler.start()
    print("Simulator running — updating vehicle positions every 30s")
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
