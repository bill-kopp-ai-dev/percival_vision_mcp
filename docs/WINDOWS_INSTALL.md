# Windows Installation Guide

## Prerequisites

- Python 3.10+
- `uv` installed

## Install

```powershell
cd C:\absolute\path\to\percival.OS_Dev
$env:UV_PROJECT_ENVIRONMENT="C:\absolute\path\to\percival.OS_Dev\.venv"
uv sync --directory mcp_servers\percival_vision_mcp
```

## Environment

```powershell
$env:PERCIVAL_API_KEY="your-api-key"
$env:PERCIVAL_BASE_URL="https://api.venice.ai/api/v1"
$env:PERCIVAL_DEFAULT_MODEL="qwen-2.5-vl"
$env:PERCIVAL_VISION_MCP_ALLOWED_ROOTS="C:\absolute\path\to\percival.OS_Dev"
$env:PERCIVAL_VISION_MCP_WORKING_DIR_MODE="compat"
$env:PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL="false"
$env:PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL="false"
$env:PERCIVAL_VISION_MCP_ALLOW_SECURITY_METRICS_CLEAR="false"
$env:PERCIVAL_VISION_MCP_EXPOSE_SECURITY_EVENT_DETAILS="false"
$env:PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT="false"
$env:PERCIVAL_VISION_MCP_ENABLED_TOOLS=""
$env:PERCIVAL_VISION_MCP_DISABLED_TOOLS=""
```

Aliases legados compatíveis:
- API key: `JARVINA_API_KEY`, `VENICE_API_KEY`, `OPENAI_API_KEY`
- Base URL: `JARVINA_BASE_URL`
- Modelo default: `JARVINA_VISION_MODEL`

## Run (stdio)

```powershell
uv run --no-sync --directory C:\absolute\path\to\percival.OS_Dev\mcp_servers\percival_vision_mcp python main.py --mode stdio
```

## Run tests

```powershell
uv run --no-sync --directory C:\absolute\path\to\percival.OS_Dev\mcp_servers\percival_vision_mcp pytest -q
```

## Controlled Rollout (Strict Canary)

```powershell
$env:PERCIVAL_VISION_MCP_WORKING_DIR_MODE="strict"
uv run --no-sync --directory C:\absolute\path\to\percival.OS_Dev\mcp_servers\percival_vision_mcp python main.py --mode stdio
```

HTTP em loopback também exige token por padrão:

```powershell
$env:PERCIVAL_VISION_MCP_AUTH_TOKEN="change-me"
uv run --no-sync --directory C:\absolute\path\to\percival.OS_Dev\mcp_servers\percival_vision_mcp python main.py --mode sse --host 127.0.0.1 --port 8001
```
