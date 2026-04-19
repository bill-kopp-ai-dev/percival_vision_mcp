from __future__ import annotations

import json
import os
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

CATALOG_SCHEMA_VERSION = "2.1"
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "2.0", "2.1"}
SUPPORTED_TASK_TYPES = {
    "general_vision",
    "ocr",
    "object_detection",
    "document_qa",
    "chart_analysis",
    "spatial_reasoning",
    "real_time_vision",
    "long_context_vision",
}
QUALITY_TIERS = {"entry", "standard", "pro", "premium"}
SPEED_TIERS = {"fast", "balanced", "slow"}
COST_ESTIMATION_LEVELS = {"low", "moderate", "high", "unknown"}
PRIVACY_TIERS = {"standard", "e2ee"}


class ModelCatalogError(ValueError):
    """Raised when the vision model catalog is invalid or cannot be loaded."""


def _default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[1] / "vision_models.json"


def _normalize_task_type(task_type: str) -> str:
    normalized = (task_type or "").strip().lower().replace(" ", "_")
    aliases = {
        "general": "general_vision",
        "vision": "general_vision",
        "analysis": "general_vision",
        "analyze": "general_vision",
        "describe": "general_vision",
        "general_vision": "general_vision",
        "ocr": "ocr",
        "read_text": "ocr",
        "text_extraction": "ocr",
        "object_detection": "object_detection",
        "identify_objects": "object_detection",
        "objects": "object_detection",
        "document_qa": "document_qa",
        "chart_analysis": "chart_analysis",
        "spatial_reasoning": "spatial_reasoning",
        "real_time_vision": "real_time_vision",
        "long_context_vision": "long_context_vision",
    }
    return aliases.get(normalized, normalized)


def normalize_task_type(task_type: str) -> str:
    """Public helper for tool-layer normalization."""
    return _normalize_task_type(task_type)


def _ensure_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelCatalogError(f"Invalid '{field}': expected non-empty string.")
    return value.strip()


def _ensure_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ModelCatalogError(f"Invalid '{field}': expected non-empty list of strings.")

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ModelCatalogError(f"Invalid '{field}': all entries must be non-empty strings.")
        normalized.append(item.strip())
    return normalized


def _infer_task_types(recommended_use_cases: list[str]) -> list[str]:
    inferred: list[str] = ["general_vision"]
    use_cases = {item.strip().lower() for item in recommended_use_cases if item and item.strip()}

    if {"private_document_qa", "web_scraping_vision"} & use_cases:
        inferred.append("document_qa")
        inferred.append("ocr")
    if {"complex_chart_analysis", "high_res_visual_reasoning"} & use_cases:
        inferred.append("chart_analysis")
    if {"spatial_awareness_tasks"} & use_cases:
        inferred.append("spatial_reasoning")
    if {"real_time_vision_apps", "real_time_data_parsing", "fast_visual_feedback", "high_volume_processing"} & use_cases:
        inferred.append("real_time_vision")
    if {"long_context_multimodal", "video_frame_analysis", "multimodal_chatbots"} & use_cases:
        inferred.append("long_context_vision")
    if {"fast_image_tagging"} & use_cases:
        inferred.append("object_detection")

    return list(dict.fromkeys(inferred))


def _normalize_cost_estimation(raw_value: Any) -> str:
    normalized = str(raw_value or "unknown").strip().lower()
    aliases = {
        "low": "low",
        "cheap": "low",
        "moderate": "moderate",
        "medium": "moderate",
        "standard": "moderate",
        "high": "high",
        "expensive": "high",
        "unknown": "unknown",
    }
    result = aliases.get(normalized, normalized)
    return result if result in COST_ESTIMATION_LEVELS else "unknown"


def _infer_quality_tier(model_id: str, cost_estimation: str) -> str:
    normalized_model = model_id.lower()
    if "mini" in normalized_model:
        return "entry"
    if cost_estimation == "low":
        return "standard"
    if cost_estimation == "moderate":
        return "pro"
    if cost_estimation == "high":
        return "premium"
    return "standard"


def _infer_speed_tier(model_id: str, model_name: str) -> str:
    normalized = f"{model_id} {model_name}".lower()
    if any(token in normalized for token in ("fast", "flash", "mini")):
        return "fast"
    if "235b" in normalized:
        return "slow"
    return "balanced"


def _infer_avoid_use_cases(task_types: list[str]) -> list[str]:
    avoid: list[str] = []
    if "ocr" in task_types:
        avoid.append("creative_freeform_generation")
    if "object_detection" in task_types:
        avoid.append("pixel_level_segmentation")
    if "real_time_vision" in task_types:
        avoid.append("latency_insensitive_batch_jobs")
    return avoid


