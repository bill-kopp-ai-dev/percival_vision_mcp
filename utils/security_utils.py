from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import Lock
from typing import Any
import re


_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_BEARER_TOKEN_RE = re.compile(r"(?i)\b(bearer\s+)([a-z0-9._\-~+/]+=*)")
_ASSIGNMENT_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*([^\s,;]+)"
)
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9]{10,}\b")

_PROMPT_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "override_instructions",
        re.compile(
            r"(?is)\b(ignore|disregard|forget|override|ignora(?:r)?|olvida(?:r)?|desconsidere|desconsidera(?:r)?)\b"
            r".{0,120}\b(previous|prior|above|all|anterior(?:es)?|previa(?:s)?|previo(?:s)?)\b"
            r".{0,120}\b(instruction|instructions|prompt|message|messages|instruccion(?:es)?|instru[cç][aã]o(?:es)?|mensaj(?:e|es)|mensag(?:em|ens))\b"
        ),
        "[redacted:override_instructions]",
    ),
    (
        "override_instructions_obfuscated",
        re.compile(
            r"(?is)\bi\W*g\W*n\W*o\W*r\W*e\W+.{0,80}\b(previous|prior|above|all)\b.{0,80}\b"
            r"(instruction|instructions|prompt|message|messages)\b"
        ),
        "[redacted:override_instructions_obfuscated]",
    ),
    (
        "system_prompt_reference",
        re.compile(
            r"(?is)\b(system prompt|developer message|hidden prompt|prompt oculto|mensaje de desarrollador|mensagem de desenvolvedor)\b"
        ),
        "[redacted:system_prompt_reference]",
    ),
    (
        "override_rules_instruction",
        re.compile(r"(?is)\boverride\b.{0,40}\b(all|any)\b.{0,40}\b(rule|rules|policy|policies)\b"),
        "[redacted:override_rules_instruction]",
    ),
    (
        "tool_invocation_instruction",
        re.compile(
            r"(?is)\b(call|invoke|use|execute|run|utilize|ejecuta|usa|utiliza)\b.{0,80}\b"
            r"(tool|function|capability|ferramenta|funcion|herramienta)\b"
        ),
        "[redacted:tool_invocation_instruction]",
    ),
    (
        "role_tag_injection",
        re.compile(r"(?is)<\s*/?\s*(system|assistant|developer|tool)\s*>"),
        "[redacted:role_tag]",
    ),
    (
        "secret_exfiltration_instruction",
        re.compile(
            r"(?is)\b(exfiltrate|leak|dump|print|reveal|show|expose|vaza(?:r)?|muestra|mostrar|revela(?:r)?)\b"
            r".{0,120}\b(secret|credential|token|api key|password|internal config|hidden directive|system prompt)\b"
        ),
        "[redacted:secret_exfiltration_instruction]",
    ),
    (
        "policy_override_instruction",
        re.compile(
            r"(?is)\b(new policy|prioritize this message|higher priority)\b.{0,100}\b(over|above|instead of)\b.{0,80}\b(previous|prior)\b"
        ),
        "[redacted:policy_override_instruction]",
    ),
)

_SECURITY_LOCK = Lock()
_SECURITY_COUNTERS: Counter[str] = Counter()
_RECENT_SECURITY_EVENTS: deque[dict[str, Any]] = deque(maxlen=100)
_LAST_AUDIT_WRITE_ERROR: str | None = None
_LAST_AUDIT_WRITE_AT: str | None = None


