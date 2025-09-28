#!/usr/bin/env python3
"""Generate a quick data-quality report for SavedPlaces."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SOURCE = Path("data/GoogleMaps/SavedPlaces.json")


def load_data(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"SavedPlaces file not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def is_valid_coords(coords) -> bool:
    return (
        isinstance(coords, list)
        and len(coords) == 2
        and isinstance(coords[0], (int, float))
        and isinstance(coords[1], (int, float))
        and not (coords[0] == 0 and coords[1] == 0)
    )


def main() -> None:
    data = load_data(SOURCE)
    features = data.get("features", [])
    total = len(features)

    missing = Counter()
    category_dist = Counter()
    list_dist = Counter()

    for feature in features:
        props = feature.get("properties", {})
        location = props.get("location", {})
        coords = feature.get("geometry", {}).get("coordinates")

        if not (location.get("name") or "").strip():
            missing["name"] += 1
        if not (location.get("address") or "").strip():
            missing["address"] += 1
        if not is_valid_coords(coords):
            missing["coordinates"] += 1
        if not (props.get("date") or "").strip():
            missing["date"] += 1
        if not (props.get("google_maps_url") or "").strip():
            missing["google_maps_url"] += 1
        if not (props.get("prefecture") or "").strip():
            missing["prefecture"] += 1
        if props.get("notes") in (None, ""):
            missing["notes"] += 1
        if props.get("visited") is None:
            missing["visited"] += 1
        if not (props.get("visited_date") or "").strip():
            missing["visited_date"] += 1
        if props.get("tabelog_rating") in (None, ""):
            missing["tabelog_rating"] += 1

        category = props.get("category")
        saved_list = props.get("saved_list")

        if not (category or "").strip():
            missing["category"] += 1
        else:
            category_dist[category] += 1

        if not (saved_list or "").strip():
            missing["saved_list"] += 1
        else:
            list_dist[saved_list] += 1

    print(f"SavedPlaces completeness report (total features: {total})")
    print("-" * 60)
    fields = [
        "name",
        "address",
        "coordinates",
        "date",
        "google_maps_url",
        "prefecture",
        "notes",
        "visited",
        "visited_date",
        "tabelog_rating",
        "category",
        "saved_list",
    ]

    for field in fields:
        count_missing = missing.get(field, 0)
        pct = (count_missing / total * 100) if total else 0
        print(f"Field '{field:15}': missing {count_missing:4} ({pct:5.2f}%)")

    print("\nCategory distribution:")
    for key, count in category_dist.most_common():
        pct = (count / total * 100) if total else 0
        print(f"  {key or '<unset>':15} {count:4} ({pct:5.2f}%)")
    if not category_dist:
        print("  <no categories set>")

    print("\nSaved list distribution:")
    for key, count in list_dist.most_common():
        pct = (count / total * 100) if total else 0
        print(f"  {key or '<unset>':15} {count:4} ({pct:5.2f}%)")
    if not list_dist:
        print("  <no saved_list values set>")


if __name__ == "__main__":
    main()