def _normalize_card_v2(raw_card: dict[str, Any]) -> dict[str, Any]:
    model_id = _ensure_string(raw_card.get("id"), "id")
    name = _ensure_string(raw_card.get("name", model_id), "name")
    description = _ensure_string(raw_card.get("description", "No description provided."), "description")
    developer = str(raw_card.get("developer") or "unknown").strip() or "unknown"

    recommended_use_cases_raw = raw_card.get("recommended_use_cases")
    if recommended_use_cases_raw is None:
        recommended_use_cases = ["general_image_captioning"]
    else:
        recommended_use_cases = _ensure_string_list(recommended_use_cases_raw, "recommended_use_cases")

    task_types_raw = raw_card.get("task_types")
    if not task_types_raw:
        task_types = _infer_task_types(recommended_use_cases)
    else:
        task_types = [_normalize_task_type(task) for task in _ensure_string_list(task_types_raw, "task_types")]

    unknown_tasks = [task for task in task_types if task not in SUPPORTED_TASK_TYPES]
    if unknown_tasks:
        raise ModelCatalogError(
            f"Model '{model_id}' has unsupported task_types: {', '.join(sorted(set(unknown_tasks)))}"
        )
    task_types = list(dict.fromkeys(task_types))

    capabilities_raw = raw_card.get("capabilities")
    if capabilities_raw is None:
        capabilities_raw = {}
    if not isinstance(capabilities_raw, dict):
        raise ModelCatalogError(f"Model '{model_id}': capabilities must be an object.")

    privacy_tier = str(capabilities_raw.get("privacy_tier") or "standard").strip().lower()
    if privacy_tier not in PRIVACY_TIERS:
        raise ModelCatalogError(
            f"Model '{model_id}': privacy_tier must be one of {sorted(PRIVACY_TIERS)}, got '{privacy_tier}'."
        )

    capabilities = {
        "text_input": bool(capabilities_raw.get("text_input", True)),
        "vision_input": bool(capabilities_raw.get("vision_input", True)),
        "privacy_tier": privacy_tier,
    }

    status = str(raw_card.get("status") or "active").strip().lower()
    if status not in {"active", "deprecated", "disabled"}:
        raise ModelCatalogError(
            f"Model '{model_id}': status must be one of active/deprecated/disabled, got '{status}'."
        )

    cost_estimation = _normalize_cost_estimation(raw_card.get("cost_estimation"))

    quality_tier = str(raw_card.get("quality_tier") or _infer_quality_tier(model_id, cost_estimation)).strip().lower()
    if quality_tier not in QUALITY_TIERS:
        raise ModelCatalogError(
            f"Model '{model_id}': quality_tier must be one of {sorted(QUALITY_TIERS)}, got '{quality_tier}'."
        )

    speed_tier = str(raw_card.get("speed_tier") or _infer_speed_tier(model_id, name)).strip().lower()
    if speed_tier not in SPEED_TIERS:
        raise ModelCatalogError(
            f"Model '{model_id}': speed_tier must be one of {sorted(SPEED_TIERS)}, got '{speed_tier}'."
        )

    aliases_raw = raw_card.get("aliases")
    if aliases_raw is None:
        aliases_raw = []
    if not isinstance(aliases_raw, list):
        raise ModelCatalogError(f"Model '{model_id}': aliases must be a list.")

    aliases: list[str] = []
    for alias in aliases_raw:
        if isinstance(alias, str) and alias.strip():
            aliases.append(alias.strip())

    avoid_use_cases_raw = raw_card.get("avoid_use_cases")
    if avoid_use_cases_raw is None:
        avoid_use_cases = _infer_avoid_use_cases(task_types)
    else:
        avoid_use_cases = _ensure_string_list(avoid_use_cases_raw, "avoid_use_cases")

    pricing_raw = raw_card.get("pricing")
    if pricing_raw is None:
        pricing_raw = {
            "currency": "relative",
            "cost_estimation": cost_estimation,
            "per_image": None,
        }
    if not isinstance(pricing_raw, dict):
        raise ModelCatalogError(f"Model '{model_id}': pricing must be an object.")

    pricing = {
        "currency": str(pricing_raw.get("currency") or "relative"),
        "cost_estimation": _normalize_cost_estimation(pricing_raw.get("cost_estimation", cost_estimation)),
        "per_image": pricing_raw.get("per_image"),
    }

    normalized = {
        "id": model_id,
        "name": name,
        "developer": developer,
        "description": description,
        "task_types": task_types,
        "status": status,
        "capabilities": capabilities,
        "cost_estimation": cost_estimation,
        "pricing": pricing,
        "quality_tier": quality_tier,
        "speed_tier": speed_tier,
        "recommended_use_cases": recommended_use_cases,
        "avoid_use_cases": avoid_use_cases,
        "aliases": aliases,
    }

    recommended_api_params = raw_card.get("recommended_api_params")
    if recommended_api_params is not None:
        if not isinstance(recommended_api_params, dict):
            raise ModelCatalogError(
                f"Model '{model_id}': recommended_api_params must be an object when provided."
            )
        normalized["recommended_api_params"] = deepcopy(recommended_api_params)

    known_fields = {
        "id",
        "name",
        "developer",
        "description",
        "task_types",
        "status",
        "capabilities",
        "cost_estimation",
        "pricing",
        "quality_tier",
        "speed_tier",
        "recommended_use_cases",
        "avoid_use_cases",
        "aliases",
        "recommended_api_params",
    }
    for key, value in raw_card.items():
        if key in known_fields:
            continue
        normalized[key] = deepcopy(value)

    return normalized


