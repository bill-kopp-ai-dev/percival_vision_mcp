# Percival Vision MCP Server

An asynchronous, high-performance, and provider-agnostic Computer Vision MCP server. Fully standardized with FastMCP and designed for seamless integration with the **Nanobot** agent ecosystem.

This server enables AI agents to "see" by providing advanced image analysis, OCR, object detection, and intelligent model routing capabilities.

> **Contract Version**: `2026-03-s10` (Modern/Async)

## 🚀 Key Features

- **Async-First Architecture**: Built on `AsyncOpenAI` and `httpx`, allowing non-blocking concurrent vision operations.
- **Dynamic Model Routing**: Empowers agents to choose the best model based on a structured catalog (E2EE/Privacy, High-Resolution, or Performance tiers).
- **Agnostic Sandbox**: Flexible file access logic that supports Home (`~`) and Nanobot workspaces (`~/.nanobot/workspace`) across different OS languages.
- **Rich Analytics & Security**: Hardened I/O with path validation, output sanitization, and real-time security metrics.
- **Standardized Contracts**: Predictable JSON responses for both success and error states.

## 🛠 Available Tools

### Vision Operations
- `analyze_image`: Generic analysis with custom prompts.
- `describe_image`: Generates comprehensive visual descriptions.
- `identify_objects`: Structured object detection and listing.
- `read_text`: Advanced OCR (Text extraction).

### Model Governance & Routing
- `recommend_vision_model_for_intent`: Recommends models based on task type (e.g., OCR, Privacy).
- `list_vision_model_cards`: Lists metadata-rich model cards from the local catalog.
- `get_vision_model_card`: Retrieval of detailed model capabilities.
- `verify_vision_model_availability`: Real-time availability check on the provider side.
- `list_available_vision_models`: Live inventory of models from the provider.

### System & Telemetry
- `get_nanobot_profile`: Machine-readable integration profile.
- `get_security_metrics`: Real-time audit counters.
- `clear_security_metrics`: Policy-gated counter reset.
- `get_security_posture`: Current security settings status.
- `get_rollout_status`: Modernization and async status track.
- `get_access_policy_status`: Active tool policy report.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PERCIVAL_VISION_MCP_API_KEY` | Primary API Key (Fallback: `JARVINA_API_KEY`) | Required |
| `PERCIVAL_VISION_MCP_BASE_URL` | Provider Base URL | `https://api.venice.ai/api/v1` |
| `PERCIVAL_VISION_MCP_MODEL` | Default Vision Model | `qwen3-5-9b` |
| `PERCIVAL_VISION_MCP_ALLOWED_ROOTS` | Allowed root paths (CSV) | `~, cwd, workspace` |
| `PERCIVAL_VISION_MCP_TIMEOUT_SECONDS`| Provider request timeout | `90` |
| `PERCIVAL_VISION_MCP_STRICT_MODEL_CHECK`| Verify models against catalog | `true` |
| `PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX`| Disable path validation (Warning!) | `false` |

## 📦 Installation

This server uses `uv` for ultra-fast dependency management.

```bash
# Clone and sync dependencies
cd percival_vision_mcp
uv sync
```

## 🎮 Execution

### Stdio Mode (Standard for MCP)

```bash
uv run python main.py --mode stdio
```

### SSE / HTTP Transport (Modern)

```bash
# Start with SSE support and Auth Token
PERCIVAL_VISION_MCP_AUTH_TOKEN=my-secure-token uv run python main.py --mode sse --port 8001
```

## 🤖 Nanobot Integration

Add the following to your `~/.nanobot/config.json`:

```json
"percival-vision": {
  "command": "uv",
  "args": [
    "run",
    "--no-sync",
    "--directory",
    "/absolute/path/to/percival_vision_mcp",
    "python",
    "main.py",
    "--mode",
    "stdio"
  ],
  "env": {
    "PERCIVAL_VISION_MCP_API_KEY": "YOUR_KEY",
    "PERCIVAL_VISION_MCP_MODEL": "qwen3-5-9b",
    "PERCIVAL_VISION_MCP_ALLOWED_ROOTS": "/home/user/Documents"
  }
}
```

## 🛡 Security Policy

- **Path Sandbox**: All file operations are restricted to `PERCIVAL_VISION_MCP_ALLOWED_ROOTS`.
- **Content Sanitization**: Vision model outputs are treated as untrusted and sanitized against prompt-injection patterns.
- **Model Validation**: Models can be restricted to only those present in the trusted `vision_models.json` catalog.

## 📄 License & Attribution

This project is part of the **Percival OS** ecosystem. 
Modernized by the Google Deepmind Agentic Coding team in collaboration with **Bill Kopp**.

Original concept inspired by high-performance vision servers.

---
*Built for the next generation of agentic intelligence.*
