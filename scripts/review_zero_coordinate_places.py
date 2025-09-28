#!/usr/bin/env python3
"""CLI helper to review zero-coordinate saved places."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_SOURCE = Path("data/GoogleMaps/SavedPlacesZeroCoords.json")
SAVED_PLACES_PATH = Path("data/GoogleMaps/SavedPlaces.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review zero-coordinate saved places interactively.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="JSON file listing the zero-coordinate entries to review.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=SAVED_PLACES_PATH,
        help="Main SavedPlaces JSON file to modify when deleting entries.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write any changes to the data file.",
    )
    parser.add_argument(
        "--refresh-zero-list",
        action="store_true",
        default=True,
        help="Refresh the zero-coordinate list file after processing (default: on).",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def normalise_entry(item: Dict[str, Any]) -> Tuple[str | None, str | None, str | None]:
    """Return (name, address, maps_url) from either a flattened dict or raw feature."""

    if "properties" in item:
        props = item.get("properties", {})
        location = props.get("location", {})
        return (
            location.get("name"),
            location.get("address"),
            props.get("google_maps_url"),
        )

    return (
        item.get("name"),
        item.get("address"),
        item.get("maps_url"),
    )


def find_feature_index(features: List[Dict[str, Any]], maps_url: str | None) -> int | None:
    if not maps_url:
        return None
    for idx, feature in enumerate(features):
        if feature.get("properties", {}).get("google_maps_url") == maps_url:
            return idx
    return None


def main() -> None:
    args = parse_args()

    review_items = load_json(args.source)
    main_data = load_json(args.data)
    features = main_data.get("features", [])

    if not review_items:
        print("No entries to review.")
        return

    print("Interactive review starting. Commands: [d]elete, [r]ename, [n]ext, [q]uit")
    print("-----------------------------------------------------------")

    for idx, item in enumerate(review_items, start=1):
        name, address, maps_url = normalise_entry(item)
        name_display = name or "<Unnamed>"
        address_display = address or "<No address>"
        link_display = maps_url or "<No link available>"

        print(f"[{idx}/{len(review_items)}]")
        print(f"  Name    : {name_display}")
        print(f"  Address : {address_display}")
        print(f"  Map link: {link_display}\n")

        while True:
            choice = input("Action ([d]elete/[r]ename/[n]ext/[q]uit): ").strip().lower()
            if choice in {"d", "r", "n", "q"}:
                break
            print("Invalid choice. Please enter d, r, n, or q.")

        if choice == "q":
            print("Quitting review.")
            break
        if choice == "n":
            continue
        if choice == "d":
            feature_index = find_feature_index(features, maps_url)
            if feature_index is None:
                print("  - Warning: corresponding feature not found in dataset; skipping delete.")
                continue
            removed_feature = features.pop(feature_index)
            print(f"  - Deleted feature with URL: {maps_url}")
            if args.dry_run:
                features.insert(feature_index, removed_feature)
                print("    (dry-run) change not persisted.")
            continue
        if choice == "r":
            if maps_url is None:
                print("  - Cannot rename: no Google Maps URL available to locate feature.")
                continue
            feature_index = find_feature_index(features, maps_url)
            if feature_index is None:
                print("  - Warning: corresponding feature not found in dataset; skipping rename.")
                continue

            new_name = input("  New name (leave blank to cancel): ").strip()
            if not new_name:
                print("  - Rename cancelled.")
                continue

            feature = features[feature_index]
            props = feature.setdefault("properties", {})
            location = props.setdefault("location", {})
            old_name = location.get("name")
            location["name"] = new_name
            print(f"  - Renamed '{old_name or '<Unnamed>'}' to '{new_name}'.")
            continue

    if not args.dry_run:
        main_data["features"] = features
        save_json(args.data, main_data)
        print(f"Saved updates to {args.data}")
    else:
        print("Dry-run mode; no changes saved.")

    if args.refresh_zero_list and not args.dry_run:
        zero_features = [
            feature
            for feature in features
            if feature.get("geometry", {}).get("coordinates") == [0, 0]
        ]
        save_json(args.source, zero_features)
        print(f"Refreshed zero-coordinate list at {args.source}")
    elif args.refresh_zero_list and args.dry_run:
        print("(dry-run) Skipped refreshing zero-coordinate list.")


if __name__ == "__main__":
    main()