def _migrate_catalog(raw_catalog: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_catalog, dict):
        raise ModelCatalogError("Catalog root must be a JSON object.")

    cards_raw = raw_catalog.get("vision_models")
    if not isinstance(cards_raw, list):
        raise ModelCatalogError("'vision_models' must be a list.")

    normalized_cards = [_normalize_card_v2(card if isinstance(card, dict) else {}) for card in cards_raw]

    raw_schema_version = str(raw_catalog.get("schema_version") or "").strip() or "1.0"
    if raw_schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ModelCatalogError(
            f"Unsupported catalog schema_version '{raw_schema_version}'. "
            f"Expected one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}."
        )

    catalog = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "provider": str(raw_catalog.get("provider") or "venice.ai"),
        "catalog_version": str(raw_catalog.get("catalog_version") or "unknown"),
        "strategy": str(raw_catalog.get("strategy") or "default"),
        "last_updated": str(raw_catalog.get("last_updated") or raw_catalog.get("catalog_version") or "unknown"),
        "default_task_type": _normalize_task_type(str(raw_catalog.get("default_task_type") or "general_vision")),
        "supported_task_types": [
            _normalize_task_type(str(task))
            for task in raw_catalog.get("supported_task_types", sorted(SUPPORTED_TASK_TYPES))
            if _normalize_task_type(str(task)) in SUPPORTED_TASK_TYPES
        ],
        "vision_models": normalized_cards,
    }

    if not catalog["supported_task_types"]:
        catalog["supported_task_types"] = sorted(SUPPORTED_TASK_TYPES)

    if catalog["default_task_type"] not in SUPPORTED_TASK_TYPES:
        catalog["default_task_type"] = "general_vision"

    catalog["supported_task_types"] = list(dict.fromkeys(catalog["supported_task_types"]))

    _validate_catalog(catalog)
    return catalog


def _validate_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise ModelCatalogError(
            f"Unsupported catalog schema_version '{catalog.get('schema_version')}'. "
            f"Expected '{CATALOG_SCHEMA_VERSION}'."
        )

    _ensure_string(catalog.get("provider"), "provider")
    _ensure_string(catalog.get("catalog_version"), "catalog_version")
    _ensure_string(catalog.get("last_updated"), "last_updated")

    default_task_type = _normalize_task_type(_ensure_string(catalog.get("default_task_type"), "default_task_type"))
    if default_task_type not in SUPPORTED_TASK_TYPES:
        raise ModelCatalogError(f"Invalid default_task_type '{default_task_type}'.")

    supported_task_types = _ensure_string_list(catalog.get("supported_task_types"), "supported_task_types")
    normalized_supported = [_normalize_task_type(task) for task in supported_task_types]
    unknown = [task for task in normalized_supported if task not in SUPPORTED_TASK_TYPES]
    if unknown:
        raise ModelCatalogError(f"Unsupported task types in catalog: {', '.join(sorted(set(unknown)))}")

    cards = catalog.get("vision_models")
    if not isinstance(cards, list) or not cards:
        raise ModelCatalogError("Catalog must include a non-empty 'vision_models' list.")

    seen_ids: set[str] = set()
    for card in cards:
        card_id = _ensure_string(card.get("id"), "id")
        if card_id in seen_ids:
            raise ModelCatalogError(f"Duplicate model id detected: '{card_id}'.")
        seen_ids.add(card_id)


