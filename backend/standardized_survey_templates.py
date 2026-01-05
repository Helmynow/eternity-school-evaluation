"""
Standardized survey templates for parent/staff benchmarking and rotation.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

STANDARDIZED_SURVEYS_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "surveys" / "standardized_surveys.json"
)


@lru_cache(maxsize=1)
def load_standardized_survey_bundle() -> Dict[str, Any]:
    """Load the standardized survey bundle from disk (cached)."""
    with STANDARDIZED_SURVEYS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_standardized_surveys(
    *,
    audience: Optional[str] = None,
    term_type: Optional[str] = None,
    name: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
    """Return standardized surveys filtered by audience/term/name."""
    bundle = load_standardized_survey_bundle()
    surveys = bundle.get("surveys", [])

    def _matches(value: Optional[str], target: Optional[str]) -> bool:
        if value is None or target is None:
            return True
        return str(value).strip().lower() == str(target).strip().lower()

    filtered = [
        survey
        for survey in surveys
        if _matches(survey.get("audience"), audience)
        and _matches(survey.get("term_type"), term_type)
        and _matches(survey.get("name"), name)
    ]

    if name:
        return filtered[0] if filtered else None

    return {
        "surveys": filtered,
        "rotation_calendar": bundle.get("rotation_calendar", {}),
    }


def score_standardized_survey_responses(
    survey: Dict[str, Any], responses: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Compute weighted scores for a standardized survey using question weights.

    Responses can be:
      - dict mapping question text -> value
      - list of {"text": "...", "value": ...} objects
    """
    response_map = _normalize_response_map(responses)
    section_scores: Dict[str, Dict[str, float]] = {}
    total_weight = 0.0
    total_weighted = 0.0
    answered_weight = 0.0

    for section in survey.get("sections", []):
        section_name = section.get("name", "Unknown")
        section_weighted = 0.0
        section_total = 0.0
        section_answered = 0.0
        for question in section.get("questions", []):
            weight = float(question.get("weight") or 0.0)
            if weight <= 0:
                continue
            score = _coerce_score(question, response_map.get(question.get("text")))
            section_total += weight
            total_weight += weight
            if score is None:
                continue
            section_weighted += score * weight
            total_weighted += score * weight
            section_answered += weight
            answered_weight += weight

        section_scores[section_name] = {
            "score": (section_weighted / section_total) if section_total > 0 else 0.0,
            "answered_weight": section_answered,
            "total_weight": section_total,
        }

    overall_score = (total_weighted / total_weight) if total_weight > 0 else 0.0
    return {
        "overall_score": overall_score,
        "answered_weight": answered_weight,
        "total_weight": total_weight,
        "section_scores": section_scores,
    }


def _normalize_response_map(
    responses: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    if isinstance(responses, dict):
        return responses
    normalized: Dict[str, Any] = {}
    for item in responses or []:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if text:
            normalized[text] = item.get("value")
    return normalized


def _coerce_score(question: Dict[str, Any], value: Any) -> Optional[float]:
    if value is None:
        return None

    q_type = str(question.get("type") or "").strip().lower()
    if q_type == "likert":
        return _coerce_numeric(value)
    if q_type == "categorical":
        return _coerce_categorical(question.get("options") or [], value)

    return None


def _coerce_numeric(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _coerce_categorical(options: Iterable[str], value: Any) -> Optional[float]:
    numeric = _coerce_numeric(value)
    if numeric is not None:
        return numeric
    if isinstance(value, str):
        normalized = value.strip().lower()
        for index, option in enumerate(options):
            if str(option).strip().lower() == normalized:
                return float(index + 1)
    return None
