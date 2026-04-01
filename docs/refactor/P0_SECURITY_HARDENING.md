# P0 Security Hardening (Concluído)

Data: 2026-03-31

## Escopo

Implementação dos três blocos críticos de P0:

1. Bloqueio de exfiltração por arquivo local disfarçado de imagem.
2. Hardening de egress para `PERCIVAL_BASE_URL`.
3. Autenticação HTTP obrigatória por padrão, inclusive em loopback.

## Mudanças

### 1) Validação robusta de imagem

- `utils/client.py`
  - validação de conteúdo real da imagem com Pillow (`Image.verify` + formato detectado);
  - allowlist de MIME (`PERCIVAL_VISION_MCP_ALLOWED_IMAGE_MIME_TYPES`);
  - limite de pixels (`PERCIVAL_VISION_MCP_MAX_IMAGE_PIXELS`);
  - rejeição explícita de arquivo inválido/corrompido/não-imagem.

### 2) Validação de URL do provedor (egress policy)

- `utils/client.py`
  - nova validação de `base_url`:
    - esquema seguro por padrão (`https`);
    - bloqueio de host local/privado por padrão;
    - allowlist opcional de host;
    - telemetria de eventos `provider_url_allowed|provider_url_blocked`.
- variáveis:
  - `PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL`
  - `PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL`
  - `PERCIVAL_VISION_MCP_ALLOWED_PROVIDER_HOSTS`

### 3) HTTP auth padrão estrito

- `main.py`
  - loopback HTTP sem token agora falha por padrão;
  - bypass só com `--allow-unauthenticated-loopback-http` (ou env equivalente).
- `utils/runtime_config.py`
  - nova configuração:
    - `PERCIVAL_VISION_MCP_ALLOW_UNAUTHENTICATED_LOOPBACK_HTTP`.

## Testes adicionados

- `tests/test_security_p0.py`
  - rejeita arquivo não-imagem;
  - aceita PNG válido;
  - valida bloqueio/allow de `base_url`;
  - valida requirement de token em loopback por padrão.

## Documentação atualizada

- `README.md`
- `QUICKSTART.md`
- `docs/WINDOWS_INSTALL.md`
