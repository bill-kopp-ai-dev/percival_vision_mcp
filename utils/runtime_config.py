from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


DEFAULT_PROVIDER_BASE_URL = "https://api.openai.com/v1"
DEFAULT_PROVIDER_MODEL = "qwen-2.5-vl"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 120
DEFAULT_PROVIDER_MAX_TOKENS = 1000
DEFAULT_PROVIDER_MODEL_CACHE_TTL_SECONDS = 300

DEFAULT_RUNTIME_MODE = "stdio"
DEFAULT_RUNTIME_HOST = "127.0.0.1"
DEFAULT_RUNTIME_PORT = 8001
DEFAULT_RUNTIME_LOG_LEVEL = "INFO"
DEFAULT_RUNTIME_MOUNT_PATH = "/"
DEFAULT_RUNTIME_AUTH_TOKEN_ENV = "PERCIVAL_VISION_MCP_AUTH_TOKEN"
DEFAULT_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP = False
SUPPORTED_RUNTIME_MODES = {"stdio", "sse", "streamable-http"}
SUPPORTED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
DEFAULT_WORKING_DIR_MODE = "compat"
SUPPORTED_WORKING_DIR_MODES = {"compat", "strict"}
DEFAULT_EMIT_COMPAT_WARNINGS = True
DEFAULT_WORKING_DIR_STRICT_DATE = "2026-06-30"
DEFAULT_ROLLOUT_TRACK = "stable"

PROVIDER_BASE_URL_ENV_CANDIDATES = (
    "PERCIVAL_BASE_URL",
    "JARVINA_BASE_URL",
)
PROVIDER_API_KEY_ENV_CANDIDATES = (
    "PERCIVAL_API_KEY",
    "JARVINA_API_KEY",
    "VENICE_API_KEY",
    "OPENAI_API_KEY",
)
PROVIDER_MODEL_ENV_CANDIDATES = (
    "PERCIVAL_DEFAULT_MODEL",
    "JARVINA_VISION_MODEL",
)


