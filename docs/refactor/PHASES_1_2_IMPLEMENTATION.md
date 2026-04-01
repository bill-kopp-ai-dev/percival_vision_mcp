# Implementação - Fase 1 e Fase 2

## Fase 1: Estrutura Padrão FastMCP

Concluída com os seguintes componentes:

- `server.py`
  - Instância `FastMCP` central.
  - `configure_runtime_settings(...)` para aplicar settings de runtime.
- `main.py`
  - Entrypoint padrão.
  - Modos de transporte: `stdio`, `sse`, `streamable-http`.
  - Segurança de bind remoto com autenticação opcional por bearer token.
  - `--print-profile` para integração com nanobot.
- Compatibilidade legada:
  - `src/server.py` mantido como shim (`python -m src.server`).

## Fase 2: Contrato para Nanobot

Concluída com os seguintes componentes:

- `utils/contracts.py`
  - Envelope padronizado de sucesso e erro.
  - `request_id` e metadata com `contract_version`.
- `utils/nanobot_profile.py`
  - `SERVER_NAME`, `CONTRACT_VERSION`.
  - `build_nanobot_profile()` com workflow recomendado.
- `tools/vision_tools.py`
  - Tools legadas preservadas.
  - Nova tool `get_nanobot_profile`.
  - Todas as respostas retornam JSON estruturado.

## Observação de Escopo

Fase 3 (hardening completo de segurança/path sandbox e telemetria detalhada) permanece pendente.

