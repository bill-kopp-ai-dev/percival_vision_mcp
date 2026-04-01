from __future__ import annotations

import inspect
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from utils.nanobot_profile import CONTRACT_VERSION, SERVER_NAME


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_request_id(prefix: str = "vision") -> str:
    return f"{prefix}-{int(time.time() * 1000)}-{uuid4().hex[:12]}"


def json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def success_response(
    data: dict[str, Any],
    *,
    legacy_text: Optional[str] = None,
    request_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> str:
    effective_request_id = request_id or new_request_id()
    frame = inspect.currentframe()
    caller_name = frame.f_back.f_code.co_name if frame and frame.f_back else "unknown_tool"
    effective_tool_name = tool_name or caller_name
    payload: dict[str, Any] = {
        "ok": True,
        "data": data,
        "request_id": effective_request_id,
        "meta": {
            "server": SERVER_NAME,
            "contract_version": CONTRACT_VERSION,
            "request_id": effective_request_id,
            "timestamp": utc_now_iso(),
            "tool": effective_tool_name,
        },
    }
    if legacy_text:
        payload["legacy_text"] = legacy_text
    return json_response(payload)


def error_response(
    error: str,
    *,
    code: str = "tool_error",
    details: Optional[dict[str, Any]] = None,
    legacy_text: Optional[str] = None,
    request_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> str:
    effective_request_id = request_id or new_request_id()
    frame = inspect.currentframe()
    caller_name = frame.f_back.f_code.co_name if frame and frame.f_back else "unknown_tool"
    effective_tool_name = tool_name or caller_name
    payload: dict[str, Any] = {
        "ok": False,
        "error": str(error),
        "code": code,
        "request_id": effective_request_id,
        "meta": {
            "server": SERVER_NAME,
            "contract_version": CONTRACT_VERSION,
            "request_id": effective_request_id,
            "timestamp": utc_now_iso(),
            "tool": effective_tool_name,
        },
    }
    if details is not None:
        payload["details"] = details
    if legacy_text:
        payload["legacy_text"] = legacy_text
    return json_response(payload)
