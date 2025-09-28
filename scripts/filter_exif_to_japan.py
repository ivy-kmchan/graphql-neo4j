#!/usr/bin/env python3
"""Filter EXIF JSON entries to those within Japan's bounding box."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

DEFAULT_SOURCE = Path("data/photos/all_exif.json")
DEFAULT_OUTPUT = Path("data/photos/japan_exif.json")

# Rough bounding box covering Japan (same as we used for saved places).
JAPAN_BOUNDS = {
    "min_lat": 20.214581,
    "max_lat": 45.711204,
    "min_lon": 122.93457,
    "max_lon": 154.205541,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter EXIF JSON to entries within Japan bounds.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Input EXIF JSON file")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write the filtered JSON"
    )
    parser.add_argument(
        "--bounds",
        nargs=4,
        metavar=("MIN_LAT", "MAX_LAT", "MIN_LON", "MAX_LON"),
        type=float,
        help="Override bounding box (latitudes then longitudes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show counts without writing the output file",
    )
    return parser.parse_args()


def load_entries(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("EXIF JSON must contain a list of objects")
    return data


def in_bounds(entry: Dict[str, Any], bounds: Dict[str, float]) -> bool:
    lat = entry.get("GPSLatitude")
    lon = entry.get("GPSLongitude")
    if lat is None or lon is None:
        return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False
    return (
        bounds["min_lat"] <= lat_f <= bounds["max_lat"]
        and bounds["min_lon"] <= lon_f <= bounds["max_lon"]
    )


def main() -> None:
    args = parse_args()
    bounds = dict(JAPAN_BOUNDS)
    if args.bounds:
        bounds.update(
            {
                "min_lat": args.bounds[0],
                "max_lat": args.bounds[1],
                "min_lon": args.bounds[2],
                "max_lon": args.bounds[3],
            }
        )

    entries = list(load_entries(args.source))
    filtered = [entry for entry in entries if in_bounds(entry, bounds)]

    print(f"Total entries: {len(entries)}")
    print(f"Entries within bounds: {len(filtered)}")

    if args.dry_run:
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(filtered, fh, ensure_ascii=False, indent=2)
    print(f"Filtered entries written to {args.output}")


if __name__ == "__main__":
    main()
