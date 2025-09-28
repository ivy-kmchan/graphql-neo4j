#!/usr/bin/env python3
"""Classify saved Google Maps places by whether their coordinates fall within Japan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

# Coordinates for the rectangular extent that covers Japan's main islands and outlying territories.
JAPAN_BOUNDS = {
    "min_lat": 20.214581,  # Yonaguni Island (Okinawa, southernmost point)
    "max_lat": 45.711204,  # Cape Sōya (Hokkaido, northernmost point)
    "min_lon": 122.93457,  # Yonaguni Island (westernmost point)
    "max_lon": 154.205541,  # Minamitorishima (easternmost point)
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split a SavedPlaces GeoJSON file into entries whose coordinates fall inside "
            "Japan's bounding box and those that do not."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/GoogleMaps/SavedPlaces.json"),
        help="Path to the SavedPlaces GeoJSON export from Google Takeout.",
    )
    parser.add_argument(
        "--output-japan",
        type=Path,
        default=Path("data/GoogleMaps/SavedPlacesJapanByCoords.json"),
        help="Where to write features whose coordinates fall within the Japan bounds.",
    )
    parser.add_argument(
        "--output-elsewhere",
        type=Path,
        default=Path("data/GoogleMaps/SavedPlacesOutsideJapan.json"),
        help="Where to write features whose coordinates fall outside the Japan bounds.",
    )
    parser.add_argument(
        "--bounds",
        nargs=4,
        metavar=("MIN_LAT", "MAX_LAT", "MIN_LON", "MAX_LON"),
        type=float,
        help=(
            "Override the default bounding box (latitudes then longitudes). "
            "Useful if you want to narrow or expand the definition of 'Japan'."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; just print a summary of how many features fall inside/outside.",
    )
    return parser.parse_args()


def load_geojson(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_geojson(path: Path, features: Iterable[Dict[str, Any]]) -> None:
    data = {"type": "FeatureCollection", "features": list(features)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def feature_coordinates(feature: Dict[str, Any]) -> Tuple[float | None, float | None]:
    coords = feature.get("geometry", {}).get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        return None, None
    lon, lat = coords
    if isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
        return float(lon), float(lat)
    return None, None


def in_bounds(lon: float, lat: float, bounds: Dict[str, float]) -> bool:
    return (
        bounds["min_lon"] <= lon <= bounds["max_lon"]
        and bounds["min_lat"] <= lat <= bounds["max_lat"]
    )


def classify_features(
    features: Iterable[Dict[str, Any]],
    bounds: Dict[str, float],
) -> Tuple[list[Dict[str, Any]], list[Dict[str, Any]], list[Dict[str, Any]]]:
    inside: list[Dict[str, Any]] = []
    outside: list[Dict[str, Any]] = []
    missing_coords: list[Dict[str, Any]] = []

    for feature in features:
        lon, lat = feature_coordinates(feature)
        if lon is None or lat is None:
            missing_coords.append(feature)
            continue
        target = inside if in_bounds(lon, lat, bounds) else outside
        target.append(feature)

    return inside, outside, missing_coords


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

    data = load_geojson(args.source)
    features = data.get("features", [])

    inside, outside, missing = classify_features(features, bounds)

    print(
        (
            f"Total features: {len(features)}\n"
            f"Inside bounds: {len(inside)}\n"
            f"Outside bounds: {len(outside)}\n"
            f"Missing/invalid coordinates: {len(missing)}"
        )
    )

    if args.dry_run:
        return

    save_geojson(args.output_japan, inside)
    save_geojson(args.output_elsewhere, outside + missing)


if __name__ == "__main__":
    main()
