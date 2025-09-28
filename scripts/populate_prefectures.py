#!/usr/bin/env python3
"""Fill the `properties.prefecture` field by parsing the address string."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_PATH = Path("data/GoogleMaps/SavedPlaces.json")

PREFECTURES: List[Tuple[str, Tuple[str, ...]]] = [
    ("Hokkaido", ("hokkaido", "北海道")),
    ("Aomori", ("aomori", "青森")),
    ("Iwate", ("iwate", "岩手")),
    ("Miyagi", ("miyagi", "宮城")),
    ("Akita", ("akita", "秋田")),
    ("Yamagata", ("yamagata", "山形")),
    ("Fukushima", ("fukushima", "福島")),
    ("Ibaraki", ("ibaraki", "茨城")),
    ("Tochigi", ("tochigi", "栃木")),
    ("Gunma", ("gunma", "群馬")),
    ("Saitama", ("saitama", "埼玉")),
    ("Chiba", ("chiba", "千葉")),
    ("Tokyo", ("tokyo", "東京都", "東京")),
    ("Kanagawa", ("kanagawa", "神奈川")),
    ("Niigata", ("niigata", "新潟")),
    ("Toyama", ("toyama", "富山")),
    ("Ishikawa", ("ishikawa", "石川")),
    ("Fukui", ("fukui", "福井")),
    ("Yamanashi", ("yamanashi", "山梨")),
    ("Nagano", ("nagano", "長野")),
    ("Gifu", ("gifu", "岐阜")),
    ("Shizuoka", ("shizuoka", "静岡")),
    ("Aichi", ("aichi", "愛知")),
    ("Mie", ("mie", "三重")),
    ("Shiga", ("shiga", "滋賀")),
    ("Kyoto", ("kyoto", "京都")),
    ("Osaka", ("osaka", "大阪")),
    ("Hyogo", ("hyogo", "兵庫")),
    ("Nara", ("nara", "奈良")),
    ("Wakayama", ("wakayama", "和歌山")),
    ("Tottori", ("tottori", "鳥取")),
    ("Shimane", ("shimane", "島根")),
    ("Okayama", ("okayama", "岡山")),
    ("Hiroshima", ("hiroshima", "広島")),
    ("Yamaguchi", ("yamaguchi", "山口")),
    ("Tokushima", ("tokushima", "徳島")),
    ("Kagawa", ("kagawa", "香川")),
    ("Ehime", ("ehime", "愛媛")),
    ("Kochi", ("kochi", "高知")),
    ("Fukuoka", ("fukuoka", "福岡")),
    ("Saga", ("saga", "佐賀")),
    ("Nagasaki", ("nagasaki", "長崎")),
    ("Kumamoto", ("kumamoto", "熊本")),
    ("Oita", ("oita", "大分")),
    ("Miyazaki", ("miyazaki", "宮崎")),
    ("Kagoshima", ("kagoshima", "鹿児島")),
    ("Okinawa", ("okinawa", "沖縄")),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate prefecture metadata from address strings.")
    parser.add_argument("--source", type=Path, default=DEFAULT_PATH, help="SavedPlaces JSON file to update.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing to disk.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prefecture values (default: only fill blanks).",
    )
    return parser.parse_args()


def load_geojson(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_geojson(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def find_prefecture(address: str | None) -> str | None:
    if not address:
        return None
    lower = address.lower()
    for name, patterns in PREFECTURES:
        for pattern in patterns:
            if pattern in lower or pattern in address:
                return name
    return None


def main() -> None:
    args = parse_args()
    data = load_geojson(args.source)
    features = data.get("features", [])

    updates = 0
    already_set = 0
    unmatched = 0

    for feature in features:
        props = feature.setdefault("properties", {})
        location = props.get("location", {})
        current = props.get("prefecture")

        if current and not args.force:
            already_set += 1
            continue

        prefecture = find_prefecture(location.get("address"))
        if prefecture:
            if current != prefecture:
                props["prefecture"] = prefecture
                updates += 1
        else:
            if not current:
                unmatched += 1

    if args.dry_run:
        print(f"Dry run: would update {updates} features, {already_set} already set, {unmatched} unmatched.")
        return

    save_geojson(args.source, data)
    print(f"Updated prefecture for {updates} features. Unmatched: {unmatched}. Already set: {already_set}.")


if __name__ == "__main__":
    main()
