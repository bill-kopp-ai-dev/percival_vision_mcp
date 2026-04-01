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
from utils.security_utils import record_security_event, reset_security_metrics_for_tests  # noqa: E402


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


class TestPolicyAndAuditP2(unittest.TestCase):
    def setUp(self) -> None:
        reset_security_metrics_for_tests()

    def test_disabled_tool_is_blocked(self) -> None:
        with _EnvOverride({"PERCIVAL_VISION_MCP_DISABLED_TOOLS": "describe_image"}):
            payload = json.loads(vision_tools.describe_image(image_path="anything.png"))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "tool_access_denied")
        self.assertEqual(payload["details"]["tool"], "describe_image")

    def test_enabled_tools_allowlist_blocks_non_listed_tool(self) -> None:
        with _EnvOverride({"PERCIVAL_VISION_MCP_ENABLED_TOOLS": "describe_image"}):
            payload = json.loads(vision_tools.read_text(image_path="anything.png"))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "tool_access_denied")
        self.assertEqual(payload["details"]["reason"], "not_in_enabled_tools_allowlist")

    def test_access_policy_status_always_allowed(self) -> None:
        with _EnvOverride({"PERCIVAL_VISION_MCP_ENABLED_TOOLS": "describe_image"}):
            payload = json.loads(vision_tools.get_access_policy_status())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["operation"], "get_access_policy_status")

    def test_access_policy_status_warns_on_conflict(self) -> None:
        with _EnvOverride(
            {
                "PERCIVAL_VISION_MCP_ENABLED_TOOLS": "describe_image",
                "PERCIVAL_VISION_MCP_DISABLED_TOOLS": "describe_image",
            }
        ):
            payload = json.loads(vision_tools.get_access_policy_status())
        self.assertTrue(payload["ok"])
        warnings = payload["data"]["warnings"]
        self.assertIn("same tool appears in both enabled and disabled sets; deny wins", warnings)

    def test_persistent_audit_log_writes_and_redacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit_path = Path(tmp_dir) / "security-audit.jsonl"
            with _EnvOverride(
                {
                    "PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT": "true",
                    "PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH": str(audit_path),
                    "PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES": "100000",
                }
            ):
                record_security_event("unit_test_event", {"leak": "api_key=secret-value"})

                self.assertTrue(audit_path.exists())
                lines = audit_path.read_text(encoding="utf-8").splitlines()
                self.assertGreaterEqual(len(lines), 1)
                row = json.loads(lines[-1])
                self.assertEqual(row["event"], "unit_test_event")
                self.assertIn("[REDACTED]", row["details"]["leak"])

                metrics_payload = json.loads(vision_tools.get_security_metrics())
                self.assertTrue(metrics_payload["ok"])
                audit_state = metrics_payload["data"]["security_metrics"]["audit"]
                self.assertTrue(audit_state["enabled"])
                self.assertEqual(audit_state["path"], str(audit_path))

    def test_persistent_audit_rotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit_path = Path(tmp_dir) / "security-audit.jsonl"
            with _EnvOverride(
                {
                    "PERCIVAL_VISION_MCP_ENABLE_PERSISTENT_SECURITY_AUDIT": "true",
                    "PERCIVAL_VISION_MCP_SECURITY_AUDIT_LOG_PATH": str(audit_path),
                    "PERCIVAL_VISION_MCP_SECURITY_AUDIT_MAX_BYTES": "80",
                }
            ):
                record_security_event("event_1", {"data": "x" * 120})
                record_security_event("event_2", {"data": "y" * 120})

                rotated = Path(str(audit_path) + ".1")
                self.assertTrue(rotated.exists())
                self.assertTrue(audit_path.exists())


if __name__ == "__main__":
    unittest.main()
