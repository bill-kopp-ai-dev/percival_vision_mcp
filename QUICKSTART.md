# Quick Start

## 1) Instalar dependências com uv

```bash
cd /absolute/path/to/percival.OS_Dev
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
uv sync --directory mcp_servers/percival_vision_mcp
```

## 2) Definir variáveis de ambiente

```bash
export PERCIVAL_API_KEY="your-api-key"
export PERCIVAL_BASE_URL="https://api.venice.ai/api/v1"
export PERCIVAL_DEFAULT_MODEL="qwen-2.5-vl"
# export PERCIVAL_VISION_MCP_MODEL_CATALOG_PATH="/absolute/path/to/custom/vision_models.json"
export PERCIVAL_VISION_MCP_ALLOWED_ROOTS="/absolute/path/to/percival.OS_Dev"
export PERCIVAL_VISION_MCP_WORKING_DIR_MODE="compat"
export PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK="true"
export PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK_FORCE_REFRESH="false"
export PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL="false"
export PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL="false"
export PERCIVAL_VISION_MCP_ALLOW_SECURITY_METRICS_CLEAR="false"
export PERCIVAL_VISION_MCP_EXPOSE_SECURITY_EVENT_DETAILS="false"
export PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT="false"
export PERCIVAL_VISION_MCP_ENABLED_TOOLS=""
export PERCIVAL_VISION_MCP_DISABLED_TOOLS=""
```

Aliases legados compatíveis:
- API key: `JARVINA_API_KEY`, `VENICE_API_KEY`, `OPENAI_API_KEY`
- Base URL: `JARVINA_BASE_URL`
- Modelo default: `JARVINA_VISION_MODEL`

## 3) Rodar em stdio (modo recomendado para nanobot)

```bash
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode stdio
```

## 4) Validar profile de integração

```bash
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --print-profile
```

HTTP (SSE/streamable-http) exige token por padrão, inclusive em loopback:

```bash
PERCIVAL_VISION_MCP_AUTH_TOKEN="change-me" uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode sse --host 127.0.0.1 --port 8001
```

## 5) Rodar testes

```bash
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp pytest -q
```

## 6) Validar rollout controlado

Canary em modo estrito:

```bash
PERCIVAL_VISION_MCP_WORKING_DIR_MODE=strict uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode stdio
```

Canary para Fase B de modelo estrito:

```bash
PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK=true uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode stdio
```

Override legado temporário (somente migração):

```bash
PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK=false uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode stdio
```

Checklist rápido:
- `get_rollout_status` retorna `working_dir_mode=strict` no canary.
- clientes legados sem `working_dir` falham com `code=missing_working_dir`.
- `get_security_metrics` mostra queda de `compat_working_dir_derived`.
- para Fase B, monitorar `model_precheck_skipped`, `model_precheck_passed`, `model_precheck_blocked`.
