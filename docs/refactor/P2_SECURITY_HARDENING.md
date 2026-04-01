# P2 Security Hardening (Concluído)

Data: 2026-03-31

## Escopo

Introduzir governança operacional avançada:

1. Controle de acesso por tool (allowlist/denylist).
2. Auditoria de segurança persistente em arquivo.
3. Observabilidade consolidada de policy/audit em `get_security_posture`.

## Mudanças

### 1) Tool Access Policy

- Novo módulo: `utils/policy_utils.py`
  - `PERCIVAL_VISION_MCP_ENABLED_TOOLS` (allowlist opcional).
  - `PERCIVAL_VISION_MCP_DISABLED_TOOLS` (denylist opcional).
  - `PERCIVAL_VISION_MCP_ALWAYS_ALLOWED_TOOLS` (extensão da lista segura padrão).
- `tools/vision_tools.py`
  - todas as tools passam por `tool_access_guard`.
  - nova tool `get_access_policy_status` para inspeção de política efetiva.

### 2) Persistent Security Audit

- `utils/security_utils.py`
  - suporte opcional a auditoria JSONL em disco:
    - `PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT`
    - `PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH`
    - `PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES`
  - rotação simples (`.1`) quando excede limite.
  - estado de auditoria incluído no snapshot de métricas.

### 3) Observabilidade de postura

- `get_security_posture` agora inclui:
  - configuração de access policy;
  - estado de auditoria persistente;
  - warnings operacionais correspondentes.

## Testes

- Novo: `tests/test_policy_audit_p2.py`
  - bloqueio por denylist;
  - bloqueio por allowlist;
  - acessibilidade de `get_access_policy_status`;
  - auditoria persistente com redaction;
  - rotação de arquivo de auditoria.

## Resultado

- governança de segurança mais madura para operação em produção;
- superfície de execução reduzida por política de tool;
- trilha de auditoria persistente opcional para incident response.
