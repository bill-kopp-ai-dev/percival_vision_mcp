# 🤖 Percival Vision - percival.OS MCP

**Version 0.0.2**

[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)]()
[![MCP](https://img.shields.io/badge/mcp-server-blue.svg)]()
[![percival.OS](https://img.shields.io/badge/percival.OS-ecosystem-orange.svg)](https://github.com/bill-kopp-ai-dev/percival.OS)

## 📋 Description
**Percival Vision** is an asynchronous, high-performance, and provider-agnostic Computer Vision MCP server. Designed for seamless integration with Nanobot, it enables AI agents to "see" by providing advanced image analysis, OCR, and object detection.

This server is part of the **percival.OS** ecosystem, a Personal Agentic Operating System designed for autonomy, security, and absolute privacy.

---

## 🛡️ percival.OS Principles
Like all components of `percival.OS`, this MCP server strictly follows our core principles:

- **Privacy & Governance**: You have full control over which vision models are used and which image directories are accessible.
- **Data Sovereignty**: Visual analysis processing is done under your API keys, and the results remain in your infrastructure.
- **Hardened Security**: We implement a strict path sandbox, vision model output sanitization (treated as untrusted content), and security telemetry.
- **Transparency**: Open-source and auditable, with stable contracts to ensure the integrity of agent operations.

---

## 🚀 Features & Tools

### Vision Operations
- `vision_analyze`: Generic analysis with custom prompts.
- `vision_describe`: Generates comprehensive visual descriptions.
- `vision_identify`: Structured object detection and listing.
- `vision_read_text`: Advanced OCR (Text extraction).

### Model Governance
- `vision_recommend_model`: Recommends models based on task type.
- `vision_list_models`: Lists metadata-rich model cards from the local catalog.
- `vision_get_model_availability`: Real-time availability check on the provider side.

### System & Telemetry
- `vision_get_status`: Returns server operational status.
- `vision_get_security_posture`: Inspects current security settings.
- `vision_get_security_metrics`: Real-time audit counters.

---

## ⚙️ Configuration in percival.OS (Nanobot)
Add the following configuration to your `~/.nanobot/config.json`:

```json
{
  "tools": {
    "mcpServers": {
      "percival-vision": {
        "command": "uv",
        "args": [
          "run",
          "--no-sync",
          "--directory",
          "/path/to/percival_vision_mcp",
          "python",
          "main.py",
          "--mode",
          "stdio"
        ],
        "env": {
          "PERCIVAL_VISION_MCP_API_KEY": "YOUR_KEY",
          "PERCIVAL_VISION_MCP_MODEL": "qwen3-5-9b",
          "PERCIVAL_VISION_MCP_ALLOWED_ROOTS": "/home/user/Pictures"
        }
      }
    }
  }
}
```

---

## 🛠️ Development & Testing
This project uses `uv` for dependency management.

```bash
# Sync environment
uv sync

# Run in stdio mode
uv run python main.py --mode stdio
```

---

## 📚 About the Project
This server is an integral module of the **percival.OS** project. It provides the "eyes" for Nanobot, allowing advanced visual understanding.

- **Main Repository**: [https://github.com/bill-kopp-ai-dev/percival.OS](https://github.com/bill-kopp-ai-dev/percival.OS)
- **License**: MIT

---
*Developed with ❤️ by the percival.OS Team*
