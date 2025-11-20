#!/usr/bin/env python3
"""
Populate CuisineType nodes and create SERVES_CUISINE relationships.
This script reads from seed-data/cuisine_types.csv and populates the Neo4j database.
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def create_cuisine_types(session):
    """Create CuisineType nodes from CSV file."""
    
    # Cuisine descriptions
    descriptions = {
        'cafe': 'Cafes and coffee shops',
        'sushi': 'Sushi restaurants and bars',
        'ramen': 'Ramen shops and noodle restaurants',
        'japanese': 'Traditional Japanese cuisine',
        'dessert': 'Dessert shops and sweet treats',
        'tempura': 'Tempura specialty restaurants',
        'chinese': 'Chinese cuisine restaurants',
        'izakaya': 'Japanese-style pubs and taverns',
        'italian': 'Italian cuisine restaurants',
        'yakitori': 'Grilled chicken skewer restaurants',
        'western': 'Western-style restaurants',
        'korean': 'Korean cuisine restaurants'
    }
    
    csv_path = 'seed-data/cuisine_types.csv'
    
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found")
        return 0
    
    print(f"\n📁 Reading from {csv_path}...")
    
    cuisines = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['cuisine_name']
            cuisines.append({
                'name': name,
                'description': descriptions.get(name, f'{name.capitalize()} cuisine')
            })
    
    print(f"Found {len(cuisines)} cuisine types to create")
    
    # Create CuisineType nodes
    query = """
    UNWIND $cuisines AS cuisine
    MERGE (c:CuisineType {name: cuisine.name})
    ON CREATE SET c.description = cuisine.description
    ON MATCH SET c.description = cuisine.description
    RETURN count(c) as created
    """
    
    result = session.run(query, cuisines=cuisines)
    count = result.single()['created']
    print(f"✅ Created/Updated {count} CuisineType nodes")
    
    return count


def link_cuisines_to_places(session):
    """Link Places to CuisineTypes based on a cuisine field (if it exists)."""
    
    print("\n🔗 Linking Places to CuisineTypes...")
    
    # First, check if places have any cuisine-related fields
    # This might be in various fields like 'type', 'category', or a custom 'cuisine' field
    check_query = """
    MATCH (p:Place)
    WHERE p.type IS NOT NULL
    RETURN DISTINCT p.type as type, count(p) as count
    ORDER BY count DESC
    LIMIT 20
    """
    
    result = session.run(check_query)
    types = [(record['type'], record['count']) for record in result]
    
    if types:
        print(f"\nFound type values in Places (top 20):")
        for ptype, count in types[:10]:
            print(f"  - {ptype}: {count} places")
    
    # Try to link based on type field matching cuisine names
    link_query = """
    MATCH (p:Place), (c:CuisineType)
    WHERE p.type IS NOT NULL 
      AND toLower(p.type) = c.name
      AND NOT EXISTS((p)-[:SERVES_CUISINE]->(c))
    CREATE (p)-[:SERVES_CUISINE]->(c)
    RETURN count(*) as relationships_created
    """
    
    result = session.run(link_query)
    count = result.single()['relationships_created']
    print(f"✅ Created {count} SERVES_CUISINE relationships based on type field")
    
    # Also try matching on address or name containing cuisine keywords
    keyword_query = """
    MATCH (p:Place), (c:CuisineType)
    WHERE NOT EXISTS((p)-[:SERVES_CUISINE]->(c))
      AND (
        toLower(p.name) CONTAINS c.name 
        OR toLower(p.address) CONTAINS c.name
      )
      AND (
        p.type IS NULL 
        OR toLower(p.type) IN ['restaurant', 'cafe', 'food', 'dining']
      )
    CREATE (p)-[:SERVES_CUISINE]->(c)
    RETURN count(*) as relationships_created
    """
    
    result = session.run(keyword_query)
    keyword_count = result.single()['relationships_created']
    if keyword_count > 0:
        print(f"✅ Created {keyword_count} SERVES_CUISINE relationships based on name/address keywords")
    
    return count + keyword_count


def verify_results(session):
    """Verify the created nodes and relationships."""
    
    print("\n📊 Verification:")
    
    # Count CuisineType nodes
    result = session.run("MATCH (c:CuisineType) RETURN count(c) as count")
    cuisine_count = result.single()['count']
    print(f"  - CuisineType nodes: {cuisine_count}")
    
    # Count SERVES_CUISINE relationships
    result = session.run("MATCH ()-[r:SERVES_CUISINE]->() RETURN count(r) as count")
    rel_count = result.single()['count']
    print(f"  - SERVES_CUISINE relationships: {rel_count}")
    
    # Show sample relationships
    if rel_count > 0:
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType)
        RETURN p.name as place, c.name as cuisine
        LIMIT 5
        """
        result = session.run(query)
        print(f"\n  Sample relationships:")
        for record in result:
            print(f"    {record['place']} -> {record['cuisine']}")
    else:
        print("\n  ⚠️  No SERVES_CUISINE relationships created.")
        print("     Consider manually adding cuisine data to Place nodes")
    
    # Show cuisine type distribution
    if rel_count > 0:
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType)
        RETURN c.name as cuisine, count(p) as places
        ORDER BY places DESC
        """
        result = session.run(query)
        print(f"\n  Cuisine distribution:")
        for record in result:
            print(f"    {record['cuisine']}: {record['places']} places")
    
    return cuisine_count, rel_count


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print("=" * 60)
    print("POPULATE CUISINE TYPES")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Create CuisineType nodes
            create_cuisine_types(session)
            
            # Link Places to CuisineTypes
            link_cuisines_to_places(session)
            
            # Verify results
            verify_results(session)
        
        driver.close()
        print("\n✅ Script completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

