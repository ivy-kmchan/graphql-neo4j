#!/usr/bin/env python3
"""CLI helper to review zero-coordinate saved places."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CATEGORY_CHOICES = ["place", "region"]
LIST_CHOICES = ["star", "heart", "hotel", "want_to_go"]

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
        "--report",
        action="store_true",
        help="Print the completeness report before starting the review",
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


def feature_lookup(features: List[Dict[str, Any]], maps_url: str | None) -> Dict[str, Any] | None:
    if not maps_url:
        return None
    for feature in features:
        props = feature.get("properties", {})
        if props.get("google_maps_url") == maps_url:
            return props
    return None


def prompt_choice(prompt: str, options: List[str], current: str | None = None) -> str | None:
    print(prompt)
    for idx, option in enumerate(options, start=1):
        marker = " (current)" if option == current else ""
        print(f"    {idx}. {option}{marker}")
    raw = input("  Enter number (blank to cancel): ").strip()
    if not raw:
        return None
    if not raw.isdigit():
        print("  Invalid input; expected a number.")
        return None
    index = int(raw)
    if not 1 <= index <= len(options):
        print("  Invalid choice; out of range.")
        return None
    return options[index - 1]


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

    if args.report:
        report_path = Path(__file__).with_name("data_completeness_report.py")
        if report_path.exists():
            import runpy

            print("Running completeness report...\n")
            runpy.run_path(str(report_path))
            print()
        else:
            print("Warning: data_completeness_report.py not found; skipping report.\n")

    print(
        "Interactive review starting. Commands: [d]elete, [r]ename, [c]ategory, [l]ist, [p]refecture, [o]tes, [v]isited, [t]visited date, [g]rating, [n]ext, [q]uit"
    )
    print("-----------------------------------------------------------")
    quit_requested = False

    for idx, item in enumerate(review_items, start=1):
        while True:
            base_name, base_address, maps_url = normalise_entry(item)
            props = feature_lookup(features, maps_url)

            if props:
                location = props.get("location", {})
            elif isinstance(item, dict) and "properties" in item:
                props = item.get("properties", {})
                location = props.get("location", {})
            else:
                props = {}
                location = {}

            name_display = location.get("name") or base_name or "<Unnamed>"
            address_display = location.get("address") or base_address or "<No address>"
            link_display = maps_url or "<No link available>"
            category_display = props.get("category") or "<unset>"
            list_display = props.get("saved_list") or "<unset>"
            prefecture_display = props.get("prefecture") or "<unset>"
            notes_display = props.get("notes") or "<none>"
            visited_value = props.get("visited")
            visited_label = "<unset>"
            if visited_value is True:
                visited_label = "yes"
            elif visited_value is False:
                visited_label = "no"
            visited_date_display = props.get("visited_date") or "<unset>"
            rating_display = props.get("tabelog_rating") or "<unset>"

            print(f"[{idx}/{len(review_items)}]")
            print(f"  Name    : {name_display}")
            print(f"  Address : {address_display}")
            print(f"  Map link: {link_display}")
            print(f"  Category: {category_display}")
            print(f"  List type: {list_display}")
            print(f"  Prefecture: {prefecture_display}")
            print(f"  Notes: {notes_display}")
            print(f"  Visited: {visited_label}")
            print(f"  Visited date: {visited_date_display}")
            print(f"  Tabelog rating: {rating_display}\n")

            choice = input(
                "Action ([d]elete/[r]ename/[c]ategory/[l]ist/[p]refecture/[o]tes/[v]isited/[t]visited date/[g]rating/[n]ext/[q]uit): "
            ).strip().lower()
            if choice not in {"d", "r", "c", "l", "p", "o", "v", "t", "g", "n", "q"}:
                print("Invalid choice. Please enter one of the listed options.")
                continue

            if choice == "q":
                print("Quitting review.")
                quit_requested = True
                break
            if choice == "n":
                break
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
                break
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
                props_local = feature.setdefault("properties", {})
                location_local = props_local.setdefault("location", {})
                old_name = location_local.get("name")
                location_local["name"] = new_name
                if "properties" in item:
                    item.setdefault("properties", {}).setdefault("location", {})["name"] = new_name
                print(f"  - Renamed '{old_name or '<Unnamed>'}' to '{new_name}'.")
                continue
            if choice == "c":
                if maps_url is None:
                    print("  - Cannot set category: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping category update.")
                    continue
                new_category = prompt_choice(
                    "  Select category",
                    CATEGORY_CHOICES,
                    current=features[feature_index]["properties"].get("category"),
                )
                if new_category is None:
                    print("  - Category update cancelled.")
                    continue
                features[feature_index]["properties"]["category"] = new_category
                print(f"  - Category set to '{new_category}'.")
                continue
            if choice == "l":
                if maps_url is None:
                    print("  - Cannot set list type: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping list update.")
                    continue
                new_list = prompt_choice(
                    "  Select list type",
                    LIST_CHOICES,
                    current=features[feature_index]["properties"].get("saved_list"),
                )
                if new_list is None:
                    print("  - List update cancelled.")
                    continue
                features[feature_index]["properties"]["saved_list"] = new_list
                print(f"  - List type set to '{new_list}'.")
                continue
            if choice == "p":
                if maps_url is None:
                    print("  - Cannot set prefecture: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping prefecture update.")
                    continue
                new_pref = input("  Enter prefecture (blank to clear): ").strip()
                features[feature_index]["properties"]["prefecture"] = new_pref or None
                if "properties" in item:
                    item.setdefault("properties", {})["prefecture"] = new_pref or None
                print("  - Prefecture updated.")
                continue
            if choice == "o":
                if maps_url is None:
                    print("  - Cannot set notes: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping notes update.")
                    continue
                new_notes = input("  Enter notes (blank to clear): ").strip()
                features[feature_index]["properties"]["notes"] = new_notes or None
                if "properties" in item:
                    item.setdefault("properties", {})["notes"] = new_notes or None
                print("  - Notes updated.")
                continue
            if choice == "v":
                if maps_url is None:
                    print("  - Cannot set visited flag: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping visited update.")
                    continue
                resp = input("  Visited? (y/n/blank to unset): ").strip().lower()
                if resp == "y":
                    value = True
                elif resp == "n":
                    value = False
                elif resp == "":
                    value = None
                else:
                    print("  - Invalid response; keeping previous value.")
                    continue
                features[feature_index]["properties"]["visited"] = value
                if "properties" in item:
                    item.setdefault("properties", {})["visited"] = value
                print("  - Visited flag updated.")
                continue
            if choice == "t":
                if maps_url is None:
                    print("  - Cannot set visited date: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping visited date update.")
                    continue
                new_date = input("  Enter visited date (ISO format, blank to clear): ").strip()
                features[feature_index]["properties"]["visited_date"] = new_date or None
                if "properties" in item:
                    item.setdefault("properties", {})["visited_date"] = new_date or None
                print("  - Visited date updated.")
                continue
            if choice == "g":
                if maps_url is None:
                    print("  - Cannot set Tabelog rating: missing Google Maps URL.")
                    continue
                feature_index = find_feature_index(features, maps_url)
                if feature_index is None:
                    print("  - Warning: feature not found; skipping rating update.")
                    continue
                new_rating = input("  Enter Tabelog rating (blank to clear): ").strip()
                features[feature_index]["properties"]["tabelog_rating"] = new_rating or None
                if "properties" in item:
                    item.setdefault("properties", {})["tabelog_rating"] = new_rating or None
                print("  - Tabelog rating updated.")
                continue

        if quit_requested:
            break

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
