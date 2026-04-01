# Implementação - Fase 6 e Fase 7

## Fase 6: Testes, Docs e Exemplos

Concluída com os seguintes componentes:

- Testes ampliados:
  - `tests/test_rollout_runtime.py` para validar:
    - precedência de aliases de configuração de provedor;
    - fallback seguro de configuração de rollout;
    - comportamento `strict` (erro `missing_working_dir`);
    - contrato de `get_rollout_status`;
    - bloco de rollout em `get_security_posture`.
- Atualização de documentação:
  - `README.md`: novas seções de cobertura de testes e rollout controlado.
  - `QUICKSTART.md`: checklist de canary strict.
  - `docs/WINDOWS_INSTALL.md`: fluxo equivalente para Windows.
- Exemplos:
  - `examples/usage_examples.py` com `get_rollout_status`.
  - configs de integração com `PERCIVAL_VISION_MCP_WORKING_DIR_MODE`.

## Fase 7: Rollout Controlado

Concluída com os seguintes componentes:

- `utils/runtime_config.py`
  - `RolloutConfig` com:
    - `PERCIVAL_VISION_MCP_WORKING_DIR_MODE` (`compat|strict`);
    - `PERCIVAL_VISION_MCP_EMIT_COMPAT_WARNINGS`;
    - `PERCIVAL_VISION_MCP_STRICT_WORKING_DIR_DATE`;
    - `PERCIVAL_VISION_MCP_ROLLOUT_TRACK`.
- `tools/vision_tools.py`
  - enforcement de rollout:
    - `compat`: deriva `working_dir` com segurança;
    - `strict`: bloqueia ausência de `working_dir` com `code=missing_working_dir`.
  - payloads com metadados de rollout.
  - nova tool `get_rollout_status`.
- `main.py`
  - startup inclui `rollout_track` e `working_dir_mode` para observabilidade operacional.
- `utils/nanobot_profile.py`
  - contrato atualizado para `2026-03-s7`.
  - recomendação explícita de `get_rollout_status`.

## Validação

- `pytest -q` executado localmente com sucesso.
- `py_compile` executado nos módulos do servidor com sucesso.
