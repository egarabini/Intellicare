"""BotSandbox — executes Python code in a restricted environment.

Primary:  RestrictedPython (if installed)
Fallback: stdlib exec() with threading timeout (development only)

RestrictedPython prevents:
  - Access to __builtins__.__import__ beyond the allowlist
  - Access to private attributes (_ prefixed)
  - Attribute write on protected objects
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Optional

ALLOWED_IMPORTS = frozenset(
    {
        "json",
        "datetime",
        "math",
        "re",
        "hashlib",
        "collections",
        "itertools",
        "functools",
        "typing",
        "uuid",
        "decimal",
        "string",
        "textwrap",
    }
)


@dataclass
class SandboxResult:
    success: bool
    log_output: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class _BotLogCapture:
    lines: list[str] = field(default_factory=list)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.lines.append(" ".join(str(a) for a in args))

    def getvalue(self) -> str:
        return "\n".join(self.lines)


def _restricted_import(name: str, *args: Any, **kwargs: Any) -> Any:
    """Allow only safelisted imports inside bot code."""
    if name not in ALLOWED_IMPORTS:
        raise ImportError(f"Import of '{name}' is not allowed in bot sandbox")
    return __import__(name, *args, **kwargs)


class BotSandbox:
    """Execute bot Python code in a sandboxed environment."""

    def execute(
        self,
        code: str,
        globals_ctx: dict[str, Any],
        timeout: int = 30,
    ) -> SandboxResult:
        """Run *code* with *globals_ctx* and enforce *timeout* seconds."""
        import time

        log = _BotLogCapture()
        start = time.monotonic()
        result_container: list[SandboxResult] = []

        def _run() -> None:
            try:
                _execute_code(code, globals_ctx, log)
                elapsed = (time.monotonic() - start) * 1000
                result_container.append(
                    SandboxResult(success=True, log_output=log.getvalue(), duration_ms=elapsed)
                )
            except Exception as exc:
                elapsed = (time.monotonic() - start) * 1000
                result_container.append(
                    SandboxResult(
                        success=False,
                        log_output=log.getvalue(),
                        error=f"{type(exc).__name__}: {exc}",
                        duration_ms=elapsed,
                    )
                )

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            elapsed = (time.monotonic() - start) * 1000
            return SandboxResult(
                success=False,
                log_output=log.getvalue(),
                error=f"Bot execution timed out after {timeout}s",
                duration_ms=elapsed,
            )

        return result_container[0] if result_container else SandboxResult(
            success=False, error="No result — execution thread did not complete"
        )


def _execute_code(code: str, globals_ctx: dict[str, Any], log: _BotLogCapture) -> None:
    """Try RestrictedPython first, fall back to plain exec."""
    try:
        from RestrictedPython import (  # type: ignore[import]
            compile_restricted,
            safe_builtins,
            safe_globals,
        )

        compiled = compile_restricted(code, "<bot>", "exec")
        restricted_globals: dict[str, Any] = {
            **safe_globals,
            "__builtins__": {**safe_builtins, "__import__": _restricted_import},
            "print": log,
        }
        restricted_globals.update(globals_ctx)
        exec(compiled, restricted_globals)  # noqa: S102

    except ImportError:
        # RestrictedPython not installed — plain exec with print capture (dev only)
        _builtins_base = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)  # type: ignore[arg-type]
        plain_globals: dict[str, Any] = {
            "__builtins__": {**_builtins_base, "__import__": _restricted_import},
            "print": log,
        }
        plain_globals.update(globals_ctx)
        exec(code, plain_globals)  # noqa: S102
