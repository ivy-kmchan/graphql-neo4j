#!/usr/bin/env python3
"""
Populate ActivityCategory nodes and create HAS_ACTIVITY relationships.
This script reads from seed-data/activity_categories.csv and populates the Neo4j database.
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def create_activity_categories(session):
    """Create ActivityCategory nodes from CSV file."""
    
    # Activity category descriptions
    descriptions = {
        'temple': 'Religious and spiritual sites including shrines and temples',
        'restaurant': 'Dining establishments and eateries',
        'park': 'Parks, gardens, and outdoor recreational areas',
        'museum': 'Museums, galleries, and cultural centers',
        'shopping': 'Shopping areas, stores, and markets',
        'transport': 'Transportation hubs including stations and airports',
        'hotel': 'Accommodation and lodging facilities',
        'entertainment': 'Entertainment venues and attractions',
        'nature': 'Natural attractions and scenic spots',
        'historical': 'Historical sites and landmarks'
    }
    
    csv_path = 'seed-data/activity_categories.csv'
    
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found")
        return 0
    
    print(f"\n📁 Reading from {csv_path}...")
    
    categories = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['activity_name']
            categories.append({
                'name': name,
                'description': descriptions.get(name, f'{name.capitalize()} category')
            })
    
    print(f"Found {len(categories)} categories to create")
    
    # Create ActivityCategory nodes
    query = """
    UNWIND $categories AS cat
    MERGE (a:ActivityCategory {name: cat.name})
    ON CREATE SET a.description = cat.description
    ON MATCH SET a.description = cat.description
    RETURN count(a) as created
    """
    
    result = session.run(query, categories=categories)
    count = result.single()['created']
    print(f"✅ Created/Updated {count} ActivityCategory nodes")
    
    return count


def link_activities_to_places(session):
    """Link Places to ActivityCategories based on activity_type field."""
    
    print("\n🔗 Linking Places to ActivityCategories...")
    
    # First, check what activity_type values exist
    check_query = """
    MATCH (p:Place)
    WHERE p.activity_type IS NOT NULL
    RETURN DISTINCT p.activity_type as type, count(p) as count
    ORDER BY count DESC
    """
    
    result = session.run(check_query)
    activity_types = [(record['type'], record['count']) for record in result]
    
    if activity_types:
        print(f"\nFound activity_type values in Places:")
        for atype, count in activity_types:
            print(f"  - {atype}: {count} places")
    else:
        print("⚠️  No Places have activity_type set yet")
    
    # Create relationships
    link_query = """
    MATCH (p:Place), (ac:ActivityCategory)
    WHERE p.activity_type IS NOT NULL 
      AND p.activity_type = ac.name
      AND NOT EXISTS((p)-[:HAS_ACTIVITY]->(ac))
    CREATE (p)-[:HAS_ACTIVITY]->(ac)
    RETURN count(*) as relationships_created
    """
    
    result = session.run(link_query)
    count = result.single()['relationships_created']
    print(f"✅ Created {count} HAS_ACTIVITY relationships")
    
    return count


def verify_results(session):
    """Verify the created nodes and relationships."""
    
    print("\n📊 Verification:")
    
    # Count ActivityCategory nodes
    result = session.run("MATCH (ac:ActivityCategory) RETURN count(ac) as count")
    ac_count = result.single()['count']
    print(f"  - ActivityCategory nodes: {ac_count}")
    
    # Count HAS_ACTIVITY relationships
    result = session.run("MATCH ()-[r:HAS_ACTIVITY]->() RETURN count(r) as count")
    rel_count = result.single()['count']
    print(f"  - HAS_ACTIVITY relationships: {rel_count}")
    
    # Show sample relationships
    if rel_count > 0:
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
        RETURN p.name as place, ac.name as category
        LIMIT 5
        """
        result = session.run(query)
        print(f"\n  Sample relationships:")
        for record in result:
            print(f"    {record['place']} -> {record['category']}")
    
    return ac_count, rel_count


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print("=" * 60)
    print("POPULATE ACTIVITY CATEGORIES")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Create ActivityCategory nodes
            create_activity_categories(session)
            
            # Link Places to ActivityCategories
            link_activities_to_places(session)
            
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

