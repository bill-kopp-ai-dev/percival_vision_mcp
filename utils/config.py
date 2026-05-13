from __future__ import annotations

import os
from pathlib import Path

def env_bool(var_name: str, default: bool = False) -> bool:
    val = os.getenv(var_name, "").lower().strip()
    if val in ("true", "1", "yes", "on"):
        return True
    if val in ("false", "0", "no", "off"):
        return False
    return default

def env_int(var_name: str, default: int) -> int:
    try:
        return int(os.getenv(var_name, str(default)))
    except (ValueError, TypeError):
        return default

# Provider Configuration
# We support PERCIVAL_API_KEY as the primary, with fallbacks to JARVINA, VENICE, and OPENAI.
PERCIVAL_API_KEY = (
    os.getenv("PERCIVAL_VISION_MCP_API_KEY") or
    os.getenv("PERCIVAL_API_KEY") or
    os.getenv("JARVINA_API_KEY") or
    os.getenv("VENICE_API_KEY") or
    os.getenv("OPENAI_API_KEY")
)

# Base URL: primary from environment, fallback to Venice or OpenAI.
JARVINA_BASE_URL = (
    os.getenv("PERCIVAL_VISION_MCP_BASE_URL") or
    os.getenv("JARVINA_BASE_URL") or 
    os.getenv("VENICE_BASE_URL") or
    "https://api.venice.ai/api/v1"
)

# Vision Model
JARVINA_VISION_MODEL = (
    os.getenv("PERCIVAL_VISION_MCP_MODEL") or
    os.getenv("JARVINA_VISION_MODEL") or
    "qwen-2.5-vl"
)

# Timeouts & Limits
PROVIDER_TIMEOUT = env_int("PERCIVAL_VISION_MCP_TIMEOUT_SECONDS", 90)
DEFAULT_MAX_TOKENS = env_int("PERCIVAL_VISION_MCP_MAX_TOKENS", 4096)
MODEL_CACHE_TTL = env_int("PERCIVAL_VISION_MCP_MODEL_CACHE_TTL_SECONDS", 300)

# Security & Sandbox
# Agnostic Home + Nanobot Workspace support
DEFAULT_ALLOWED_ROOTS = [
    Path.home().resolve(),
    Path(os.getcwd()).resolve(),
    Path("~/.nanobot/workspace").expanduser().resolve()
]

# Formatting and constraints
MAX_PIXELS = env_int("PERCIVAL_VISION_MCP_MAX_IMAGE_PIXELS", 40_000_000)
MAX_IMAGE_BYTES = env_int("PERCIVAL_VISION_MCP_MAX_IMAGE_BYTES", 20 * 1024 * 1024)
MAX_PROMPT_CHARS = env_int("PERCIVAL_VISION_MCP_MAX_ANALYSIS_PROMPT_CHARS", 4000)

# Egress & Network Guardrails
ALLOW_INSECURE_URL = env_bool("PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL", False)
ALLOW_PRIVATE_URL = env_bool("PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL", False)
ALLOWED_PROVIDER_HOSTS = [h.strip().lower() for h in os.getenv("PERCIVAL_VISION_MCP_ALLOWED_PROVIDER_HOSTS", "").split(",") if h.strip()]

# Rollout & Policy
STRICT_MODEL_CHECK = env_bool("PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK", True)
DISABLE_SANDBOX = env_bool("PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX", False)
