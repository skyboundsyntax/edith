"""
Matches job titles to requested roles without accepting generic word overlap.
"""
import re
from typing import Any, Dict

ROLE_ANCHORS = {
    "analyst", "architect", "assistant", "coordinator", "designer", "developer",
    "engineer", "executive", "manager", "officer", "programmer", "representative",
    "specialist", "writer", "dev",
}
ROLE_FILLER = {
    "a", "an", "and", "at", "for", "in", "job", "jobs", "of", "opening",
    "openings", "position", "positions", "role", "roles", "the", "with",
}

ROLE_TITLE_ALIASES = {
    "game developer": (
        r"\b(?:game|gameplay)\s+(?:software\s+)?(?:developer|programmer|engineer|dev)\b",
        r"\b(?:unity|unreal)(?:\s+engine)?\s+(?:developer|programmer|engineer|dev)\b",
    ),
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _matches_role(title: str, role: str) -> bool:
    normalized_title = _normalize(title)
    normalized_role = _normalize(role)
    if not normalized_role:
        return False

    if re.search(r"\b" + re.escape(normalized_role) + r"\b", normalized_title):
        return True

    for canonical_role, aliases in ROLE_TITLE_ALIASES.items():
        if normalized_role == canonical_role and any(
            re.search(pattern, normalized_title) for pattern in aliases
        ):
            return True

    role_words = normalized_role.split()
    qualifiers = [
        word for word in role_words
        if word not in ROLE_FILLER and word not in ROLE_ANCHORS
    ]
    anchors = [word for word in role_words if word in ROLE_ANCHORS]

    if qualifiers:
        return (
            all(re.search(r"\b" + re.escape(word) + r"\b", normalized_title) for word in qualifiers)
            and any(re.search(r"\b" + re.escape(anchor) + r"\b", normalized_title) for anchor in anchors)
        )

    if anchors:
        return any(re.search(r"\b" + re.escape(anchor) + r"\b", normalized_title) for anchor in anchors)

    return normalized_role == "job opening"


def is_matching_role(title: str, query_spec: Dict[str, Any], department: str = "", description: str = "") -> bool:
    """
    Return whether a listing title matches one of the requested roles.

    Department and description are retained in the signature for connector
    compatibility; role relevance is deliberately determined by the title so
    incidental mentions in a description cannot admit an unrelated job.
    """
    if not title:
        return False

    roles = query_spec.get("roles") or []
    if roles:
        return any(_matches_role(title, role) for role in roles)

    keywords = query_spec.get("keywords") or []
    if keywords:
        return any(_matches_role(title, keyword) for keyword in keywords)

    return True