def _resolve_catalog_path(catalog_path: Optional[str | Path]) -> Path:
    if catalog_path is not None:
        return Path(catalog_path).expanduser().resolve()

    configured = os.getenv("PERCIVAL_VISION_MCP_MODEL_CATALOG_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    return _default_catalog_path()


@lru_cache(maxsize=8)
def _load_catalog_cached(path_str: str) -> dict[str, Any]:
    catalog_path = Path(path_str)
    if not catalog_path.exists():
        raise ModelCatalogError(f"Model catalog file not found: {catalog_path}")

    try:
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelCatalogError(f"Invalid JSON in model catalog '{catalog_path}': {exc}") from exc

    return _migrate_catalog(raw_catalog)


def clear_catalog_cache() -> None:
    _load_catalog_cached.cache_clear()


def load_catalog(catalog_path: Optional[str | Path] = None, use_cache: bool = True) -> dict[str, Any]:
    resolved_path = _resolve_catalog_path(catalog_path)
    if use_cache:
        return deepcopy(_load_catalog_cached(str(resolved_path)))

    clear_catalog_cache()
    return deepcopy(_load_catalog_cached(str(resolved_path)))


def list_model_cards(
    task_type: Optional[str] = None,
    include_inactive: bool = False,
    catalog: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    active_catalog = catalog or load_catalog()
    cards = active_catalog.get("vision_models", [])

    normalized_task = _normalize_task_type(task_type) if task_type else None
    if normalized_task and normalized_task not in SUPPORTED_TASK_TYPES:
        raise ModelCatalogError(f"Unsupported task_type '{task_type}'.")

    filtered: list[dict[str, Any]] = []
    for card in cards:
        if not include_inactive and card.get("status") != "active":
            continue

        card_tasks = card.get("task_types", [])
        if normalized_task and normalized_task not in card_tasks:
            continue

        filtered.append(deepcopy(card))

    return filtered


def get_model_card(model_id: str, catalog: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    lookup_id = (model_id or "").strip()
    if not lookup_id:
        raise ModelCatalogError("model_id must be a non-empty string.")

    active_catalog = catalog or load_catalog()
    for card in active_catalog.get("vision_models", []):
        if card.get("id") == lookup_id:
            return deepcopy(card)
        aliases = card.get("aliases", [])
        if lookup_id in aliases:
            return deepcopy(card)

    return None


def _cost_rank(value: str) -> int:
    return {
        "low": 1,
        "moderate": 2,
        "high": 3,
        "unknown": 4,
    }.get(value, 4)


def _quality_rank(value: str) -> int:
    return {
        "entry": 1,
        "standard": 2,
        "pro": 3,
        "premium": 4,
    }.get(value, 0)


def _speed_rank(value: str) -> int:
    return {
        "slow": 1,
        "balanced": 2,
        "fast": 3,
    }.get(value, 0)


def find_alternatives(
    model_id: str,
    task_type: Optional[str] = None,
    max_results: int = 3,
    include_inactive: bool = False,
    catalog: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    if max_results < 1:
        return []

    active_catalog = catalog or load_catalog()
    current = get_model_card(model_id, catalog=active_catalog)

    if task_type:
        normalized_task = _normalize_task_type(task_type)
        if normalized_task not in SUPPORTED_TASK_TYPES:
            raise ModelCatalogError(f"Unsupported task_type '{task_type}'.")
    elif current and current.get("task_types"):
        normalized_task = str(current["task_types"][0])
    else:
        normalized_task = str(active_catalog.get("default_task_type") or "general_vision")

    candidates = list_model_cards(
        task_type=normalized_task,
        include_inactive=include_inactive,
        catalog=active_catalog,
    )

    current_privacy = None
    if current:
        current_privacy = str((current.get("capabilities") or {}).get("privacy_tier") or "")

    ranked: list[tuple[int, int, int, int, str, dict[str, Any]]] = []
    for card in candidates:
        if card.get("id") == model_id:
            continue

        privacy_tier = str((card.get("capabilities") or {}).get("privacy_tier") or "")
        privacy_bonus = 1 if current_privacy and privacy_tier == current_privacy else 0
        quality_score = _quality_rank(str(card.get("quality_tier") or ""))
        speed_score = _speed_rank(str(card.get("speed_tier") or ""))
        cost_score = _cost_rank(str(card.get("cost_estimation") or "unknown"))

        ranked.append(
            (
                -privacy_bonus,
                -quality_score,
                -speed_score,
                cost_score,
                str(card.get("id") or ""),
                card,
            )
        )

    ranked.sort(key=lambda item: item[:5])
    return [deepcopy(item[5]) for item in ranked[:max_results]]


def get_catalog_metadata(catalog: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    active_catalog = catalog or load_catalog()
    return {
        "schema_version": active_catalog.get("schema_version"),
        "provider": active_catalog.get("provider"),
        "catalog_version": active_catalog.get("catalog_version"),
        "last_updated": active_catalog.get("last_updated"),
        "default_task_type": active_catalog.get("default_task_type"),
        "supported_task_types": list(active_catalog.get("supported_task_types", [])),
        "model_count": len(active_catalog.get("vision_models", [])),
    }
