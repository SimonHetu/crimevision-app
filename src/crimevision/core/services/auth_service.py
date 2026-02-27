from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import requests


@dataclass
class AuthState:
    token: str
    role: str
    email: str


class AuthService:
    def __init__(self, api_base: str):
        self.api_base = api_base.rstrip("/")
        self.state: Optional[AuthState] = None

    def login_admin(self, email: str, password: str) -> AuthState:
        url = f"{self.api_base}/api/auth/login"

        try:
            r = requests.post(url, json={"email": email, "password": password}, timeout=10)
        except requests.RequestException as e:
            raise RuntimeError(f"Backend inaccessible: {e}") from e

        # essaie d'extraire un message JSON si présent
        msg = None
        try:
            j = r.json()
            msg = j.get("message") or j.get("error")
        except Exception:
            pass

        if r.status_code != 200:
            raise RuntimeError(msg or r.text or f"HTTP {r.status_code}")

        data = (r.json() or {}).get("data") or {}
        token = data.get("token")
        user = data.get("user") or {}
        role = user.get("role")

        if not token:
            raise RuntimeError("Token manquant.")
        if role != "ADMIN":
            raise RuntimeError("Accès refusé: admin seulement.")

        self.state = AuthState(token=token, role=role, email=user.get("email") or email)
        return self.state

    def logout(self):
        self.state = None

    def headers(self) -> dict[str, str]:
        if not self.state:
            return {}
        return {"Authorization": f"Bearer {self.state.token}"}