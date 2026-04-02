# Percival Vision MCP Server

Servidor MCP de visão computacional provider-agnostic, padronizado com FastMCP e contrato estruturado para uso com nanobot.

Contrato atual: `2026-03-s9`.

## Status da Refatoração

- Fase 0: Baseline e congelamento concluída (`docs/refactor/`).
- Fase 1: Estrutura padrão FastMCP concluída (`main.py` + `server.py`).
- Fase 2: Contrato para nanobot concluída (respostas estruturadas + `get_nanobot_profile`).
- Fase 3: Segurança e Governança de I/O concluída (sandbox de path, sanitização e métricas).
- Fase 4: Cliente de provedor e configuração unificada concluída (`utils/runtime_config.py` + cliente unificado).
- Fase 5: Paridade funcional e compatibilidade concluída (modo compatível sem `working_dir` explícito).
- Fase 6: Testes, docs e exemplos concluída (matriz ampliada + guias de operação).
- Fase 7: Rollout controlado concluída (modo `compat|strict` + telemetria de migração).
- Fase B de seleção de modelo concluída (strict_model_check via env + telemetria de impacto).
- Fase C concluída: `strict_model_check` tornou-se default `true` após estabilização.
- Ajuste pós-rollout concluído: `identify_objects` validado em `general_vision` no precheck estrito para evitar falso `model_task_mismatch`.
- Catálogo atualizado com `qwen-2.5-vl` para compatibilidade do modelo default.
- Hardening de Segurança P0, P1 e P2 concluído.
- Limpeza pós-refatoração concluída (remoção de shims legados em `src/` e artefatos locais temporários).

## Estrutura atual

- entrypoint CLI: `main.py`
- configuração FastMCP: `server.py`
- tools MCP: `tools/vision_tools.py`
- utilitários compartilhados: `utils/`
- testes: `tests/`

## Tools disponíveis

- `recommend_vision_model_for_intent`
- `list_vision_model_cards`
- `get_vision_model_card`
- `verify_vision_model_availability`
- `list_available_vision_models`
- `analyze_image`
- `describe_image`
- `identify_objects`
- `read_text`
- `get_nanobot_profile`
- `get_security_metrics`
- `clear_security_metrics`
- `get_security_posture`
- `get_rollout_status`
- `get_access_policy_status`

## Contrato de Resposta

Todas as tools retornam JSON compacto com envelope:

- sucesso: `ok=true`, `data`, `meta`, `request_id`, `legacy_text` (opcional)
- erro: `ok=false`, `error`, `code`, `details` (opcional), `meta`, `request_id`, `legacy_text` (opcional)

`meta` inclui: `server`, `contract_version`, `timestamp`, `tool`.

## Segurança e Governança de I/O (Fase 3)

Para tools de análise (`analyze_image`, `describe_image`, `identify_objects`, `read_text`):

- `working_dir` é recomendado.
- `image_path` deve resolver dentro de `working_dir`.
- `working_dir` deve estar dentro de roots permitidas (`PERCIVAL_VISION_MCP_ALLOWED_ROOTS`) quando sandbox estiver habilitado.
- `strict_model_check` é habilitado por padrão e pode ser desabilitado por env em cenários legados controlados.
- saída do modelo é tratada como dado não confiável e passa por sanitização contra padrões de prompt-injection.
- eventos de segurança são registrados em memória.
- compatibilidade legada: se `working_dir` não for enviado, o servidor deriva com segurança (`parent` de `image_path` absoluto ou `cwd`).

## Requisitos

- Python 3.10+
- `uv`

## Instalação

```bash
cd /absolute/path/to/percival.OS_Dev
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
uv sync --directory mcp_servers/percival_vision_mcp
```

## Execução

Stdio (padrão):

```bash
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode stdio
```

SSE / Streamable HTTP:

```bash
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
PERCIVAL_VISION_MCP_AUTH_TOKEN=change-me uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode sse --host 127.0.0.1 --port 8001
PERCIVAL_VISION_MCP_AUTH_TOKEN=change-me uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --mode streamable-http --host 127.0.0.1 --port 8001 --stateless-http
```

