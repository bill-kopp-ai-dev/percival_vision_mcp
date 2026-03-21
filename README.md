# 👁️ Percival Vision MCP Server

**Percival** is a provider-agnostic [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for Computer Vision and Image Analysis. It was designed to break free from local model constraints and adopt the universal industry standard (OpenAI Vision / Chat Completions), integrating natively with cloud providers like **Venice.ai** — acting as the "eyes" of the [nanobot](https://github.com/HKUDS/nanobot) autonomous agent ecosystem within [percival.OS](https://github.com/bill-kopp-ai-dev/percival.OS_Dev).

---

## 🙏 Credits & Original Repository

This project is a deeply refactored fork of **[ollama-vision-mcp](https://github.com/xkiranj/ollama-vision-mcp)**, originally created by **xkiranj**.

The semantic tool architecture (`read_text`, `identify_objects`, `describe_image`) was inherited from the original project. Our refactoring focused on **portability**: we removed the strict dependency on local Ollama infrastructure and rebuilt the inference engine to accept any cloud or local API that complies with the multimodal Chat Completions standard.

---

## 🛠️ What Changed? (Refactoring Details)

The following architectural changes were made to transform `ollama-vision-mcp` into **Percival**:

### 1. New Connection Engine (Core Decoupling)

The original project made direct HTTP calls to `localhost:11434` or used the Ollama local library.

- **Change:** Replaced the local engine with the official `openai` SDK used as an agnostic bridge. Added `PERCIVAL_BASE_URL` and `PERCIVAL_API_KEY` environment variables with a fail-fast validation at startup.
- **Benefit:** The server can now process images using state-of-the-art hosted models on Venice.ai, Groq, OpenAI, or any compatible API, without changing any tool logic.

### 2. Standard Vision Payload (`encode_image_for_vision`)

Ollama accepted images as plain base64 string arrays. The industry-standard API requires a strict multimodal format.

- **Change:** Created a universal helper (`encode_image_for_vision`) that reads local files, detects the MIME type (`image/jpeg`, `image/png`, etc.) and builds the correct multimodal payload using Data URIs (`data:image/ext;base64,...`), then sends them via the `image_url` content block.
- **Benefit:** Eliminates `Bad Request` errors from cloud providers and ensures that images are correctly processed as part of a Chat Completions conversation.

### 3. Intelligent Model Discovery (Agent Autonomy)

Since Percival now targets providers with dozens of models — most of them text-only — there was a risk of the agent sending images to incompatible models.

- **Change:** Added the `list_available_vision_models` tool, which queries the provider's `/v1/models` endpoint and applies a keyword heuristic (`vision`, `vl`, `llava`, `pixtral`, `qwen`) to filter and recommend only vision-capable models.
- **Benefit:** Gives full autonomy to the LLM orchestrator (e.g. nanobot) to discover and select the correct vision model before making inference calls.

### 4. Infrastructure Cleanup & Renaming

- **Change:** Removed legacy setup scripts (`setup.bat`, `setup.sh`, `setup.py`) and centralized package management in `pyproject.toml` using `uv`. Server class renamed from `OllamaVisionServer` to `PercivalVisionServer`. Configuration extracted to a dedicated `src/config.py` with environment-aware defaults.

---

## 🔌 MCP Tools

| Tool | Description |
|---|---|
| `list_available_vision_models` | Queries the provider and returns a filtered list of vision-capable models. **Call this first** if the model is unknown. |
| `analyze_image` | Analyze an image based on a custom user-provided prompt |
| `describe_image` | Generate a comprehensive general description of an image |
| `identify_objects` | Identify and list all distinct objects present in an image |
| `read_text` | Extract all visible text from an image (OCR capability) |

---

## 🚀 Requirements

- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) package manager

---

## 📦 Installation

```bash
git clone https://github.com/bill-kopp-ai-dev/percival_vision_mcp.git
cd percival_vision_mcp
uv sync
```

---

## ▶️ Running

```bash
uv run src/server.py
```

Or via the installed script entry point:

```bash
percival-vision
```

---

## ⚙️ Configuration

Percival is configured exclusively via environment variables:

| Variable | Required | Default | Description |
|---|---|---|---|
| `PERCIVAL_API_KEY` | ✅ | — | API key for the provider (fail-fast if missing) |
| `PERCIVAL_BASE_URL` | ❌ | `https://api.openai.com/v1` | Base URL for the OpenAI-compatible API endpoint |
| `PERCIVAL_DEFAULT_MODEL` | ❌ | `qwen32b-vision` | Default vision model to use when none is specified |
| `PERCIVAL_LOG_LEVEL` | ❌ | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PERCIVAL_TIMEOUT` | ❌ | `120` | Request timeout in seconds |

---

## 🤖 Integrating with nanobot / Claude Desktop

Add the following entry to your agent's `config.json`:

```json
"percival-vision": {
  "command": "/path/to/.venv/bin/python",
  "args": ["-m", "src.server"],
  "env": {
    "PYTHONPATH": "/path/to/percival_vision_mcp",
    "PERCIVAL_API_KEY": "your-api-key-here",
    "PERCIVAL_BASE_URL": "https://api.venice.ai/api/v1",
    "PERCIVAL_DEFAULT_MODEL": "qwen-2.5-vl"
  }
}
```

### Example Usage

```
User: What does this screenshot say?

Agent: [calls list_available_vision_models to find a vision-capable model]
       [calls read_text with the screenshot path and detected model]
       → Returns all extracted text from the image

User: Now describe what's shown in the UI.

Agent: [calls describe_image with the same path]
       → Returns a detailed description of the interface elements
```

---

## 📁 Project Structure

```
percival_vision_mcp/
├── pyproject.toml           # Project metadata, dependencies & script entry point
├── src/
│   ├── config.py            # Environment-aware configuration manager
│   └── server.py            # PercivalVisionServer: MCP tools, vision payload handler, inference engine
├── examples/
│   ├── claude_desktop_config.json         # Claude Desktop integration example
│   └── usage_examples.py                  # Usage code samples
├── tests/
│   └── test_server.py       # Server tests
└── docs/
    └── WINDOWS_INSTALL.md   # Windows-specific installation guide
```

---

## 📖 Attribution

This project is built upon the work of:

- **[xkiranj/ollama-vision-mcp](https://github.com/xkiranj/ollama-vision-mcp)** — The direct upstream project, providing the original semantic vision tool architecture.

---

## 📄 License

This project maintains the MIT License from the original repository. See [LICENSE](LICENSE) for details.
