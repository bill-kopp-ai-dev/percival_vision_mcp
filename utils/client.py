from __future__ import annotations

import base64
import httpx
import logging
from pathlib import Path
from typing import Any, Optional
from openai import AsyncOpenAI
from PIL import Image, UnidentifiedImageError

from utils.config import (
    JARVINA_BASE_URL,
    PERCIVAL_API_KEY,
    JARVINA_VISION_MODEL,
    PROVIDER_TIMEOUT,
    MAX_PIXELS,
    MAX_IMAGE_BYTES
)

logger = logging.getLogger(__name__)

# Constants for vision processing
ALLOWED_MIME_TYPES = {
    "image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp", "image/tiff"
}

_client_instance: Optional[AsyncOpenAI] = None

def get_client() -> AsyncOpenAI:
    """
    Lazily initialize and return the AsyncOpenAI client.
    """
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    if not PERCIVAL_API_KEY:
        raise RuntimeError("Missing API Key. Please configure PERCIVAL_VISION_MCP_API_KEY.")

    _client_instance = AsyncOpenAI(
        api_key=PERCIVAL_API_KEY,
        base_url=JARVINA_BASE_URL,
        timeout=float(PROVIDER_TIMEOUT),
        http_client=httpx.AsyncClient(
            timeout=httpx.Timeout(float(PROVIDER_TIMEOUT)),
            follow_redirects=True
        )
    )
    return _client_instance

async def validate_image_file(path: Path) -> str:
    """
    Check if file is a valid image, within size limits, and return its MIME type.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    
    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_BYTES:
         raise ValueError(f"Image too large ({file_size} bytes). Max: {MAX_IMAGE_BYTES}")

    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            width, height = img.size
            if width * height > MAX_PIXELS:
                raise ValueError(f"Resolution too high ({width}x{height}). Max: {MAX_PIXELS} pixels.")
            
            fmt = str(img.format or "").upper()
            mime = Image.MIME.get(fmt, f"image/{fmt.lower()}")
            if mime not in ALLOWED_MIME_TYPES:
                raise ValueError(f"Unsupported image format: {mime}")
            return mime
    except UnidentifiedImageError:
        raise ValueError(f"File at {path} is not a valid image.")
    except Exception as e:
        raise ValueError(f"Error validating image {path}: {e}")

async def encode_image(path: Path) -> dict[str, str]:
    """
    Read and encode image to base64 for vision API.
    """
    mime_type = await validate_image_file(path)
    raw_bytes = path.read_bytes()
    b64_data = base64.b64encode(raw_bytes).decode("utf-8")
    
    return {
        "mime_type": mime_type,
        "base64": b64_data,
        "data_uri": f"data:{mime_type};base64,{b64_data}"
    }

async def run_vision_request(
    *,
    image_path: Path,
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> dict[str, Any]:
    """
    Execute a vision completion request asynchronously.
    """
    client = get_client()
    target_model = model or JARVINA_VISION_MODEL
    img_data = await encode_image(image_path)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": img_data["data_uri"]}}
        ]
    })
    
    try:
        response = await client.chat.completions.create(
            model=target_model,
            messages=messages,
            max_tokens=max_tokens or 1024
        )
        
        content = response.choices[0].message.content
        return {
            "text": content or "",
            "model": target_model,
            "usage": response.usage.model_dump() if response.usage else {}
        }
    except Exception as e:
        logger.error(f"Vision request failed: {e}")
        raise RuntimeError(f"API request failed: {e}")
