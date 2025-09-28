#!/usr/bin/env python3
"""Ensure SavedPlaces features have category and list metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_FILE = Path("data/GoogleMaps/SavedPlaces.json")


def load_geojson(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_geojson(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def main() -> None:
    path = DEFAULT_FILE
    if not path.exists():
        raise SystemExit(f"Missing SavedPlaces file at {path}")

    data = load_geojson(path)
    features = data.get("features", [])

    updated = 0
    for feature in features:
        props = feature.setdefault("properties", {})

        # Saved list type corresponds to the Google list this feature came from.
        if "saved_list" not in props:
            props["saved_list"] = "star"
            updated += 1

        # Category differentiates point-of-interest vs broader region.
        if "category" not in props:
            props["category"] = "place"
            updated += 1

        # Prefecture is an app-managed geographic field (default unknown).
        if "prefecture" not in props:
            props["prefecture"] = None
            updated += 1

        # Notes allow free-form annotations.
        if "notes" not in props:
            props["notes"] = None
            updated += 1

        # Visited flag (bool/None) and visited_date (ISO string or None).
        if "visited" not in props:
            props["visited"] = None
            updated += 1
        if "visited_date" not in props:
            props["visited_date"] = None
            updated += 1

        # Tabelog rating (float/string) primarily for food/hotel entries.
        if "tabelog_rating" not in props:
            props["tabelog_rating"] = None
            updated += 1

    if updated:
        save_geojson(path, data)
        print(f"Updated {path} with {updated} new metadata fields")
    else:
        print("No updates required; metadata already present")


if __name__ == "__main__":
    main()
