from __future__ import annotations

import os
from typing import Optional


DEFAULT_ALWAYS_ALLOWED_TOOLS = {
    "get_access_policy_status",
    "get_security_posture",
    "get_rollout_status",
    "get_nanobot_profile",
}


def _csv_to_set(var_name: str) -> set[str]:
    raw = os.getenv(var_name, "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _normalize_tool_name(tool_name: str) -> str:
    return (tool_name or "").strip().lower()


def get_tool_access_policy_snapshot() -> dict[str, object]:
    enabled_tools = _csv_to_set("PERCIVAL_VISION_MCP_ENABLED_TOOLS")
    disabled_tools = _csv_to_set("PERCIVAL_VISION_MCP_DISABLED_TOOLS")
    configured_always_allowed = _csv_to_set("PERCIVAL_VISION_MCP_ALWAYS_ALLOWED_TOOLS")
    always_allowed = set(DEFAULT_ALWAYS_ALLOWED_TOOLS) | configured_always_allowed
    return {
        "enabled_tools": sorted(enabled_tools),
        "disabled_tools": sorted(disabled_tools),
        "always_allowed_tools": sorted(always_allowed),
        "enabled_env": "PERCIVAL_VISION_MCP_ENABLED_TOOLS",
        "disabled_env": "PERCIVAL_VISION_MCP_DISABLED_TOOLS",
        "always_allowed_env": "PERCIVAL_VISION_MCP_ALWAYS_ALLOWED_TOOLS",
    }


def check_tool_access(tool_name: str) -> tuple[bool, Optional[str]]:
    normalized_tool = _normalize_tool_name(tool_name)
    policy = get_tool_access_policy_snapshot()

    always_allowed = set(policy["always_allowed_tools"])
    if normalized_tool in always_allowed:
        return True, None

    enabled_tools = set(policy["enabled_tools"])
    disabled_tools = set(policy["disabled_tools"])

    if enabled_tools and normalized_tool not in enabled_tools:
        return False, "not_in_enabled_tools_allowlist"
    if normalized_tool in disabled_tools:
        return False, "explicitly_disabled"
    return True, None
