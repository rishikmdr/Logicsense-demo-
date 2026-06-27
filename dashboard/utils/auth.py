import streamlit as st
from utils.api import login as api_login

ROLE_PERMISSIONS = {
    "admin": [
        "fleet:read", "fleet:write", "trips:read", "trips:write",
        "analytics:read", "alerts:read", "alerts:write", "finance:read",
        "ai:read", "compliance:read",
    ],
    "operations_manager": [
        "fleet:read", "fleet:write", "trips:read", "trips:write",
        "analytics:read", "alerts:read", "alerts:write", "compliance:read", "ai:read",
    ],
    "finance_manager": ["trips:read", "analytics:read", "finance:read", "ai:read"],
    "branch_manager": ["fleet:read", "trips:read", "analytics:read", "alerts:read", "compliance:read"],
    "driver": ["trips:read"],
    "customer": ["trips:read"],
}


def is_logged_in() -> bool:
    return bool(st.session_state.get("access_token"))


def do_login(email: str, password: str) -> dict:
    result = api_login(email, password)
    if result["success"]:
        st.session_state["access_token"] = result["token"]
        st.session_state["user"] = result["user"]
        st.session_state["role"] = result["user"]["role"]
        st.session_state["role_permissions"] = ROLE_PERMISSIONS.get(result["user"]["role"], [])
    return result


def do_logout():
    for key in ["access_token", "user", "role", "role_permissions"]:
        st.session_state.pop(key, None)


def require_login():
    if not is_logged_in():
        st.switch_page("app.py")


def has_permission(perm: str) -> bool:
    perms = st.session_state.get("role_permissions", [])
    return perm in perms


def current_user() -> dict:
    return st.session_state.get("user", {})


def get_token() -> str:
    return st.session_state.get("access_token", "")
