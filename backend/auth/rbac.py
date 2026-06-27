from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth.jwt import decode_token
from models.user import User

bearer = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "admin": [
        "fleet:read", "fleet:write",
        "trips:read", "trips:write",
        "analytics:read",
        "alerts:read", "alerts:write",
        "finance:read",
        "ai:read",
        "compliance:read",
    ],
    "operations_manager": [
        "fleet:read", "fleet:write",
        "trips:read", "trips:write",
        "analytics:read",
        "alerts:read", "alerts:write",
        "compliance:read",
        "ai:read",
    ],
    "finance_manager": [
        "trips:read",
        "analytics:read",
        "finance:read",
        "ai:read",
    ],
    "branch_manager": [
        "fleet:read",
        "trips:read",
        "analytics:read",
        "alerts:read",
        "compliance:read",
    ],
    "driver": [
        "trips:read",
    ],
    "customer": [
        "trips:read",
    ],
}


class CurrentUser:
    def __init__(self, user: User):
        self.id = user.id
        self.email = user.email
        self.full_name = user.full_name
        self.role = user.role
        self.company_id = user.company_id
        self.branch_ids = user.branch_ids or []
        self.permissions = ROLE_PERMISSIONS.get(user.role, [])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id), User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(user)


def require_permission(permission: str):
    async def checker(current_user: CurrentUser = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission}")
        return current_user
    return Depends(checker)
