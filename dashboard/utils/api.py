import os
import requests
from typing import Optional, Dict, List, Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 10


def _headers(token: Optional[str] = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def api_get(path: str, params: Optional[dict] = None, token: Optional[str] = None) -> Optional[Any]:
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, headers=_headers(token), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


def api_post(path: str, data: Optional[dict] = None, token: Optional[str] = None) -> Optional[Any]:
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=data, headers=_headers(token), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


def api_patch(path: str, data: Optional[dict] = None, params: Optional[dict] = None, token: Optional[str] = None) -> Optional[Any]:
    try:
        r = requests.patch(f"{BACKEND_URL}{path}", json=data, params=params, headers=_headers(token), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def backend_is_healthy() -> bool:
    """Check if the backend is reachable."""
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def login(email: str, password: str) -> Dict:
    """
    Returns dict with keys: success, token, user, error
    - success=True, token=..., user=... on valid login
    - success=False, error="backend_down" if backend not reachable
    - success=False, error="invalid_credentials" if wrong email/password
    - success=False, error="server_error" for other server errors
    """
    try:
        r = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return {"success": True, "token": data["access_token"], "user": data["user"]}
        elif r.status_code == 401:
            return {"success": False, "error": "invalid_credentials"}
        else:
            return {"success": False, "error": "server_error", "detail": f"HTTP {r.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "backend_down"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "backend_down"}
    except Exception as e:
        return {"success": False, "error": "server_error", "detail": str(e)}
