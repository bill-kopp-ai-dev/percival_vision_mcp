# Implementação - Fase 4 e Fase 5

## Fase 4: Cliente de Provedor e Configuração Unificada

Concluída com os seguintes componentes:

- `utils/runtime_config.py`
  - camada única para leitura/normalização de env vars;
  - `ProviderRuntimeConfig` e `HttpRuntimeConfig`;
  - defaults centralizados para provedor e transporte.
- `utils/client.py`
  - passa a consumir `load_provider_runtime_config()`;
  - mantém aliases legados (`JARVINA_*`, `PERCIVAL_*`) para compatibilidade.
- `main.py`
  - defaults do parser passam a vir de `load_http_runtime_config()`.
- `src/config.py`
  - shim legado passa a refletir a configuração unificada.

## Fase 5: Paridade Funcional e Compatibilidade

Concluída com os seguintes componentes:

- `tools/vision_tools.py`
  - `working_dir` passa a ser opcional por compatibilidade;
  - quando ausente, o servidor deriva de forma segura:
    - `image_path` absoluto -> parent da imagem;
    - caso contrário -> `cwd`.
  - payload inclui `working_dir_source` (`explicit` ou `compat_derived`).
- `utils/nanobot_profile.py`
  - contrato atualizado para `2026-03-s5`;
  - notas explícitas de compatibilidade legada.
- documentação/examples
  - atualização de README/Quickstart/Windows com aliases e comportamento compatível.

## Validação

- suíte `pytest` local atualizada para cobrir:
  - contrato `2026-03-s5`;
  - compatibilidade sem `working_dir`;
  - aliases de configuração de API key no `Config` legado.
