"""Pseudonimizacao LGPD."""

from __future__ import annotations

import hashlib


def hash_patient_id(patient_id: str, salt: str) -> str:
    data = f"{patient_id}:{salt}".encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"