Imprimir profile de integração:

```bash
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp python main.py --print-profile
```

## Variáveis de ambiente

Configuração de provedor:

- `PERCIVAL_API_KEY` (primária; fallback: `JARVINA_API_KEY`, `VENICE_API_KEY`, `OPENAI_API_KEY`)
- `PERCIVAL_BASE_URL` (primária; fallback: `JARVINA_BASE_URL`; default: `https://api.openai.com/v1`)
- `PERCIVAL_DEFAULT_MODEL` (primária; fallback: `JARVINA_VISION_MODEL`; default: `qwen-2.5-vl`)
- `PERCIVAL_VISION_MCP_MODEL_CATALOG_PATH` (opcional; override do caminho de `vision_models.json`)
- `PERCIVAL_TIMEOUT` (default: `120`)
- `PERCIVAL_VISION_MCP_MAX_TOKENS` (default: `1000`)
- `PERCIVAL_VISION_MCP_MODEL_CACHE_TTL` (default: `300`)

Segurança e I/O:

- `PERCIVAL_VISION_MCP_ALLOWED_ROOTS` (lista CSV de roots absolutos permitidos para `working_dir`)
- `PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX` (default: `false`)
- `PERCIVAL_VISION_MCP_MAX_ANALYSIS_PROMPT_CHARS` (default: `4000`)
- `PERCIVAL_VISION_MCP_MAX_OUTPUT_CHARS` (default: `8000`)
- `PERCIVAL_VISION_MCP_MAX_IMAGE_BYTES` (default: `20971520`)
- `PERCIVAL_VISION_MCP_MAX_IMAGE_PIXELS` (default: `40000000`)
- `PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK` (default: `true`; quando `false`, desativa precheck estrito de modelo)
- `PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK_FORCE_REFRESH` (default: `false`; força refresh de `/models` durante precheck estrito)
- `PERCIVAL_VISION_MCP_ALLOWED_IMAGE_MIME_TYPES` (CSV; default seguro interno)
- `PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL` (default: `false`)
- `PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL` (default: `false`)
- `PERCIVAL_VISION_MCP_ALLOWED_PROVIDER_HOSTS` (CSV opcional de allowlist)
- `PERCIVAL_VISION_MCP_DISABLE_SYSTEM_GUARDRAIL` (default: `false`)
- `PERCIVAL_VISION_MCP_SYSTEM_GUARDRAIL_PROMPT` (override opcional do guardrail de sistema)
- `PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT` (default: `false`)
- `PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH` (default: `.percival_vision_security_audit.jsonl`)
- `PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES` (default: `5242880`)

Runtime FastMCP:

- `PERCIVAL_VISION_MCP_MODE` (`stdio|sse|streamable-http`, default: `stdio`)
- `PERCIVAL_VISION_MCP_HOST` (default: `127.0.0.1`)
- `PERCIVAL_VISION_MCP_PORT` (default: `8001`)
- `PERCIVAL_VISION_MCP_LOG_LEVEL` (default: `INFO`)
- `PERCIVAL_VISION_MCP_AUTH_TOKEN` (recomendado para HTTP)
- `PERCIVAL_VISION_MCP_ALLOW_REMOTE_HTTP` (default: `false`)
- `PERCIVAL_VISION_MCP_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP` (default: `false`, inseguro)
- `PERCIVAL_VISION_MCP_WORKING_DIR_MODE` (`compat|strict`, default: `compat`)
- `PERCIVAL_VISION_MCP_STRICT_WORKING_DIR_DATE` (default: `2026-06-30`)
- `PERCIVAL_VISION_MCP_EMIT_COMPAT_WARNINGS` (default: `true`)
- `PERCIVAL_VISION_MCP_ROLLOUT_TRACK` (default: `stable`)
- `PERCIVAL_VISION_MCP_ALLOW_SECURITY_METRICS_CLEAR` (default: `false`)
- `PERCIVAL_VISION_MCP_EXPOSE_SECURITY_EVENT_DETAILS` (default: `false`)
- `PERCIVAL_VISION_MCP_ENABLED_TOOLS` (CSV de allowlist opcional)
- `PERCIVAL_VISION_MCP_DISABLED_TOOLS` (CSV de denylist opcional)
- `PERCIVAL_VISION_MCP_ALWAYS_ALLOWED_TOOLS` (CSV adicional para tools sempre liberadas)

