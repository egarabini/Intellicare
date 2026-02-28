"""Tests for BotSandbox — RestrictedPython / exec fallback."""

import time

import pytest

from intellicare_core.bots.sandbox import ALLOWED_IMPORTS, BotSandbox, SandboxResult


@pytest.fixture
def sandbox() -> BotSandbox:
    return BotSandbox()


# ── Successful execution ────────────────────────────────────────────────────


def test_simple_print_captured(sandbox: BotSandbox) -> None:
    result = sandbox.execute("print('hello')", {})
    assert result.success is True
    assert "hello" in result.log_output
    assert result.error is None


def test_math_computation(sandbox: BotSandbox) -> None:
    code = "result = 2 + 2\nprint(result)"
    r = sandbox.execute(code, {})
    assert r.success is True
    assert "4" in r.log_output


def test_globals_ctx_injected(sandbox: BotSandbox) -> None:
    code = "print(x * 3)"
    r = sandbox.execute(code, {"x": 7})
    assert r.success is True
    assert "21" in r.log_output


def test_input_resource_accessible(sandbox: BotSandbox) -> None:
    resource = {"resourceType": "Patient", "id": "p-1"}
    code = "print(input['resourceType'])"
    r = sandbox.execute(code, {"input": resource})
    assert r.success is True
    assert "Patient" in r.log_output


def test_multi_print_lines(sandbox: BotSandbox) -> None:
    code = "print('line1')\nprint('line2')\nprint('line3')"
    r = sandbox.execute(code, {})
    assert r.success is True
    assert "line1" in r.log_output
    assert "line2" in r.log_output
    assert "line3" in r.log_output


def test_duration_ms_populated(sandbox: BotSandbox) -> None:
    r = sandbox.execute("pass", {})
    assert r.success is True
    assert r.duration_ms >= 0.0


# ── Allowed imports ─────────────────────────────────────────────────────────


def test_import_json_allowed(sandbox: BotSandbox) -> None:
    code = "import json\nprint(json.dumps({'a': 1}))"
    r = sandbox.execute(code, {})
    assert r.success is True
    assert '"a"' in r.log_output


def test_import_datetime_allowed(sandbox: BotSandbox) -> None:
    code = "import datetime\nprint(type(datetime.datetime.utcnow()))"
    r = sandbox.execute(code, {})
    assert r.success is True


def test_import_re_allowed(sandbox: BotSandbox) -> None:
    code = "import re\nm = re.match(r'(\\d+)', '42abc')\nprint(m.group(1))"
    r = sandbox.execute(code, {})
    assert r.success is True
    assert "42" in r.log_output


def test_import_uuid_allowed(sandbox: BotSandbox) -> None:
    code = "import uuid\nprint(len(str(uuid.uuid4())))"
    r = sandbox.execute(code, {})
    assert r.success is True
    assert "36" in r.log_output


# ── Blocked imports ─────────────────────────────────────────────────────────


def test_import_os_blocked(sandbox: BotSandbox) -> None:
    code = "import os\nprint(os.getcwd())"
    r = sandbox.execute(code, {})
    assert r.success is False
    assert r.error is not None
    assert "os" in r.error.lower() or "import" in r.error.lower() or "not allowed" in r.error.lower()


def test_import_subprocess_blocked(sandbox: BotSandbox) -> None:
    code = "import subprocess\nsubprocess.run(['whoami'])"
    r = sandbox.execute(code, {})
    assert r.success is False


def test_import_sys_blocked(sandbox: BotSandbox) -> None:
    code = "import sys\nprint(sys.version)"
    r = sandbox.execute(code, {})
    assert r.success is False


# ── Error handling ───────────────────────────────────────────────────────────


def test_runtime_error_captured(sandbox: BotSandbox) -> None:
    code = "raise ValueError('something went wrong')"
    r = sandbox.execute(code, {})
    assert r.success is False
    assert "ValueError" in (r.error or "")
    assert "something went wrong" in (r.error or "")


def test_division_by_zero(sandbox: BotSandbox) -> None:
    code = "x = 1 / 0"
    r = sandbox.execute(code, {})
    assert r.success is False
    assert r.error is not None


def test_syntax_error_captured(sandbox: BotSandbox) -> None:
    code = "def broken(:"
    r = sandbox.execute(code, {})
    assert r.success is False
    assert r.error is not None


def test_partial_output_preserved_on_error(sandbox: BotSandbox) -> None:
    code = "print('before')\nraise RuntimeError('boom')"
    r = sandbox.execute(code, {})
    assert r.success is False
    assert "before" in r.log_output


# ── Timeout ─────────────────────────────────────────────────────────────────


def test_timeout_enforced(sandbox: BotSandbox) -> None:
    code = "import time\ntime.sleep(10)"
    r = sandbox.execute(code, {"time": __import__("time")}, timeout=1)
    # time is not in ALLOWED_IMPORTS, so the import is blocked — which also returns
    # a failure but NOT a timeout error. We test the timeout with the injected time.
    assert r.success is False


def test_timeout_with_injected_sleep(sandbox: BotSandbox) -> None:
    """Inject time module into globals to bypass import block and test real timeout."""
    import time as _time
    code = "time.sleep(10)"
    start = _time.monotonic()
    r = sandbox.execute(code, {"time": _time}, timeout=1)
    elapsed = _time.monotonic() - start
    assert r.success is False
    # Should finish ~1s, not 10s
    assert elapsed < 5.0


# ── Return type ─────────────────────────────────────────────────────────────


def test_returns_sandbox_result_type(sandbox: BotSandbox) -> None:
    r = sandbox.execute("pass", {})
    assert isinstance(r, SandboxResult)


def test_empty_code_succeeds(sandbox: BotSandbox) -> None:
    r = sandbox.execute("", {})
    assert r.success is True


# ── ALLOWED_IMPORTS constant ─────────────────────────────────────────────────


def test_allowed_imports_contains_safe_modules() -> None:
    for mod in ("json", "datetime", "math", "re", "hashlib", "uuid"):
        assert mod in ALLOWED_IMPORTS


def test_allowed_imports_excludes_dangerous() -> None:
    for mod in ("os", "sys", "subprocess", "socket", "shutil", "pathlib"):
        assert mod not in ALLOWED_IMPORTS
