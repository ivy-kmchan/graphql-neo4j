#!/usr/bin/env python3
"""Backfill missing coordinates from google_maps_url query parameters."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

JAPAN_BOUNDS = {
    "min_lat": 20.214581,
    "max_lat": 45.711204,
    "min_lon": 122.93457,
    "max_lon": 154.205541,
}

COORD_PAIR_REGEX = re.compile(r"(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate missing geometry coordinates from google_maps_url values."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/GoogleMaps/SavedPlaces.json"),
        help="Path to the SavedPlaces GeoJSON file to update.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. When omitted, overwrites the source file.",
    )
    parser.add_argument(
        "--fill-country",
        action="store_true",
        help="When set, assign country_code=JP for coordinates falling within Japan bounds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute statistics without writing any files.",
    )
    return parser.parse_args()


def load_geojson(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_geojson(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def extract_pair(text: str) -> Optional[Tuple[float, float]]:
    match = COORD_PAIR_REGEX.search(text)
    if not match:
        return None
    first = float(match.group(1))
    second = float(match.group(2))

    def in_range(lat: float, lon: float) -> bool:
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    if in_range(first, second):
        return first, second
    if in_range(second, first):
        # Handles the rare case where lon appears before lat in the string.
        return second, first
    return None


def coords_from_url(url: str) -> Optional[Tuple[float, float]]:
    if not url:
        return None
    parsed = urlparse(url)

    # Query string ?q=LAT,LON or &q=
    query_values = parse_qs(parsed.query).get("q", [])
    for raw in query_values:
        decoded = unquote(raw)
        pair = extract_pair(decoded)
        if pair:
            return pair

    # Fragment like @LAT,LON,zoom
    fragment = unquote(parsed.fragment)
    if fragment:
        pair = extract_pair(fragment)
        if pair:
            return pair

    # Path segment sometimes contains @LAT,LON
    path = unquote(parsed.path)
    pair = extract_pair(path)
    if pair:
        return pair

    return None


def in_japan(lon: float, lat: float) -> bool:
    return (
        JAPAN_BOUNDS["min_lon"] <= lon <= JAPAN_BOUNDS["max_lon"]
        and JAPAN_BOUNDS["min_lat"] <= lat <= JAPAN_BOUNDS["max_lat"]
    )


def ensure_geometry(feature: Dict[str, Any]) -> Dict[str, Any]:
    geometry = feature.setdefault("geometry", {})
    geometry.setdefault("type", "Point")
    geometry.setdefault("coordinates", [None, None])
    return geometry


def update_features(
    features: Iterable[Dict[str, Any]],
    fill_country: bool,
) -> Tuple[int, int, int]:
    extracted = 0
    updated_geo = 0
    updated_country = 0

    for feature in features:
        geometry = ensure_geometry(feature)
        coords = geometry.get("coordinates")
        if not (isinstance(coords, list) and len(coords) == 2):
            continue
        lon, lat = coords
        needs_coords = not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)) or (lon == 0 and lat == 0)
        if not needs_coords:
            continue

        url = feature.get("properties", {}).get("google_maps_url") or ""
        pair = coords_from_url(url)
        if not pair:
            continue
        extracted += 1
        lat_v, lon_v = pair
        geometry["coordinates"] = [lon_v, lat_v]
        updated_geo += 1

        location = feature.setdefault("properties", {}).setdefault("location", {})
        country = (location.get("country_code") or "").strip()
        if fill_country and not country and in_japan(lon_v, lat_v):
            location["country_code"] = "JP"
            updated_country += 1

    return extracted, updated_geo, updated_country


def main() -> None:
    args = parse_args()
    data = load_geojson(args.source)
    features = data.get("features", [])

    extracted, updated_geo, updated_country = update_features(features, args.fill_country)

    print(
        (
            f"Features processed: {len(features)}\n"
            f"Coordinates extracted from URL: {extracted}\n"
            f"Geometries updated: {updated_geo}\n"
            f"Country codes set to JP: {updated_country}"
        )
    )

    if args.dry_run:
        return

    output = args.output or args.source
    save_geojson(output, data)
    print(f"Written updated GeoJSON to {output}")


if __name__ == "__main__":
    main()