def env_bool(var_name: str, default: bool) -> bool:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def env_int(var_name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except Exception:
        return default
    return max(minimum, value)


def _first_env(candidates: tuple[str, ...]) -> tuple[Optional[str], Optional[str]]:
    for name in candidates:
        value = os.getenv(name)
        if value is None:
            continue
        normalized = value.strip()
        if normalized:
            return normalized, name
    return None, None


@dataclass(frozen=True)
class ProviderRuntimeConfig:
    base_url: str
    api_key: Optional[str]
    api_key_env: Optional[str]
    default_model: str
    timeout_seconds: int
    default_max_tokens: int
    model_cache_ttl_seconds: int


def load_provider_runtime_config() -> ProviderRuntimeConfig:
    base_url, _ = _first_env(PROVIDER_BASE_URL_ENV_CANDIDATES)
    api_key, api_key_env = _first_env(PROVIDER_API_KEY_ENV_CANDIDATES)
    default_model, _ = _first_env(PROVIDER_MODEL_ENV_CANDIDATES)

    return ProviderRuntimeConfig(
        base_url=base_url or DEFAULT_PROVIDER_BASE_URL,
        api_key=api_key,
        api_key_env=api_key_env,
        default_model=default_model or DEFAULT_PROVIDER_MODEL,
        timeout_seconds=env_int("PERCIVAL_TIMEOUT", DEFAULT_PROVIDER_TIMEOUT_SECONDS),
        default_max_tokens=env_int("PERCIVAL_VISION_MCP_MAX_TOKENS", DEFAULT_PROVIDER_MAX_TOKENS),
        model_cache_ttl_seconds=env_int(
            "PERCIVAL_VISION_MCP_MODEL_CACHE_TTL",
            DEFAULT_PROVIDER_MODEL_CACHE_TTL_SECONDS,
        ),
    )


@dataclass(frozen=True)
class HttpRuntimeConfig:
    mode: str
    host: str
    port: int
    log_level: str
    mount_path: str
    json_response: bool
    stateless_http: bool
    allow_remote_http: bool
    allow_unauthenticated_loopback_http: bool
    auth_token_env: str
    auth_token: Optional[str]


@dataclass(frozen=True)
class RolloutConfig:
    working_dir_mode: str
    emit_compat_warnings: bool
    strict_working_dir_date: str
    rollout_track: str


def load_http_runtime_config() -> HttpRuntimeConfig:
    auth_token_env = (
        os.getenv("PERCIVAL_VISION_MCP_AUTH_TOKEN_ENV", DEFAULT_RUNTIME_AUTH_TOKEN_ENV).strip()
        or DEFAULT_RUNTIME_AUTH_TOKEN_ENV
    )
    auth_token_raw = os.getenv(auth_token_env, "").strip()
    auth_token = auth_token_raw or None
    raw_mode = os.getenv("PERCIVAL_VISION_MCP_MODE", DEFAULT_RUNTIME_MODE).strip().lower() or DEFAULT_RUNTIME_MODE
    mode = raw_mode if raw_mode in SUPPORTED_RUNTIME_MODES else DEFAULT_RUNTIME_MODE
    raw_log_level = os.getenv("PERCIVAL_VISION_MCP_LOG_LEVEL", DEFAULT_RUNTIME_LOG_LEVEL).strip().upper()
    log_level = raw_log_level if raw_log_level in SUPPORTED_LOG_LEVELS else DEFAULT_RUNTIME_LOG_LEVEL

    return HttpRuntimeConfig(
        mode=mode,
        host=os.getenv("PERCIVAL_VISION_MCP_HOST", DEFAULT_RUNTIME_HOST).strip() or DEFAULT_RUNTIME_HOST,
        port=env_int("PERCIVAL_VISION_MCP_PORT", DEFAULT_RUNTIME_PORT),
        log_level=log_level,
        mount_path=os.getenv("PERCIVAL_VISION_MCP_MOUNT_PATH", DEFAULT_RUNTIME_MOUNT_PATH) or DEFAULT_RUNTIME_MOUNT_PATH,
        json_response=env_bool("PERCIVAL_VISION_MCP_JSON_RESPONSE", False),
        stateless_http=env_bool("PERCIVAL_VISION_MCP_STATELESS_HTTP", False),
        allow_remote_http=env_bool("PERCIVAL_VISION_MCP_ALLOW_REMOTE_HTTP", False),
        allow_unauthenticated_loopback_http=env_bool(
            "PERCIVAL_VISION_MCP_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP",
            DEFAULT_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP,
        ),
        auth_token_env=auth_token_env,
        auth_token=auth_token,
    )


def load_rollout_config() -> RolloutConfig:
    raw_working_dir_mode = (
        os.getenv("PERCIVAL_VISION_MCP_WORKING_DIR_MODE", DEFAULT_WORKING_DIR_MODE).strip().lower()
        or DEFAULT_WORKING_DIR_MODE
    )
    working_dir_mode = (
        raw_working_dir_mode
        if raw_working_dir_mode in SUPPORTED_WORKING_DIR_MODES
        else DEFAULT_WORKING_DIR_MODE
    )
    strict_working_dir_date = (
        os.getenv("PERCIVAL_VISION_MCP_STRICT_WORKING_DIR_DATE", DEFAULT_WORKING_DIR_STRICT_DATE).strip()
        or DEFAULT_WORKING_DIR_STRICT_DATE
    )
    rollout_track = os.getenv("PERCIVAL_VISION_MCP_ROLLOUT_TRACK", DEFAULT_ROLLOUT_TRACK).strip() or DEFAULT_ROLLOUT_TRACK
    return RolloutConfig(
        working_dir_mode=working_dir_mode,
        emit_compat_warnings=env_bool("PERCIVAL_VISION_MCP_EMIT_COMPAT_WARNINGS", DEFAULT_EMIT_COMPAT_WARNINGS),
        strict_working_dir_date=strict_working_dir_date,
        rollout_track=rollout_track,
    )
