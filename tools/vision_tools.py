from __future__ import annotations

from typing import Optional

from server import mcp
from utils.client import run_vision_request, get_client
from utils.contracts import error_response, new_request_id, success_response
from utils.path_utils import validate_image_path, validate_working_directory
from utils.config import JARVINA_VISION_MODEL, MAX_PROMPT_CHARS, STRICT_MODEL_CHECK
from utils.security_utils import (
    get_security_metrics_snapshot,
    clear_security_metrics as clear_security_metrics_snapshot,
    sanitize_untrusted_text,
    record_security_event
)
from utils.vision_model_catalog import (
    get_model_card as catalog_get_model_card,
    list_model_cards as catalog_list_model_cards
)

# Constants
PROMPTS = {
    "describe": "Descreva esta imagem em detalhes. O que você vê? Quais são os elementos principais, cores e o contexto geral?",
    "objects": "Liste todos os objetos distintos que você consegue identificar nesta imagem. Retorne em tópicos estruturados.",
    "ocr": "Extraia todo o texto visível nesta imagem. Retorne APENAS o texto extraído.",
}

# --- Internal Helpers ---

async def _analyze_flow(
    *,
    image_path: str,
    working_dir: Optional[str],
    prompt: str,
    model: Optional[str],
    max_tokens: Optional[int],
    operation: str,
    request_id: str
) -> str:
    """
    Common async flow for all vision analysis tools.
    """
    # 1. Validate Working Directory
    work_path, work_err = validate_working_directory(working_dir)
    if work_err:
        return error_response(work_err, code="invalid_working_dir", request_id=request_id)

    # 2. Validate Image Path
    img_path, img_err = validate_image_path(image_path, work_path)
    if img_err:
        return error_response(img_err, code="invalid_image_path", request_id=request_id)

    # 3. Prompt Sanitization
    if not prompt or len(prompt) > MAX_PROMPT_CHARS:
        return error_response(f"Prompt must be 1-{MAX_PROMPT_CHARS} chars.", code="invalid_prompt", request_id=request_id)

    # 4. Strict Model Pre-check (Optional but recommended)
    target_model = (model or JARVINA_VISION_MODEL).strip()
    if STRICT_MODEL_CHECK:
        card = catalog_get_model_card(target_model)
        if not card:
             # Just a warning or soft check? In strict mode we might block.
             # For now, we proceed but log it.
             record_security_event("model_visibility_warning", {"model": target_model})

    try:
        # 5. Core Async Request
        result = await run_vision_request(
            image_path=img_path,
            prompt=prompt,
            model=target_model,
            max_tokens=max_tokens
        )

        # 6. Sanitize Output
        sanitized = sanitize_untrusted_text(result["text"])
        
        return success_response(
            data={
                "operation": operation,
                "analysis": sanitized["text"],
                "model": result["model"],
                "security": {
                    "sanitized": sanitized["modified"],
                    "findings": sanitized["findings"]
                }
            },
            request_id=request_id
        )
    except Exception as e:
        return error_response(str(e), code="vision_request_failed", request_id=request_id)

# --- Tools ---

