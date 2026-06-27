import random
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database import AsyncSessionLocal
from models.user import Company, Branch, User
from models.vehicle import Vehicle
from models.driver import Driver
from models.trip import Trip
from models.order import Order
from models.alert import Alert
from auth.jwt import get_password_hash

COMPANIES = [
    {"name": "FastTrack Logistics Pvt Ltd", "gst": "27AABCF1234A1Z5", "city": "Mumbai"},
    {"name": "BharatMove Solutions", "gst": "29AABCB5678B2Z6", "city": "Bangalore"},
    {"name": "NorthStar Transport Ltd", "gst": "07AABCN9012C3Z7", "city": "Delhi"},
]

BRANCHES = [
    # FastTrack (company_id=1)
    {"company_idx": 0, "name": "Mumbai HQ", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
    {"company_idx": 0, "name": "Pune Branch", "city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
    {"company_idx": 0, "name": "Nashik Hub", "city": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lng": 73.7898},
    {"company_idx": 0, "name": "Nagpur Depot", "city": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882},
    # BharatMove (company_id=2)
    {"company_idx": 1, "name": "Bangalore HQ", "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
    {"company_idx": 1, "name": "Chennai Hub", "city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
    {"company_idx": 1, "name": "Hyderabad Branch", "city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
    {"company_idx": 1, "name": "Coimbatore Depot", "city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lng": 76.9558},
    # NorthStar (company_id=3)
    {"company_idx": 2, "name": "Delhi HQ", "city": "Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"company_idx": 2, "name": "Jaipur Branch", "city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873},
    {"company_idx": 2, "name": "Chandigarh Hub", "city": "Chandigarh", "state": "Punjab", "lat": 30.7333, "lng": 76.7794},
    {"company_idx": 2, "name": "Lucknow Depot", "city": "Lucknow", "state": "UP", "lat": 26.8467, "lng": 80.9462},
]

DEMO_USERS = [
    {"email": "admin@fasttrack.in", "password": "Admin@123", "name": "Arjun Mehta", "role": "admin", "company_idx": 0},
    {"email": "ops@fasttrack.in", "password": "Ops@123", "name": "Priya Sharma", "role": "operations_manager", "company_idx": 0},
    {"email": "finance@fasttrack.in", "password": "Finance@123", "name": "Rahul Gupta", "role": "finance_manager", "company_idx": 0},
    {"email": "branch@fasttrack.in", "password": "Branch@123", "name": "Sunita Patel", "role": "branch_manager", "company_idx": 0},
    {"email": "driver1@fasttrack.in", "password": "Driver@123", "name": "Ramesh Kumar", "role": "driver", "company_idx": 0},
    {"email": "customer@acme.in", "password": "Customer@123", "name": "Vijay Reddy", "role": "customer", "company_idx": 0},
]

DRIVER_NAMES = [
    "Ramesh Kumar", "Suresh Singh", "Mahesh Patel", "Dinesh Sharma", "Ganesh Yadav",
    "Rajesh Verma", "Umesh Gupta", "Naresh Tiwari", "Haresh Modi", "Karesh Nair",
    "Arun Mishra", "Tarun Chauhan", "Varun Joshi", "Kiran Rao", "Rajan Pillai",
    "Mohan Das", "Rohan Reddy", "Sohan Murthy", "Johan Fernandez", "Anand Krishnan",
    "Vijay Pandey", "Sanjay Thakur", "Ajay Bose", "Bijay Nanda", "Nilay Mehta",
    "Prakash Sawant", "Vikash Bhatt", "Deepak Jain", "Rupak Shah", "Supak Garg",
    "Amit Agarwal", "Sumit Bansal", "Rohit Kapoor", "Mohit Arora", "Ankit Saxena",
    "Manish Tyagi", "Satish Dubey", "Rajiv Malhotra", "Naveen Kumar", "Praveen Das",
    "Ashok Shetty", "Vinod Kamath", "Manoj Hegde", "Pramod Poojary", "Shyam Bhat",
]

STATES = ["MH", "KA", "TN", "DL", "RJ", "UP", "GJ", "PB", "HR", "AP"]
VEHICLE_TYPES = ["truck", "mini_truck", "tempo", "container", "tanker"]
MAKES = ["Tata 407", "Ashok Leyland 2518", "Eicher 10.90", "Mahindra Furio", "BharatBenz 1217"]
CARGO_TYPES = ["FMCG", "Auto Parts", "Textiles", "Pharma", "Electronics", "Cement", "Steel", "Agri Produce"]

ROUTES = [
    {"origin": "Mumbai", "dest": "Pune", "dist": 150, "olat": 19.0760, "olng": 72.8777, "dlat": 18.5204, "dlng": 73.8567},
    {"origin": "Mumbai", "dest": "Nashik", "dist": 165, "olat": 19.0760, "olng": 72.8777, "dlat": 19.9975, "dlng": 73.7898},
    {"origin": "Mumbai", "dest": "Ahmedabad", "dist": 524, "olat": 19.0760, "olng": 72.8777, "dlat": 23.0225, "dlng": 72.5714},
    {"origin": "Bangalore", "dest": "Chennai", "dist": 346, "olat": 12.9716, "olng": 77.5946, "dlat": 13.0827, "dlng": 80.2707},
    {"origin": "Bangalore", "dest": "Hyderabad", "dist": 570, "olat": 12.9716, "olng": 77.5946, "dlat": 17.3850, "dlng": 78.4867},
    {"origin": "Delhi", "dest": "Jaipur", "dist": 270, "olat": 28.6139, "olng": 77.2090, "dlat": 26.9124, "dlng": 75.7873},
    {"origin": "Delhi", "dest": "Chandigarh", "dist": 260, "olat": 28.6139, "olng": 77.2090, "dlat": 30.7333, "dlng": 76.7794},
    {"origin": "Delhi", "dest": "Lucknow", "dist": 560, "olat": 28.6139, "olng": 77.2090, "dlat": 26.8467, "dlng": 80.9462},
    {"origin": "Pune", "dest": "Nagpur", "dist": 720, "olat": 18.5204, "olng": 73.8567, "dlat": 21.1458, "dlng": 79.0882},
    {"origin": "Chennai", "dest": "Coimbatore", "dist": 495, "olat": 13.0827, "olng": 80.2707, "dlat": 11.0168, "dlng": 76.9558},
]


def random_reg(state: str, idx: int) -> str:
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    l1 = letters[idx % len(letters)]
    l2 = letters[(idx // len(letters)) % len(letters)]
    num = 1000 + (idx * 37 % 9000)
    return f"{state}-{(idx % 20) + 1:02d}-{l1}{l2}-{num}"


def random_date_near(days_offset: int, spread: int = 30) -> date:
    delta = days_offset + random.randint(-spread, spread)
    return date.today() + timedelta(days=delta)


async def seed_if_empty():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Company))
        if result.scalars().first():
            return
    await seed_all()


async def seed_all():
    async with AsyncSessionLocal() as db:
        # Companies
        companies = []
        for c in COMPANIES:
            co = Company(name=c["name"], gst_number=c["gst"], hq_city=c["city"])
            db.add(co)
        await db.flush()
        result = await db.execute(select(Company))
        companies = result.scalars().all()

        # Branches
        branch_objs = []
        for b in BRANCHES:
            co = companies[b["company_idx"]]
            br = Branch(
                company_id=co.id,
                name=b["name"],
                city=b["city"],
                state=b["state"],
                lat=b["lat"],
                lng=b["lng"],
            )
            db.add(br)
        await db.flush()
        result = await db.execute(select(Branch))
        branch_objs = result.scalars().all()

        # Vehicles — 50 per company
        vehicle_objs = []
        used_regs = set()
        for co_idx, co in enumerate(companies):
            co_branches = [b for b in branch_objs if b.company_id == co.id]
            for i in range(50):
                state = STATES[co_idx * 3 + (i % 3)]
                for attempt in range(20):
                    reg = random_reg(state, i + co_idx * 50 + attempt * 150)
                    if reg not in used_regs:
                        used_regs.add(reg)
                        break
                vtype = VEHICLE_TYPES[i % len(VEHICLE_TYPES)]
                branch = co_branches[i % len(co_branches)]
                v = Vehicle(
                    company_id=co.id,
                    branch_id=branch.id,
                    registration_number=reg,
                    vehicle_type=vtype,
                    make_model=MAKES[i % len(MAKES)],
                    capacity_tons=random.choice([5.0, 7.5, 10.0, 15.0, 20.0]),
                    status=random.choices(["active", "idle", "maintenance", "breakdown"], weights=[40, 40, 15, 5])[0],
                    current_lat=branch.lat + random.uniform(-0.5, 0.5),
                    current_lng=branch.lng + random.uniform(-0.5, 0.5),
                    current_speed_kmh=random.uniform(0, 80) if random.random() > 0.5 else 0,
                    fuel_level_pct=random.uniform(20, 100),
                    odometer_km=random.uniform(10000, 300000),
                    insurance_expiry=random_date_near(random.randint(-30, 365)),
                    fitness_expiry=random_date_near(random.randint(-10, 180)),
                    road_tax_expiry=random_date_near(random.randint(30, 365)),
                    puc_expiry=random_date_near(random.randint(-5, 90)),
                )
                db.add(v)
                vehicle_objs.append(v)
        await db.flush()
        result = await db.execute(select(Vehicle))
        vehicle_objs = result.scalars().all()

        # Drivers — 15 per company
        driver_objs = []
        used_licenses = set()
        for co_idx, co in enumerate(companies):
            for i in range(15):
                name = DRIVER_NAMES[(co_idx * 15 + i) % len(DRIVER_NAMES)]
                lic = f"DL{co_idx:02d}{i:04d}{random.randint(10, 99)}"
                while lic in used_licenses:
                    lic = f"DL{co_idx:02d}{i:04d}{random.randint(10, 99)}"
                used_licenses.add(lic)
                d = Driver(
                    company_id=co.id,
                    full_name=name,
                    license_number=lic,
                    license_expiry=random_date_near(random.randint(30, 730)),
                    phone=f"9{random.randint(100000000, 999999999)}",
                    performance_score=random.uniform(65, 98),
                    total_trips=random.randint(50, 800),
                    incidents=random.randint(0, 5),
                )
                db.add(d)
        await db.flush()
        result = await db.execute(select(Driver))
        driver_objs = result.scalars().all()

        # Trips — ~833 per company across 90 days
        trip_num = 1000
        statuses = ["delivered", "delivered", "delivered", "delivered", "delivered", "delivered", "in_transit", "dispatched", "cancelled"]
        for co_idx, co in enumerate(companies):
            co_vehicles = [v for v in vehicle_objs if v.company_id == co.id]
            co_drivers = [d for d in driver_objs if d.company_id == co.id]
            for i in range(833):
                route = ROUTES[i % len(ROUTES)]
                days_ago = random.randint(0, 90)
                dep = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
                status = random.choice(statuses)
                sla_hours = route["dist"] / 60 * 1.5
                arr_planned = dep + timedelta(hours=sla_hours)
                arr_actual = arr_planned + timedelta(hours=random.uniform(-2, 6)) if status == "delivered" else None
                dist = route["dist"] * random.uniform(0.95, 1.10)
                fuel = dist * random.uniform(3.5, 5.5)
                driver_cost = random.uniform(800, 2000)
                toll = dist * random.uniform(0.5, 1.2)
                maint = random.uniform(0, 500)
                total_cost = fuel + driver_cost + toll + maint
                revenue = total_cost * random.uniform(1.1, 1.5)
                profit = revenue - total_cost
                trip_num += 1
                t = Trip(
                    company_id=co.id,
                    vehicle_id=random.choice(co_vehicles).id,
                    driver_id=random.choice(co_drivers).id,
                    trip_number=f"TRP-{trip_num}",
                    status=status,
                    origin_city=route["origin"],
                    destination_city=route["dest"],
                    origin_lat=route["olat"],
                    origin_lng=route["olng"],
                    destination_lat=route["dlat"],
                    destination_lng=route["dlng"],
                    distance_km=round(dist, 1),
                    cargo_type=random.choice(CARGO_TYPES),
                    cargo_weight_tons=random.uniform(2, 15),
                    planned_departure=dep,
                    actual_departure=dep + timedelta(minutes=random.randint(-30, 60)),
                    planned_arrival=arr_planned,
                    actual_arrival=arr_actual,
                    revenue_inr=round(revenue, 2),
                    fuel_cost_inr=round(fuel, 2),
                    driver_cost_inr=round(driver_cost, 2),
                    toll_cost_inr=round(toll, 2),
                    maintenance_cost_inr=round(maint, 2),
                    total_cost_inr=round(total_cost, 2),
                    profit_inr=round(profit, 2),
                    cost_per_km=round(total_cost / max(dist, 1), 2),
                    progress_pct=100.0 if status == "delivered" else random.uniform(10, 90),
                )
                db.add(t)

        await db.flush()

        # Alerts
        alert_templates = [
            ("overspeed", "high", "Overspeed Alert", "Vehicle exceeded 80 km/h speed limit on highway"),
            ("geofence", "medium", "Geofence Violation", "Vehicle moved outside authorized zone"),
            ("doc_expiry", "critical", "Document Expiry Warning", "Vehicle fitness certificate expiring within 7 days"),
            ("sla_breach", "high", "SLA Breach Risk", "Shipment at risk of missing delivery window"),
            ("fuel_anomaly", "high", "Fuel Anomaly Detected", "Fuel consumption 30% above route average"),
        ]
        for co_idx, co in enumerate(companies):
            co_vehicles = [v for v in vehicle_objs if v.company_id == co.id]
            for i in range(17):
                tmpl = alert_templates[i % len(alert_templates)]
                v = random.choice(co_vehicles)
                a = Alert(
                    company_id=co.id,
                    vehicle_id=v.id,
                    alert_type=tmpl[0],
                    severity=tmpl[1],
                    title=tmpl[2],
                    description=f"{tmpl[3]} — Vehicle {v.registration_number}",
                    is_resolved=random.random() > 0.6,
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
                )
                db.add(a)

        # Demo users
        result = await db.execute(select(Company).where(Company.name == "FastTrack Logistics Pvt Ltd"))
        fasttrack = result.scalar_one()
        for u in DEMO_USERS:
            user = User(
                company_id=fasttrack.id,
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["name"],
                role=u["role"],
                is_active=True,
            )
            db.add(user)

        await db.commit()
        print("Seed complete: companies, branches, vehicles, drivers, trips, alerts, and demo users created.")
