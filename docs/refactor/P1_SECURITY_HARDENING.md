# P1 Security Hardening (Concluído)

Data: 2026-03-31

## Escopo

Fortalecer defesa contra prompt injection e reduzir exposição de dados sensíveis em erros/telemetria.

## Mudanças

### 1) Prompt Injection Hardening

- `utils/client.py`
  - inclusão de guardrail de sistema por padrão em chamadas de visão;
  - variáveis:
    - `PERCIVAL_VISION_MCP_DISABLE_SYSTEM_GUARDRAIL`
    - `PERCIVAL_VISION_MCP_SYSTEM_GUARDRAIL_PROMPT`
- `utils/security_utils.py`
  - expansão de padrões de detecção para variações multilíngues e obfuscadas.

### 2) Minimização de vazamento em erros

- `tools/vision_tools.py`
  - erros de validação de `working_dir`/`image_path` retornam mensagens genéricas;
  - detalhes usam referências compactas (`*_ref`) e `reason` normalizado;
  - `invalid_prompt` não ecoa conteúdo do prompt;
  - falha de provedor não retorna exceção bruta para cliente.

### 3) Governança de telemetria

- `get_security_metrics`
  - por padrão retorna apenas `detail_keys` dos eventos recentes;
  - detalhes completos só com `PERCIVAL_VISION_MCP_EXPOSE_SECURITY_EVENT_DETAILS=true`.
- `clear_security_metrics`
  - bloqueado por padrão;
  - liberação explícita com `PERCIVAL_VISION_MCP_ALLOW_SECURITY_METRICS_CLEAR=true`.

## Testes adicionados/atualizados

- `tests/test_prompt_injection_p1.py`
  - detecção multilíngue;
  - detecção obfuscada;
  - presença de mensagem de sistema no request ao provedor.
- `tests/test_server.py`
  - validação de não vazamento de prompt em erro;
  - validação de política de telemetria (`clear` bloqueado por padrão, exposição opcional de detalhes).

## Resultado

- defesa de prompt injection mais robusta;
- menor risco de vazamento de dados sensíveis em payloads MCP;
- telemetria de segurança com princípio de mínimo privilégio por padrão.