@mcp.tool("vision_analyze")
async def analyze_image(
    image_path: str,
    working_dir: Optional[str] = None,
    prompt: str = "Describe this image in detail.",
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Analyze an image with a custom prompt (Async)."""
    return await _analyze_flow(
        image_path=image_path,
        working_dir=working_dir,
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        operation="analyze_image",
        request_id=new_request_id("analyze")
    )

@mcp.tool("vision_describe")
async def describe_image(
    image_path: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Generate a detailed description of an image (Async)."""
    return await _analyze_flow(
        image_path=image_path,
        working_dir=working_dir,
        prompt=PROMPTS["describe"],
        model=model,
        max_tokens=max_tokens,
        operation="describe_image",
        request_id=new_request_id("describe")
    )

@mcp.tool("vision_identify")
async def identify_objects(
    image_path: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """List objects identified in an image (Async)."""
    return await _analyze_flow(
        image_path=image_path,
        working_dir=working_dir,
        prompt=PROMPTS["objects"],
        model=model,
        max_tokens=max_tokens,
        operation="identify_objects",
        request_id=new_request_id("objects")
    )

@mcp.tool("vision_read_text")
async def read_text(
    image_path: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Extract visible text from an image - OCR (Async)."""
    return await _analyze_flow(
        image_path=image_path,
        working_dir=working_dir,
        prompt=PROMPTS["ocr"],
        model=model,
        max_tokens=max_tokens,
        operation="read_text",
        request_id=new_request_id("ocr")
    )

@mcp.tool("vision_list_provider_models")
async def list_available_vision_models(force_refresh: bool = False) -> str:
    """List vision models available directly from the provider (Async)."""
    try:
        client = get_client()
        response = await client.models.list()
        models = [m.id for m in response.data if any(k in m.id.lower() for k in ["vision", "vl", "pixtral", "qwen"])]
        return success_response(data={"models": sorted(models)}, tool_name="list_available_vision_models")
    except Exception as e:
        return error_response(str(e), code="list_models_failed")

@mcp.tool("vision_list_models")
async def list_vision_model_cards(task_type: Optional[str] = None) -> str:
    """List structured model cards for vision tasks from local catalog."""
    try:
        cards = catalog_list_model_cards(task_type=task_type)
        return success_response(data={"models": cards}, tool_name="list_vision_model_cards")
    except Exception as e:
        return error_response(str(e), code="catalog_error")

@mcp.tool("vision_get_model")
async def get_vision_model_card(model_id: str) -> str:
    """Get a detailed model card by ID."""
    card = catalog_get_model_card(model_id)
    if not card:
        return error_response(f"Model '{model_id}' not found in catalog.", code="model_not_found")
    return success_response(data={"model": card}, tool_name="get_vision_model_card")

@mcp.tool("vision_get_security_metrics")
async def get_security_metrics() -> str:
    """Return in-memory security counters."""
    return success_response(data=get_security_metrics_snapshot(), tool_name="get_security_metrics")

@mcp.tool("vision_clear_security_metrics")
async def clear_security_metrics() -> str:
    """Reset security counters."""
    cleared = clear_security_metrics_snapshot()
    return success_response(data={"cleared": cleared}, tool_name="clear_security_metrics")

@mcp.tool("vision_get_contract_info")
async def get_nanobot_profile() -> str:
    """Return machine-readable integration profile for nanobot."""
    from utils.nanobot_profile import build_nanobot_profile
    profile = build_nanobot_profile()
    return success_response(data={"profile": profile}, tool_name="get_nanobot_profile")

@mcp.tool("vision_get_model_availability")
async def verify_vision_model_availability(model_id: str, task_type: str = "general_vision") -> str:
    """Verify if a model is available in the provider and catalog."""
    from utils.client import get_client
    client = get_client()
    try:
        models = await client.models.list()
        provider_ids = [m.id for m in models.data]
        available = model_id in provider_ids
        card = catalog_get_model_card(model_id)
        return success_response(data={
            "model_id": model_id,
            "available": available,
            "in_catalog": card is not None,
            "task_type": task_type
        })
    except Exception as e:
        return error_response(str(e))

@mcp.tool("vision_recommend_model")
async def recommend_vision_model_for_intent(intent: str, task_type: str = "general_vision") -> str:
    """Recommend a model based on user intent and task type."""
    # Simple recommendation logic based on catalog
    cards = catalog_list_model_cards(task_type=task_type)
    if not cards:
        return error_response("No models found for this task type.")
    
    # Simple heuristic: pick the first 'pro' or 'premium' quality tier
    recommendation = next((c for c in cards if c.get("quality_tier") in ["pro", "premium"]), cards[0])
    return success_response(data={"recommendation": recommendation, "intent": intent})

@mcp.tool("vision_get_security_posture")
async def get_security_posture() -> str:
    """Return effective security settings and status."""
    from utils.config import DISABLE_SANDBOX, STRICT_MODEL_CHECK
    return success_response(data={
        "sandbox_disabled": DISABLE_SANDBOX,
        "strict_model_check": STRICT_MODEL_CHECK,
        "security_metrics_enabled": True
    })

@mcp.tool("vision_get_status")
async def get_rollout_status() -> str:
    """Return current rollout/compatibility mode status."""
    return success_response(data={"mode": "modern", "async_enabled": True})

@mcp.tool("vision_get_policy")
async def get_access_policy_status() -> str:
    """Return current tool access policy status."""
    return success_response(data={"policy": "open", "restrictions": []})
