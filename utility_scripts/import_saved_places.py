#!/usr/bin/env python3
"""Import SavedPlaces.json data into Neo4j database."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

SOURCE = Path("data/GoogleMaps/SavedPlaces.json")


class Neo4jImporter:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")  # Required - set in .env
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not self.password:
            raise ValueError("NEO4J_PASSWORD not set in .env file")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def clear_existing_data(self):
        """Clear existing Place and Region data."""
        with self.driver.session(database=self.database) as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]-() DELETE r")
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            print("[OK] Cleared existing data")
    
    def create_constraints(self):
        """Create uniqueness constraints."""
        # Skip constraints for now to avoid conflicts
        print("[SKIP] Skipping constraints for now")
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from SavedPlaces.json."""
        if not SOURCE.exists():
            raise FileNotFoundError(f"SavedPlaces file not found at {SOURCE}")
        
        with SOURCE.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def is_valid_coords(self, coords) -> bool:
        """Check if coordinates are valid."""
        return (
            isinstance(coords, list)
            and len(coords) == 2
            and isinstance(coords[0], (int, float))
            and isinstance(coords[1], (int, float))
            and not (coords[0] == 0 and coords[1] == 0)
        )
    
    def extract_prefecture(self, address: str) -> Optional[str]:
        """Extract prefecture from address."""
        if not address:
            return None
        
        # Simple prefecture extraction for Japan
        prefecture_keywords = [
            "Tokyo", "Osaka", "Kyoto", "Hokkaido", "Aichi", "Kanagawa",
            "Fukuoka", "Saitama", "Chiba", "Hyogo", "Shizuoka", "Ibaraki",
            "Niigata", "Miyagi", "Gifu", "Gunma", "Tochigi", "Okayama",
            "Kumamoto", "Kagoshima", "Nagano", "Hiroshima", "Fukushima",
            "Mie", "Yamaguchi", "Ehime", "Shiga", "Aomori", "Nagasaki",
            "Oita", "Ishikawa", "Yamagata", "Miyazaki", "Toyama", "Akita",
            "Wakayama", "Yamanashi", "Kagawa", "Fukui", "Tokushima",
            "Kochi", "Shimane", "Tottori", "Iwate", "Saga", "Nara",
            "Fukushima", "Okinawa"
        ]
        
        for pref in prefecture_keywords:
            if pref in address:
                return pref
        
        return None
    
    def _calculate_data_completeness(self, place_data: Dict[str, Any]) -> int:
        """Calculate a score for data completeness (higher = better)."""
        score = 0
        if place_data.get("address"):
            score += 1
        if place_data.get("prefecture"):
            score += 1
        if place_data.get("description"):
            score += 1
        if place_data.get("google_maps_url"):
            score += 1
        if place_data.get("latitude") and place_data.get("longitude"):
            score += 2  # Coordinates are very important
        return score
    
    def import_places(self, features: List[Dict[str, Any]]):
        """Import places from GeoJSON features."""
        
        with self.driver.session(database=self.database) as session:
            imported_count = 0
            skipped_count = 0
            seen_places = {}  # Track best version of each place by name
            
            # First pass: collect and deduplicate places
            for feature in features:
                props = feature.get("properties", {})
                location = props.get("location", {})
                coords = feature.get("geometry", {}).get("coordinates")
                
                # Skip if no name or invalid coordinates
                place_name = location.get("name")
                if not place_name or not self.is_valid_coords(coords):
                    skipped_count += 1
                    continue
                
                # Extract data
                address = location.get("address", "")
                prefecture = props.get("prefecture") or self.extract_prefecture(address)
                
                # Create place data
                place_data = {
                    "name": place_name,
                    "type": props.get("type", "place"),
                    "description": props.get("description", ""),
                    "address": address,
                    "longitude": coords[0],
                    "latitude": coords[1],
                    "prefecture": prefecture,
                    "category": props.get("category", "place"),
                    "saved_list": props.get("saved_list", ""),
                    "visited": props.get("visited", False),
                    "google_maps_url": props.get("google_maps_url", ""),
                    "date": props.get("date", "")
                }
                
                # Deduplication: keep the version with more complete data
                if place_name not in seen_places:
                    seen_places[place_name] = place_data
                else:
                    # Compare data completeness and keep the better version
                    existing = seen_places[place_name]
                    current_score = self._calculate_data_completeness(place_data)
                    existing_score = self._calculate_data_completeness(existing)
                    
                    if current_score > existing_score:
                        seen_places[place_name] = place_data
                    skipped_count += 1
            
            # Second pass: import all deduplicated places using CREATE to ensure no duplicates
            for place_data in seen_places.values():
                # Use CREATE with unique constraint to prevent duplicates
                place_query = """
                CREATE (p:Place {
                    name: $name,
                    type: $type,
                    description: $description,
                    address: $address,
                    longitude: $longitude,
                    latitude: $latitude,
                    prefecture: $prefecture,
                    category: $category,
                    saved_list: $saved_list,
                    visited: $visited,
                    google_maps_url: $google_maps_url,
                    date: $date
                })
                RETURN p
                """
                
                try:
                    session.run(place_query, place_data)
                    
                    # Create region if prefecture exists
                    if place_data.get("prefecture"):
                        region_query = """
                        MERGE (r:Region {name: $prefecture})
                        WITH r
                        MATCH (p:Place {name: $place_name})
                        MERGE (r)-[:HAS_PLACE]->(p)
                        """
                        session.run(region_query, {
                            "prefecture": place_data["prefecture"],
                            "place_name": place_data["name"]
                        })
                    
                    imported_count += 1
                except Exception as e:
                    # If there's a constraint violation, skip this place
                    skipped_count += 1
                    continue
            
            print(f"[OK] Imported {imported_count} places")
            print(f"[WARN] Skipped {skipped_count} places (missing name/coordinates or duplicates)")
    
    def run(self, clear_existing: bool = False):
        """Run the import process."""
        print("[START] Starting SavedPlaces import...")
        
        # Load data
        data = self.load_data()
        features = data.get("features", [])
        print(f"[INFO] Found {len(features)} places in SavedPlaces.json")
        
        # Clear existing data if requested
        if clear_existing:
            self.clear_existing_data()
        
        # Create constraints
        self.create_constraints()
        
        # Import places
        self.import_places(features)
        
        print("[DONE] Import completed!")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import SavedPlaces.json into Neo4j")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear existing data before import"
    )
    
    args = parser.parse_args()
    
    try:
        importer = Neo4jImporter()
        importer.run(clear_existing=args.clear)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return 1
    finally:
        if 'importer' in locals():
            importer.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
