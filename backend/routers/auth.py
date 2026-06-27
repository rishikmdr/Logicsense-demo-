from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models.user import User
from auth.jwt import verify_password, create_access_token, create_refresh_token
from auth.rbac import get_current_user, CurrentUser, ROLE_PERMISSIONS

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_USERS = [
    {"email": "admin@fasttrack.in", "password": "Admin@123", "role": "admin", "name": "Arjun Mehta"},
    {"email": "ops@fasttrack.in", "password": "Ops@123", "role": "operations_manager", "name": "Priya Sharma"},
    {"email": "finance@fasttrack.in", "password": "Finance@123", "role": "finance_manager", "name": "Rahul Gupta"},
    {"email": "branch@fasttrack.in", "password": "Branch@123", "role": "branch_manager", "name": "Sunita Patel"},
    {"email": "driver1@fasttrack.in", "password": "Driver@123", "role": "driver", "name": "Ramesh Kumar"},
    {"email": "customer@acme.in", "password": "Customer@123", "role": "customer", "name": "Vijay Reddy"},
]


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == request.email.lower().strip(), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_id": user.company_id,
            "permissions": ROLE_PERMISSIONS.get(user.role, []),
        },
    }


@router.get("/demo-users")
async def get_demo_users():
    return [
        {"email": u["email"], "password": u["password"], "role": u["role"], "name": u["name"]}
        for u in DEMO_USERS
    ]


@router.get("/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company_id": current_user.company_id,
        "permissions": current_user.permissions,
    }
