#!/usr/bin/env python3
"""Normalize missing country codes for SavedPlaces features using coordinate bounds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

# Default bounding box covering Japan (main islands + remote territories).
DEFAULT_JAPAN_BOUNDS = {
    "min_lat": 20.214581,
    "max_lat": 45.711204,
    "min_lon": 122.93457,
    "max_lon": 154.205541,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill missing country codes based on coordinate bounds.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/GoogleMaps/SavedPlaces.json"),
        help="GeoJSON file to update in place.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the updated GeoJSON. Defaults to overwriting the source file.",
    )
    parser.add_argument(
        "--target-country",
        default="JP",
        help="Country code to assign when coordinates fall within the bounds.",
    )
    parser.add_argument(
        "--bounds",
        nargs=4,
        metavar=("MIN_LAT", "MAX_LAT", "MIN_LON", "MAX_LON"),
        type=float,
        help="Override the default bounding box (latitudes then longitudes).",
    )
    parser.add_argument(
        "--url-substring",
        action="append",
        default=[],
        help="Assign target country when google_maps_url contains the given substring (case-insensitive).",
    )
    parser.add_argument(
        "--address-substring",
        action="append",
        default=[],
        help="Assign target country when the saved place address contains the given substring (case-insensitive).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many features would be updated without writing changes.",
    )
    return parser.parse_args()


def load_geojson(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_geojson(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


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


def matches_hints(
    feature: Dict[str, Any],
    url_hints: Iterable[str],
    address_hints: Iterable[str],
) -> bool:
    properties = feature.get("properties", {})
    url = (properties.get("google_maps_url") or "").lower()
    if url_hints and any(h.lower() in url for h in url_hints):
        return True

    address = (
        feature.get("properties", {})
        .get("location", {})
        .get("address")
        or ""
    ).lower()
    if address_hints and any(h.lower() in address for h in address_hints):
        return True

    return False


def should_update(
    feature: Dict[str, Any],
    bounds: Dict[str, float],
    url_hints: Iterable[str],
    address_hints: Iterable[str],
) -> bool:
    location = feature.get("properties", {}).get("location", {})
    code = (location.get("country_code") or "").strip()
    if code:
        return False
    lon, lat = feature_coordinates(feature)
    if lon is None or lat is None:
        return matches_hints(feature, url_hints, address_hints)
    if in_bounds(lon, lat, bounds):
        return True
    return matches_hints(feature, url_hints, address_hints)


def update_features(
    features: Iterable[Dict[str, Any]],
    bounds: Dict[str, float],
    target_code: str,
    url_hints: Iterable[str],
    address_hints: Iterable[str],
) -> Tuple[int, int]:
    total_missing = 0
    updated = 0

    for feature in features:
        location = feature.setdefault("properties", {}).setdefault("location", {})
        code = (location.get("country_code") or "").strip()
        if not code:
            total_missing += 1
            if should_update(feature, bounds, url_hints, address_hints):
                location["country_code"] = target_code
                updated += 1

    return total_missing, updated


def main() -> None:
    args = parse_args()
    bounds = dict(DEFAULT_JAPAN_BOUNDS)
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

    total_missing, updated = update_features(
        features,
        bounds,
        args.target_country,
        args.url_substring,
        args.address_substring,
    )

    print(
        (
            f"Features inspected: {len(features)}\n"
            f"Missing country_code before update: {total_missing}\n"
            f"Updated to {args.target_country}: {updated}"
        )
    )

    if args.dry_run:
        return

    output_path = args.output or args.source
    save_geojson(output_path, data)
    print(f"Written updated GeoJSON to {output_path}")


if __name__ == "__main__":
    main()
