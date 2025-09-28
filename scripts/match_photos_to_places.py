#!/usr/bin/env python3
"""Match photo EXIF records to saved places based on proximity."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SAVED_PLACES_PATH = Path("data/GoogleMaps/SavedPlaces.json")
EXIF_PATH = Path("data/photos/japan_exif.json")
OUTPUT_PATH = Path("data/photos/place_photo_matches.json")


@dataclass
class Place:
    name: str
    address: Optional[str]
    lon: float
    lat: float
    category: Optional[str]
    saved_list: Optional[str]
    prefecture: Optional[str]
    google_maps_url: Optional[str]


@dataclass
class Photo:
    filename: str
    directory: str
    lon: float
    lat: float
    timestamp: Optional[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Match photo EXIF entries to saved places.")
    parser.add_argument("--places", type=Path, default=SAVED_PLACES_PATH, help="SavedPlaces JSON file")
    parser.add_argument("--exif", type=Path, default=EXIF_PATH, help="Filtered EXIF JSON file (Japan)")
    parser.add_argument("--radius", type=float, default=100.0, help="Matching radius in meters (default 100)")
    parser.add_argument("--max-per-photo", type=int, default=1, help="Maximum matches per photo (0 for unlimited)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Where to write match results (JSON)")
    parser.add_argument("--dry-run", action="store_true", help="Only print summary, do not write output file")
    return parser.parse_args()


def load_places(path: Path) -> List[Place]:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    places: List[Place] = []
    for feature in features:
        coords = feature.get("geometry", {}).get("coordinates")
        if not (isinstance(coords, list) and len(coords) == 2):
            continue
        lon, lat = coords
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            continue
        if lon == 0 and lat == 0:
            continue
        props = feature.get("properties", {})
        location = props.get("location", {})
        places.append(
            Place(
                name=location.get("name") or "<Unnamed>",
                address=location.get("address"),
                lon=float(lon),
                lat=float(lat),
                category=props.get("category"),
                saved_list=props.get("saved_list"),
                prefecture=props.get("prefecture"),
                google_maps_url=props.get("google_maps_url"),
            )
        )
    return places


def parse_timestamp(value: Any) -> Optional[str]:
    if not value:
        return None
    # EXIF uses "YYYY:MM:DD HH:MM:SS"
    try:
        dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        return dt.isoformat()
    except ValueError:
        return None


def load_photos(path: Path) -> List[Photo]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    photos: List[Photo] = []
    for entry in entries:
        lat = entry.get("GPSLatitude")
        lon = entry.get("GPSLongitude")
        if lat is None or lon is None:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            continue
        photos.append(
            Photo(
                filename=entry.get("FileName", ""),
                directory=entry.get("Directory", ""),
                lon=lon_f,
                lat=lat_f,
                timestamp=parse_timestamp(entry.get("DateTimeOriginal")),
            )
        )
    return photos


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon pairs."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def match_photos(
    places: List[Place], photos: List[Photo], radius_m: float, max_per_photo: int
) -> Tuple[Dict[str, Dict[str, Any]], List[Photo]]:
    place_index = {place.google_maps_url or place.name: place for place in places}
    matches: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"place": None, "matches": []}
    )

    for place in places:
        key = place.google_maps_url or place.name
        matches[key]["place"] = place

    unmatched: List[Photo] = []

    for photo in photos:
        dists: List[Tuple[float, Place]] = []
        for place in places:
            dist = haversine(photo.lat, photo.lon, place.lat, place.lon)
            if dist <= radius_m:
                dists.append((dist, place))
        if not dists:
            unmatched.append(photo)
            continue
        dists.sort(key=lambda pair: pair[0])
        if max_per_photo > 0:
            dists = dists[:max_per_photo]
        for dist, place in dists:
            key = place.google_maps_url or place.name
            matches[key]["matches"].append(
                {
                    "filename": photo.filename,
                    "directory": photo.directory,
                    "timestamp": photo.timestamp,
                    "distance_m": round(dist, 2),
                }
            )

    return matches, unmatched


def summarise(matches: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "total_places": 0,
        "places_with_matches": 0,
        "total_matches": 0,
        "place_summaries": [],
    }
    for data in matches.values():
        place = data["place"]
        photo_matches = data["matches"]
        summary["total_places"] += 1
        if not photo_matches:
            continue
        summary["places_with_matches"] += 1
        summary["total_matches"] += len(photo_matches)
        timestamps = [m["timestamp"] for m in photo_matches if m.get("timestamp")]
        earliest = min(timestamps) if timestamps else None
        latest = max(timestamps) if timestamps else None
        summary["place_summaries"].append(
            {
                "name": place.name,
                "address": place.address,
                "prefecture": place.prefecture,
                "google_maps_url": place.google_maps_url,
                "match_count": len(photo_matches),
                "earliest": earliest,
                "latest": latest,
            }
        )
    summary["place_summaries"].sort(key=lambda item: item["match_count"], reverse=True)
    return summary


def build_output(matches: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    output = {"matches": [], "summary": summarise(matches)}
    for key, data in matches.items():
        place = data["place"]
        output["matches"].append(
            {
                "place": {
                    "name": place.name,
                    "address": place.address,
                    "prefecture": place.prefecture,
                    "category": place.category,
                    "saved_list": place.saved_list,
                    "google_maps_url": place.google_maps_url,
                    "coordinates": [place.lon, place.lat],
                },
                "photos": data["matches"],
            }
        )
    output["matches"].sort(key=lambda item: len(item["photos"]), reverse=True)
    return output


def main() -> None:
    args = parse_args()
    places = load_places(args.places)
    photos = load_photos(args.exif)

    print(f"Loaded {len(places)} places and {len(photos)} photos.")
    matches, unmatched = match_photos(places, photos, args.radius, args.max_per_photo)
    summary = summarise(matches)

    print(
        f"Places with photo matches: {summary['places_with_matches']} / {summary['total_places']}"
    )
    print(f"Total photo-place pairs: {summary['total_matches']}")
    print(f"Unmatched photos: {len(unmatched)}")

    output = build_output(matches)
    output["unmatched_photos"] = [
        {
            "filename": photo.filename,
            "directory": photo.directory,
            "timestamp": photo.timestamp,
            "coordinates": [photo.lon, photo.lat],
        }
        for photo in unmatched
    ]

    if args.dry_run:
        print("Dry run: not writing output file.")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    print(f"Match results written to {args.output}")


if __name__ == "__main__":
    main()
