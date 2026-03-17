"""Adapter para geracao de JWTs e URLs do Jitsi."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt

from ..config import CareplannerSettings


class JitsiAdapter:
    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings

    def generate_room_jwt(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        is_moderator: bool = False,
        expires_in_minutes: int | None = None,
    ) -> str:
        duration = expires_in_minutes or self._settings.jitsi_default_room_duration
        now = datetime.now(tz=timezone.utc)
        payload = {
            "iss": self._settings.jitsi_app_id,
            "sub": self._settings.jitsi_base_url,
            "aud": "jitsi",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=duration)).timestamp()),
            "room": room_name,
            "moderator": is_moderator,
            "context": {
                "user": {"id": user_id, "name": user_name},
            },
        }
        return jwt.encode(payload, self._settings.jitsi_app_secret, algorithm="HS256")

    def get_room_url(self, room_name: str, jwt_token: str) -> str:
        base = self._settings.jitsi_base_url.rstrip("/")
        return f"{base}/{room_name}?jwt={jwt_token}"

    @staticmethod
    def build_room_name(tenant_slug: str, correlation_id_str: str) -> str:
        short_id = correlation_id_str.replace("-", "")[:8]
        return f"ic_{tenant_slug}_{short_id}"