def _env_bool(var_name: str, default: bool) -> bool:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _env_int(var_name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except Exception:
        return default
    return max(minimum, value)


def _audit_enabled() -> bool:
    return _env_bool("PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT", False)


def _audit_log_path() -> Path:
    raw = os.getenv("PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.cwd() / ".percival_vision_security_audit.jsonl"


def _audit_max_bytes() -> int:
    return _env_int("PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES", 5 * 1024 * 1024)


def _audit_state_snapshot() -> dict[str, Any]:
    with _SECURITY_LOCK:
        last_error = _LAST_AUDIT_WRITE_ERROR
        last_write_at = _LAST_AUDIT_WRITE_AT
    return {
        "enabled": _audit_enabled(),
        "path": str(_audit_log_path()),
        "max_bytes": _audit_max_bytes(),
        "last_write_at": last_write_at,
        "last_error": last_error,
    }


def _set_audit_write_state(*, error: str | None = None, wrote: bool = False) -> None:
    global _LAST_AUDIT_WRITE_ERROR, _LAST_AUDIT_WRITE_AT
    with _SECURITY_LOCK:
        if wrote:
            _LAST_AUDIT_WRITE_ERROR = None
            _LAST_AUDIT_WRITE_AT = _utc_now_iso()
        if error is not None:
            _LAST_AUDIT_WRITE_ERROR = redact_sensitive_text(error, max_len=400)
            _SECURITY_COUNTERS["audit_log_write_failed"] += 1


def _rotate_audit_log_if_needed(path: Path, max_bytes: int) -> None:
    if not path.exists():
        return
    size = path.stat().st_size
    if size < max_bytes:
        return
    backup = path.with_suffix(path.suffix + ".1")
    if backup.exists():
        backup.unlink()
    path.replace(backup)


def _append_persistent_audit_record(record: dict[str, Any]) -> None:
    if not _audit_enabled():
        return
    try:
        path = _audit_log_path()
        max_bytes = _audit_max_bytes()
        path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_audit_log_if_needed(path, max_bytes)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        _set_audit_write_state(wrote=True)
    except Exception as exc:
        _set_audit_write_state(error=str(exc))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_detail_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value, max_len=600)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


def record_security_event(event: str, details: dict[str, Any] | None = None) -> None:
    event_name = (event or "").strip() or "unknown_event"
    record: dict[str, Any] = {}
    with _SECURITY_LOCK:
        _SECURITY_COUNTERS[event_name] += 1
        record = {
            "event": event_name,
            "timestamp": _utc_now_iso(),
            "details": {k: _safe_detail_value(v) for k, v in (details or {}).items()},
        }
        _RECENT_SECURITY_EVENTS.append(record)
    _append_persistent_audit_record(record)


def get_security_metrics_snapshot() -> dict[str, Any]:
    with _SECURITY_LOCK:
        counters = dict(_SECURITY_COUNTERS)
        recent = list(_RECENT_SECURITY_EVENTS)
    return {
        "counters": counters,
        "recent_events": recent,
        "total_events": int(sum(counters.values())),
        "audit": _audit_state_snapshot(),
    }


def clear_security_metrics() -> dict[str, int]:
    with _SECURITY_LOCK:
        counters_total = int(sum(_SECURITY_COUNTERS.values()))
        events_total = len(_RECENT_SECURITY_EVENTS)
        _SECURITY_COUNTERS.clear()
        _RECENT_SECURITY_EVENTS.clear()
    return {
        "cleared_counters_total": counters_total,
        "cleared_recent_events_total": events_total,
    }


def reset_security_metrics_for_tests() -> None:
    global _LAST_AUDIT_WRITE_ERROR, _LAST_AUDIT_WRITE_AT
    with _SECURITY_LOCK:
        _SECURITY_COUNTERS.clear()
        _RECENT_SECURITY_EVENTS.clear()
        _LAST_AUDIT_WRITE_ERROR = None
        _LAST_AUDIT_WRITE_AT = None


def redact_sensitive_text(text: str, max_len: int = 1200) -> str:
    value = _CONTROL_CHAR_RE.sub(" ", str(text))
    value = _BEARER_TOKEN_RE.sub(r"\1[REDACTED]", value)
    value = _ASSIGNMENT_SECRET_RE.sub(r"\1=[REDACTED]", value)
    value = _OPENAI_KEY_RE.sub("[REDACTED_OPENAI_KEY]", value)
    if len(value) > max_len:
        return value[:max_len] + "...[truncated]"
    return value


def redact_sensitive_structure(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: redact_sensitive_structure(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_sensitive_structure(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_structure(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def sanitize_untrusted_text(text: str, max_len: int = 8000) -> dict[str, Any]:
    original = str(text)
    sanitized = _CONTROL_CHAR_RE.sub(" ", original)
    findings: list[str] = []

    for finding_name, pattern, replacement in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(sanitized):
            findings.append(finding_name)
            sanitized = pattern.sub(replacement, sanitized)

    truncated = False
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len] + "...[truncated]"
        truncated = True

    return {
        "text": sanitized,
        "findings": sorted(set(findings)),
        "truncated": truncated,
        "modified": sanitized != original,
    }
