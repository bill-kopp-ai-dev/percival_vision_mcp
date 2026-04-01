import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main as main_module  # noqa: E402
from utils.client import encode_image_for_vision, validate_provider_base_url  # noqa: E402
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


class TestP0SecurityHardening(unittest.TestCase):
    def setUp(self) -> None:
        reset_security_metrics_for_tests()

    def test_encode_image_rejects_non_image_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake = Path(tmp_dir) / "secret.png"
            fake.write_text("not an image")
            with self.assertRaises(ValueError):
                encode_image_for_vision(str(fake))

    def test_encode_image_accepts_valid_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            image = Path(tmp_dir) / "tiny.png"
            with Image.new("RGB", (1, 1), color=(255, 0, 0)) as generated:
                generated.save(image, format="PNG")
            payload = encode_image_for_vision(str(image))
        self.assertTrue(payload["data_uri"].startswith("data:image/png;base64,"))

    def test_provider_url_rejects_http_by_default(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL": "false",
                "PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL": "true",
            }
        ):
            with self.assertRaises(ValueError):
                validate_provider_base_url("http://127.0.0.1/v1")

    def test_provider_url_rejects_private_host_by_default(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL": "false",
                "PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL": "false",
            }
        ):
            with self.assertRaises(ValueError):
                validate_provider_base_url("https://127.0.0.1/v1")

    def test_provider_url_allows_http_private_when_explicitly_enabled(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_ALLOW_INSECURE_PROVIDER_URL": "true",
                "PERCIVAL_VISION_MCP_ALLOW_PRIVATE_PROVIDER_URL": "true",
            }
        ):
            normalized = validate_provider_base_url("http://127.0.0.1/v1")
        self.assertEqual(normalized, "http://127.0.0.1/v1")

    def test_http_loopback_requires_auth_by_default(self) -> None:
        with self.assertRaises(ValueError):
            main_module._validate_http_runtime_security(  # noqa: SLF001
                mode="sse",
                host="127.0.0.1",
                allow_remote_http=False,
                allow_unauthenticated_loopback_http=False,
                auth_token=None,
                auth_token_env="PERCIVAL_VISION_MCP_AUTH_TOKEN",
            )

    def test_http_loopback_without_auth_can_be_enabled_explicitly(self) -> None:
        main_module._validate_http_runtime_security(  # noqa: SLF001
            mode="sse",
            host="127.0.0.1",
            allow_remote_http=False,
            allow_unauthenticated_loopback_http=True,
            auth_token=None,
            auth_token_env="PERCIVAL_VISION_MCP_AUTH_TOKEN",
        )


if __name__ == "__main__":
    unittest.main()
