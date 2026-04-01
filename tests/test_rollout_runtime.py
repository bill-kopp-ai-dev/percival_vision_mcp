import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("PERCIVAL_API_KEY", "test-key")
os.environ.setdefault("PERCIVAL_VISION_MCP_ALLOWED_ROOTS", tempfile.gettempdir())

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tools.vision_tools as vision_tools  # noqa: E402
from utils.runtime_config import load_provider_runtime_config, load_rollout_config  # noqa: E402
from utils.security_utils import reset_security_metrics_for_tests  # noqa: E402


class _EnvOverride:
    def __init__(self, updates: dict[str, str | None]) -> None:
        self._updates = updates
        self._original: dict[str, str | None] = {}

    def __enter__(self):
        for key, value in self._updates.items():
            self._original[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return self

    def __exit__(self, exc_type, exc, tb):
        for key, original in self._original.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original
        return False


class TestRolloutAndRuntimeConfig(unittest.TestCase):
    def setUp(self) -> None:
        reset_security_metrics_for_tests()

    def test_provider_config_alias_precedence(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_API_KEY": None,
                "JARVINA_API_KEY": "jarvina-key",
                "VENICE_API_KEY": "venice-key",
                "OPENAI_API_KEY": "openai-key",
                "PERCIVAL_BASE_URL": None,
                "JARVINA_BASE_URL": "https://api.example.test/v1",
                "PERCIVAL_DEFAULT_MODEL": None,
                "JARVINA_VISION_MODEL": "qwen-compat-vl",
            }
        ):
            cfg = load_provider_runtime_config()

        self.assertEqual(cfg.api_key, "jarvina-key")
        self.assertEqual(cfg.api_key_env, "JARVINA_API_KEY")
        self.assertEqual(cfg.base_url, "https://api.example.test/v1")
        self.assertEqual(cfg.default_model, "qwen-compat-vl")

    def test_rollout_config_invalid_mode_falls_back(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_WORKING_DIR_MODE": "invalid-value",
                "PERCIVAL_VISION_MCP_EMIT_COMPAT_WARNINGS": "false",
                "PERCIVAL_VISION_MCP_ROLLOUT_TRACK": "canary",
            }
        ):
            cfg = load_rollout_config()

        self.assertEqual(cfg.working_dir_mode, "compat")
        self.assertFalse(cfg.emit_compat_warnings)
        self.assertEqual(cfg.rollout_track, "canary")

    def test_strict_rollout_requires_working_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample = Path(tmp_dir) / "sample.png"
            sample.write_bytes(b"sample-bytes")
            with _EnvOverride({"PERCIVAL_VISION_MCP_WORKING_DIR_MODE": "strict"}):
                payload = json.loads(vision_tools.describe_image(image_path=str(sample)))

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "missing_working_dir")
        self.assertEqual(payload["details"]["working_dir_mode"], "strict")

    def test_rollout_status_tool_contract(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_WORKING_DIR_MODE": "compat",
                "PERCIVAL_VISION_MCP_ROLLOUT_TRACK": "canary",
                "PERCIVAL_VISION_MCP_STRICT_WORKING_DIR_DATE": "2026-08-31",
            }
        ):
            payload = json.loads(vision_tools.get_rollout_status())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["operation"], "get_rollout_status")
        self.assertEqual(payload["data"]["rollout"]["track"], "canary")
        self.assertEqual(payload["data"]["rollout"]["working_dir_mode"], "compat")
        self.assertEqual(payload["data"]["rollout"]["strict_working_dir_date"], "2026-08-31")

    def test_security_posture_includes_rollout_block(self) -> None:
        with _EnvOverride({"PERCIVAL_VISION_MCP_WORKING_DIR_MODE": "compat"}):
            payload = json.loads(vision_tools.get_security_posture())

        self.assertTrue(payload["ok"])
        rollout = payload["data"]["runtime"]["rollout"]
        self.assertEqual(rollout["working_dir_mode"], "compat")
        self.assertIn("working_dir compatibility mode enabled", " ".join(payload["data"]["warnings"]))


if __name__ == "__main__":
    unittest.main()
