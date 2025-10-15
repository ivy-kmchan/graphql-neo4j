#!/usr/bin/env python3
"""Remove places with invalid coordinates from Neo4j."""

import os
from neo4j import GraphDatabase

def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set in .env file")
        return 1
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # First, find places with invalid coordinates
            result = session.run("""
                MATCH (p:Place)
                WHERE p.longitude IS NULL OR p.latitude IS NULL 
                   OR p.longitude = 0 OR p.latitude = 0
                RETURN p.name as name, p.longitude as lon, p.latitude as lat
            """)
            
            invalid_places = list(result)
            print(f"Found {len(invalid_places)} places with invalid coordinates:")
            for place in invalid_places:
                print(f"  - {place['name']} (lon: {place['lon']}, lat: {place['lat']})")
            
            if invalid_places:
                # Delete relationships first, then the places
                delete_result = session.run("""
                    MATCH (p:Place)
                    WHERE p.longitude IS NULL OR p.latitude IS NULL 
                       OR p.longitude = 0 OR p.latitude = 0
                    DETACH DELETE p
                    RETURN count(p) as deleted_count
                """)
                
                deleted_count = delete_result.single()["deleted_count"]
                print(f"\n[DONE] Deleted {deleted_count} places with invalid coordinates")
            else:
                print("\n[INFO] No places with invalid coordinates found")
                
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    finally:
        driver.close()
    
    return 0

if __name__ == "__main__":
    exit(main())
