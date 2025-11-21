#!/usr/bin/env python3
"""
Query script to find cafes in Hokkaido.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def find_cafes_in_hokkaido(driver, database='neo4j'):
    """Find all cafes in Hokkaido."""
    
    print("=" * 70)
    print("SEARCHING FOR CAFES IN HOKKAIDO")
    print("=" * 70)
    
    with driver.session(database=database) as session:
        # Query for cafes in Hokkaido
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType {name: 'cafe'})
        WHERE p.prefecture CONTAINS 'Hokkaido'
        RETURN p.name as name, 
               p.address as address, 
               p.prefecture as prefecture,
               p.latitude as latitude,
               p.longitude as longitude,
               p.google_maps_url as maps_url,
               p.visited as visited
        ORDER BY p.name
        """
        result = session.run(query)
        records = list(result)
        
        if not records:
            print("\n❌ No cafes found in Hokkaido")
            return
        
        print(f"\n✅ Found {len(records)} cafe(s) in Hokkaido:\n")
        for i, record in enumerate(records, 1):
            print(f"{i}. {record['name']}")
            if record['address']:
                print(f"   📍 Address: {record['address']}")
            if record['prefecture']:
                print(f"   🗾 Prefecture: {record['prefecture']}")
            if record['latitude'] and record['longitude']:
                print(f"   📌 Coordinates: {record['latitude']}, {record['longitude']}")
            if record['maps_url']:
                print(f"   🔗 Maps: {record['maps_url']}")
            if record['visited'] is not None:
                visited_status = "✅ Visited" if record['visited'] else "⭕ Not visited"
                print(f"   {visited_status}")
            print()


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set in .env file")
        return 1
    
    print(f"Connecting to: {uri}")
    print(f"Database: {database}\n")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        find_cafes_in_hokkaido(driver, database)
        driver.close()
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

