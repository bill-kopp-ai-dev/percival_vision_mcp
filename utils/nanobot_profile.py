from __future__ import annotations

from typing import Any


SERVER_NAME = "percival-vision-mcp"
CONTRACT_VERSION = "2026-03-s9"


def build_nanobot_profile() -> dict[str, Any]:
    """
    Return a compact machine-readable profile for nanobot orchestration.
    """
    return {
        "server": SERVER_NAME,
        "contract_version": CONTRACT_VERSION,
        "response_contract": {
            "success": {"ok": True, "data": {}, "meta": {}, "legacy_text": "optional"},
            "error": {
                "ok": False,
                "error": "message",
                "code": "error_code",
                "details": {},
                "meta": {},
                "legacy_text": "optional",
            },
            "notes": [
                "legacy_text is compatibility-only and may be omitted in future major versions.",
                "Agents should rely on structured fields (ok/data/error/code/details/meta).",
                "Vision model output is treated as untrusted data and may be sanitized.",
                "working_dir is optional for compatibility; when omitted the server derives it safely.",
                "rollout mode controls when missing working_dir becomes a hard error.",
                "security metrics details are hidden by default and clear operation is policy-gated.",
            ],
        },
        "recommended_workflows": {
            "vision_analysis": [
                "list_available_vision_models()",
                "describe_image(working_dir=..., image_path=...) or analyze_image(...)",
                "identify_objects(...) or read_text(...) when needed",
                "get_rollout_status() [optional for deployment checks]",
                "get_access_policy_status() [optional for access-control checks]",
                "get_security_posture() [optional for runtime policy checks]",
                "get_security_metrics() [optional for incident/debug]",
            ]
        },
        "recommended_enabled_tools": [
            "list_available_vision_models",
            "analyze_image",
            "describe_image",
            "identify_objects",
            "read_text",
            "get_nanobot_profile",
            "get_security_metrics",
            "clear_security_metrics",
            "get_security_posture",
            "get_rollout_status",
            "get_access_policy_status",
        ],
        "defaults": {
            "provider_model_cache_ttl_seconds": 300,
            "default_max_tokens": 1000,
            "default_model_env": "PERCIVAL_DEFAULT_MODEL",
            "provider_base_url_env": "PERCIVAL_BASE_URL",
            "provider_api_key_env_candidates": [
                "PERCIVAL_API_KEY",
                "JARVINA_API_KEY",
                "VENICE_API_KEY",
                "OPENAI_API_KEY",
            ],
            "max_output_chars_env": "PERCIVAL_VISION_MCP_MAX_OUTPUT_CHARS",
            "max_image_bytes_env": "PERCIVAL_VISION_MCP_MAX_IMAGE_BYTES",
            "max_image_pixels_env": "PERCIVAL_VISION_MCP_MAX_IMAGE_PIXELS",
            "allowed_image_mime_types_env": "PERCIVAL_VISION_MCP_ALLOWED_IMAGE_MIME_TYPES",
            "allow_insecure_provider_url_env": "PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL",
            "allow_private_provider_url_env": "PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL",
            "allowed_provider_hosts_env": "PERCIVAL_VISION_MCP_ALLOWED_PROVIDER_HOSTS",
            "allow_unauthenticated_loopback_http_env": "PERCIVAL_VISION_MCP_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP",
            "allow_security_metrics_clear_env": "PERCIVAL_VISION_MCP_ALLOW_SECURITY_METRICS_CLEAR",
            "expose_security_event_details_env": "PERCIVAL_VISION_MCP_EXPOSE_SECURITY_EVENT_DETAILS",
            "disable_system_guardrail_env": "PERCIVAL_VISION_MCP_DISABLE_SYSTEM_GUARDRAIL",
            "system_guardrail_prompt_env": "PERCIVAL_VISION_MCP_SYSTEM_GUARDRAIL_PROMPT",
            "enable_persistent_security_audit_env": "PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT",
            "security_audit_log_path_env": "PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH",
            "security_audit_max_bytes_env": "PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES",
            "enabled_tools_env": "PERCIVAL_VISION_MCP_ENABLED_TOOLS",
            "disabled_tools_env": "PERCIVAL_VISION_MCP_DISABLED_TOOLS",
            "always_allowed_tools_env": "PERCIVAL_VISION_MCP_ALWAYS_ALLOWED_TOOLS",
            "allowed_roots_env": "PERCIVAL_VISION_MCP_ALLOWED_ROOTS",
            "disable_root_sandbox_env": "PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX",
            "working_dir_mode_env": "PERCIVAL_VISION_MCP_WORKING_DIR_MODE",
            "strict_working_dir_date_env": "PERCIVAL_VISION_MCP_STRICT_WORKING_DIR_DATE",
        },
    }
