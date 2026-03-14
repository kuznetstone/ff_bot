from __future__ import annotations

from typing import List, Dict, Any

SPECIALISTS = [
    {"id": 1, "name": "Марина"},
    {"id": 2, "name": "Елизавета"},
    {"id": 3, "name": "Ирина"},
    {"id": 4, "name": "Татьяна"},
]


def get_specialists(allowed_names: List[str] | None = None) -> List[Dict[str, Any]]:
    if not allowed_names:
        return SPECIALISTS.copy()
    return [s for s in SPECIALISTS if s["name"] in allowed_names]


def get_specialist_by_id(spec_id: int) -> Dict[str, Any] | None:
    for spec in SPECIALISTS:
        if spec["id"] == spec_id:
            return spec
    return None
