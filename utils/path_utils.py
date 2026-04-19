from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from utils.config import DEFAULT_ALLOWED_ROOTS, DISABLE_SANDBOX

def get_allowed_working_roots() -> list[Path]:
    """
    Return list of Path objects that are allowed as roots for the context sandbox.
    
    Order:
    1. PERCIVAL_VISION_MCP_ALLOWED_ROOTS env var (if set)
    2. Default roots (Home, CWD, Nanobot Workspace)
    """
    if DISABLE_SANDBOX:
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
        if roots:
            return roots

    # Fallback to default agnostic roots
    for root in DEFAULT_ALLOWED_ROOTS:
        try:
            # We don't force strict existence for Home/Workspace here to avoid crashes,
            # but we resolve what we can.
            roots.append(root.resolve(strict=False))
        except Exception:
            continue

    return list(dict.fromkeys(roots))

def validate_working_directory(working_dir: Optional[str]) -> tuple[Path, Optional[str]]:
    """
    Validate and resolve a working directory against the allowed roots.
    """
    if not working_dir:
        return Path(os.getcwd()).resolve(), None

    try:
        path = Path(working_dir).expanduser().resolve(strict=True)
    except Exception as exc:
        return Path(os.getcwd()), f"Working directory does not exist or cannot be resolved: {exc}"

    if not path.is_dir():
        return path, "Path is not a directory."

    if DISABLE_SANDBOX:
        return path, None

    allowed_roots = get_allowed_working_roots()
    if not any(str(path).startswith(str(root)) for root in allowed_roots):
        return path, "Working directory is outside allowed roots (sandbox escape blocked)."

    return path, None

def validate_image_path(image_path: str, working_dir: Path) -> tuple[Path, Optional[str]]:
    """
    Validate that an image path is safe and exists within the working directory.
    """
    raw_path = (image_path or "").strip()
    if not raw_path:
        return Path("."), "image_path is required."

    try:
        # Resolve the image path relative to working_dir if not absolute
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = (working_dir / path).resolve(strict=True)
        else:
            path = path.resolve(strict=True)
    except Exception as exc:
        return Path("."), f"Image path does not exist or cannot be resolved: {exc}"

    if not path.is_file():
        return path, "Path must reference a file."

    # Entailment check: must be inside working_dir
    try:
        path.relative_to(working_dir)
    except ValueError:
        return path, "Image path is outside the validated working_dir (jailbreak attempt blocked)."

    return path, None
