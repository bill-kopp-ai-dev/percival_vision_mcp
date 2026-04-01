from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from utils.runtime_config import env_bool
from utils.security_utils import record_security_event


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def get_allowed_working_roots() -> list[Path]:
    """
    Return allowed roots for working_dir containment.

    Environment:
      - PERCIVAL_VISION_MCP_ALLOWED_ROOTS: comma-separated absolute paths.
      - PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX: when true, disables root containment.
    """
    if env_bool("PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX", False):
        return []

    raw = os.getenv("PERCIVAL_VISION_MCP_ALLOWED_ROOTS", "").strip()
    roots: list[Path] = []

    if raw:
        candidates = [item.strip() for item in raw.split(",") if item.strip()]
        for candidate in candidates:
            path = Path(candidate).expanduser()
            if not path.is_absolute():
                continue
            try:
                roots.append(path.resolve(strict=True))
            except Exception:
                continue
        return roots

    try:
        return [Path(os.getcwd()).resolve(strict=True)]
    except Exception:
        return []


def validate_working_directory(working_dir: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Validate working_dir and enforce root containment policy.
    """
    working_path = Path((working_dir or "").strip()).expanduser()
    if not str(working_dir or "").strip():
        return None, "Error: working_dir is required."
    if not working_path.is_absolute():
        return None, f"Error: working_dir must be an absolute path, got: {working_dir}"
    if not working_path.exists():
        return None, f"Error: working_dir does not exist: {working_dir}"
    if not working_path.is_dir():
        return None, f"Error: working_dir is not a directory: {working_dir}"

    try:
        resolved_working = working_path.resolve(strict=True)
    except Exception as exc:
        return None, f"Error: failed to resolve working_dir '{working_dir}': {exc}"

    if env_bool("PERCIVAL_VISION_MCP_DISABLE_ROOT_SANDBOX", False):
        return resolved_working, None

    allowed_roots = get_allowed_working_roots()
    if not allowed_roots:
        return None, (
            "Error: no valid allowed roots configured for working_dir sandbox. "
            "Set PERCIVAL_VISION_MCP_ALLOWED_ROOTS with absolute existing directories."
        )

    if not any(_is_relative_to(resolved_working, root) for root in allowed_roots):
        allowed_display = ", ".join(str(root) for root in allowed_roots)
        record_security_event(
            "working_dir_blocked",
            {
                "working_dir": str(resolved_working),
                "allowed_roots": allowed_display,
            },
        )
        return None, (
            "Error: working_dir is outside allowed roots.\n"
            f"- working_dir: '{resolved_working}'\n"
            f"- allowed_roots: '{allowed_display}'"
        )

    return resolved_working, None


def validate_image_path(image_path: str, working_path: Path) -> tuple[Optional[Path], Optional[str]]:
    """
    Resolve and validate image path within working_dir.
    """
    raw_path = (image_path or "").strip()
    if not raw_path:
        return None, "Error: image_path is required."

    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = working_path / candidate

    try:
        resolved = candidate.resolve(strict=True)
    except Exception as exc:
        return None, (
            "Error: image_path does not exist or cannot be resolved.\n"
            f"- image_path: '{image_path}'\n"
            f"- resolved_candidate: '{candidate}'\n"
            f"- error: {exc}"
        )

    if not _is_relative_to(resolved, working_path):
        record_security_event(
            "path_escape_blocked",
            {
                "label": "image_path",
                "provided_path": image_path,
                "resolved_path": str(resolved),
                "working_dir": str(working_path),
            },
        )
        return None, (
            "Error: image_path must resolve inside working_dir.\n"
            f"- image_path: '{image_path}'\n"
            f"- resolved: '{resolved}'\n"
            f"- working_dir: '{working_path}'"
        )

    if not resolved.is_file():
        return None, f"Error: image_path must reference a file: {resolved}"

    return resolved, None
