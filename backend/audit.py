"""Append-only audit trail of agent-loop activity: output/audit_trail.json (Problem 12).

The file is one valid JSON array. New entries are appended in place: we only
replace the closing "]" at the very end, so earlier entries are never rewritten and
the file is never wiped between runs or server restarts.

Events (all have "time" in UTC ISO-8601, "run_id", "event"):
  run_start    channel, shopper ("guest" or "user:<id>"), page, message (short, redacted), history_turns
  tool_call    tool, args (short)
  tool_result  tool, result (one-line summary), ms
  tool_error   tool, error, ms
  run_end      stop_reason, model_finish_reason, requests, tool_calls, input_tokens, output_tokens,
               cards, reply (short, redacted), ms

Privacy: emails and long digit runs (card/phone numbers) are masked, and texts are cut
to a short length. Shoppers are identified by user id only, never by name or email.
"""

import functools
import inspect
import json
import re
import threading
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 160
NL = b"\n"  # written in binary so Windows doesn't turn it into \r\n

_lock = threading.Lock()
current_run: ContextVar[str | None] = ContextVar("current_run", default=None)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_LONG_DIGITS = re.compile(r"(?:\d[ -]?){7,}")


def redact(text: str) -> str:
    return _LONG_DIGITS.sub("[number]", _EMAIL.sub("[email]", text))


def short(value: Any, limit: int = MAX_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    text = redact(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _append(entry: dict) -> None:
    line = json.dumps(entry, ensure_ascii=False).encode("utf-8")
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_bytes(b"[" + NL + line + NL + b"]" + NL)
            return
        with open(AUDIT_PATH, "r+b") as f:
            # walk back to the closing "]" (only whitespace may follow it)
            f.seek(0, 2)
            pos = f.tell()
            while pos > 0:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch == b"]":
                    break
                if not ch.isspace():
                    raise ValueError("audit_trail.json does not end with ']'; refusing to modify it")
            # the last real character before "]" tells us if the array is empty ("[") or not
            back = pos
            prev = b"["
            while back > 0:
                back -= 1
                f.seek(back)
                c = f.read(1)
                if not c.isspace():
                    prev = c
                    break
            sep = NL if prev == b"[" else b"," + NL
            # overwrite only the closing bracket; every earlier byte stays exactly as it was
            f.seek(pos)
            f.truncate()
            f.write(sep + line + NL + b"]" + NL)


def record(event: str, **fields: Any) -> None:
    """Append one event. Never raises, so a logging problem can't break a shopper's chat."""
    entry = {"time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "run_id": current_run.get(), "event": event}
    entry.update(fields)
    try:
        _append(entry)
    except Exception:  # pragma: no cover - logging must never take the shop down
        pass


def start_run() -> str:
    run_id = uuid.uuid4().hex[:12]
    current_run.set(run_id)
    return run_id


# ---------- tool wrapper ----------

def _summary(result: Any) -> str:
    """One readable line per tool result (full results would bloat the log)."""
    name = type(result).__name__
    if name == "SearchResults":
        top = ", ".join(p.name for p in result.products[:3])
        extra = f"; ignored {result.ignored_terms}" if result.ignored_terms else ""
        return short(f"{result.total_matches} matches (returned {result.returned}): {top}{extra}")
    if name == "ProductDetails":
        stock = " ".join(f"{s.size}={s.quantity}" for s in result.sizes)
        return short(f"{result.name} ${result.price_usd:g} | {stock}")
    if name == "StockCheck":
        return short(f"{result.name} size {result.size}: qty {result.quantity} ({result.status}), ${result.price_usd:g}")
    if name in ("ProductNotFound", "InvalidSize"):
        return short(result.model_dump())
    if name == "ShopperContext":
        return short(f"logged_in={result.logged_in}, viewing={result.viewing_product_id}")
    if isinstance(result, list):
        return short(f"{len(result)} items: " + ", ".join(getattr(r, "name", str(r)) for r in result[:6]))
    return short(getattr(result, "model_dump", lambda: result)())


def audited(fn):
    """Log every call of an agent tool (args + summarized result + timing) to the audit trail."""
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        call_args = {k: v for k, v in bound.arguments.items() if k != "ctx" and v is not None}
        record("tool_call", tool=fn.__name__, args=short(call_args))
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            record("tool_error", tool=fn.__name__, error=short(repr(e)), ms=round((time.perf_counter() - t0) * 1000))
            raise
        record("tool_result", tool=fn.__name__, result=_summary(result), ms=round((time.perf_counter() - t0) * 1000))
        return result

    return wrapper
