"""
Location normalization packages.
"""
from backend.app.locations.india_locations import (
    INDIAN_TECH_HUBS,
    normalize_location,
    matches_location_preference
)

__all__ = ["INDIAN_TECH_HUBS", "normalize_location", "matches_location_preference"]
