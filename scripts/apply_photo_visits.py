#!/usr/bin/env python3
"""Populate visited metadata based on photo matches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

PLACES_DEFAULT = Path("data/GoogleMaps/SavedPlaces.json")
MATCHES_DEFAULT = Path("data/photos/place_photo_matches.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark places as visited using photo match data.")
    parser.add_argument("--places", type=Path, default=PLACES_DEFAULT, help="SavedPlaces JSON file")
    parser.add_argument(
        "--matches", type=Path, default=MATCHES_DEFAULT, help="Photo-place match JSON file"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing visited/visited_date values (default: only fill blanks)",
    )
    parser.add_argument(
        "--append-note",
        action="store_true",
        help="Append a short note (or replace empty notes) summarising photo evidence.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing output")
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_match_lookup(matches: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for entry in matches.get("matches", []):
        place = entry.get("place", {})
        key = place.get("google_maps_url") or place.get("name")
        if not key:
            continue
        photos = entry.get("photos", [])
        if not photos:
            continue
        timestamps = [p.get("timestamp") for p in photos if p.get("timestamp")]
        summary = {
            "count": len(photos),
            "earliest": min(timestamps) if timestamps else None,
            "latest": max(timestamps) if timestamps else None,
        }
        lookup[key] = summary
    return lookup


def apply(matches_lookup: Dict[str, Dict[str, Any]], data: Dict[str, Any], force: bool, append_note: bool) -> Dict[str, int]:
    stats = {"visited_set": 0, "date_set": 0, "notes_appended": 0}

    for feature in data.get("features", []):
        props = feature.setdefault("properties", {})
        location = props.get("location", {})
        key = props.get("google_maps_url") or location.get("name")
        if not key or key not in matches_lookup:
            continue
        summary = matches_lookup[key]
        if not summary.get("earliest"):
            continue

        if force or props.get("visited") is None:
            if props.get("visited") is not True:
                props["visited"] = True
                stats["visited_set"] += 1
        if summary.get("earliest") and (force or not props.get("visited_date")):
            props["visited_date"] = summary["earliest"]
            stats["date_set"] += 1
        if append_note and summary.get("count"):
            note = f"Photos: {summary['count']} (range {summary.get('earliest')} – {summary.get('latest')})"
            existing = props.get("notes")
            if existing:
                if note not in existing:
                    props["notes"] = f"{existing}\n{note}"
                    stats["notes_appended"] += 1
            else:
                props["notes"] = note
                stats["notes_appended"] += 1

    return stats


def main() -> None:
    args = parse_args()
    places_data = load_json(args.places)
    matches_data = load_json(args.matches)

    lookup = build_match_lookup(matches_data)
    stats = apply(lookup, places_data, force=args.force, append_note=args.append_note)

    print(
        f"Visited flags set: {stats['visited_set']}, visited_date set: {stats['date_set']}, "
        f"notes updated: {stats['notes_appended']}"
    )

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    save_json(args.places, places_data)
    print(f"Saved updates to {args.places}")


if __name__ == "__main__":
    main()