## Integração com nanobot

Exemplo para `~/.nanobot/config.json`:

```json
"percival-vision": {
  "command": "uv",
  "args": [
    "run",
    "--no-sync",
    "--directory",
    "/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp",
    "python",
    "main.py",
    "--mode",
    "stdio"
  ],
  "enabledTools": [
    "recommend_vision_model_for_intent",
    "list_vision_model_cards",
    "get_vision_model_card",
    "verify_vision_model_availability",
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
    "get_access_policy_status"
  ],
  "toolTimeout": 45,
  "env": {
    "UV_PROJECT_ENVIRONMENT": "/absolute/path/to/percival.OS_Dev/.venv",
    "PERCIVAL_API_KEY": "your-api-key-here",
    "PERCIVAL_BASE_URL": "https://api.venice.ai/api/v1",
    "PERCIVAL_DEFAULT_MODEL": "qwen-2.5-vl",
    "PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK": "true",
    "PERCIVAL_VISION_MCP_ALLOWED_ROOTS": "/absolute/path/to/percival.OS_Dev"
  }
}
```

### Exemplo de chamada de tool (modo recomendado)

```json
{
  "working_dir": "/absolute/path/to/percival.OS_Dev",
  "image_path": "assets/screenshot.png"
}
```

### Exemplo de chamada em modo compatível legado

```json
{
  "image_path": "assets/screenshot.png"
}
```

## Testes

```bash
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/percival.OS_Dev/.venv
uv run --no-sync --directory /absolute/path/to/percival.OS_Dev/mcp_servers/percival_vision_mcp pytest -q
```

Cobertura de regressão inclui:
- contrato estruturado e `contract_version`;
- sanitização de saída não confiável;
- sandbox de path;
- compatibilidade legada sem `working_dir`;
- rollout `compat|strict` e status operacional.
- precheck de modelo estrito (`strict_model_check=true` por padrão) com cenários `skipped/passed/blocked`.
- compatibilidade de task mapping para `identify_objects` com modelos `general_vision`.
- políticas de egress e autenticação HTTP padrão estritas.
- proteção de telemetria (detalhes ocultos por padrão).

## Rollout Controlado (Fase 7)

Estratégia recomendada:
1. `stable/compat` (default): aceitar chamadas legadas sem `working_dir` e monitorar eventos `compat_working_dir_derived`.
2. `canary/strict` (staging): ativar `PERCIVAL_VISION_MCP_WORKING_DIR_MODE=strict` e corrigir clientes restantes.
3. Fase B de modelos: medir impacto de `strict_model_check` via counters de precheck.
4. Fase C: operar com `strict_model_check=true` como padrão e usar override pontual apenas quando necessário.
5. produção em `strict`: bloquear ausência de `working_dir` com erro `missing_working_dir`.

Tool de apoio operacional:
- `get_rollout_status`: mostra track, modo efetivo e data alvo para migração.
- `get_security_metrics`: permite confirmar redução de tráfego em modo compatível.
- monitorar counters: `model_precheck_skipped`, `model_precheck_passed`, `model_precheck_blocked`.

## Compatibilidade temporária

- Nomes das 5 tools legadas de visão foram preservados:
  `list_available_vision_models`, `analyze_image`, `describe_image`, `identify_objects`, `read_text`.
- As novas tools de catálogo/recomendação são opcionais.
- `strict_model_check` está ligado por padrão (`true`); para clientes legados, use override temporário explícito.
