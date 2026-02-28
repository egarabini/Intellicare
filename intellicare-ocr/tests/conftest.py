from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ocr.storage.chroma_store import get_chroma_store


@pytest.fixture(autouse=True)
def _reset_inmemory_stores() -> None:
    get_chroma_store().clear()
