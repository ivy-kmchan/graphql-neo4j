#!/usr/bin/env python3
"""
Test script to verify ActivityCategory and CuisineType queries work correctly.
This ensures the Streamlit chatbot will be able to query the relationships.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def test_queries(driver, database='neo4j'):
    """Run test queries to verify the data."""
    
    print("=" * 70)
    print("TESTING ACTIVITYCATEGORY AND CUISINETYPE QUERIES")
    print("=" * 70)
    
    with driver.session(database=database) as session:
        
        # Test 1: Find temples
        print("\n1️⃣  TEST: Find temples in Kyoto")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory {name: 'temple'})
        WHERE p.prefecture CONTAINS 'Kyoto'
        RETURN p.name as name, p.address as address, p.prefecture as prefecture
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} temples in Kyoto:")
        for record in records:
            print(f"  • {record['name']}")
            print(f"    {record['address']}")
        
        # Test 2: Find sushi restaurants
        print("\n2️⃣  TEST: Find sushi restaurants")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType {name: 'sushi'})
        RETURN p.name as name, p.address as address, p.prefecture as prefecture
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} sushi restaurants:")
        for record in records:
            print(f"  • {record['name']}")
            print(f"    Prefecture: {record['prefecture']}")
        
        # Test 3: Find parks
        print("\n3️⃣  TEST: Find parks")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory {name: 'park'})
        RETURN p.name as name, p.prefecture as prefecture
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} parks:")
        for record in records:
            print(f"  • {record['name']} ({record['prefecture']})")
        
        # Test 4: Find cafes
        print("\n4️⃣  TEST: Find cafes")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType {name: 'cafe'})
        RETURN p.name as name, p.prefecture as prefecture
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} cafes:")
        for record in records:
            print(f"  • {record['name']} ({record['prefecture']})")
        
        # Test 5: Activity statistics
        print("\n5️⃣  TEST: Activity statistics")
        print("-" * 70)
        query = """
        MATCH (a:ActivityCategory)<-[:HAS_ACTIVITY]-(p:Place)
        RETURN a.name as activity, count(p) as count
        ORDER BY count DESC
        """
        result = session.run(query)
        print("Activity distribution:")
        for record in result:
            print(f"  • {record['activity']}: {record['count']} places")
        
        # Test 6: Cuisine statistics
        print("\n6️⃣  TEST: Cuisine statistics")
        print("-" * 70)
        query = """
        MATCH (c:CuisineType)<-[:SERVES_CUISINE]-(p:Place)
        RETURN c.name as cuisine, count(p) as count
        ORDER BY count DESC
        """
        result = session.run(query)
        print("Cuisine distribution:")
        for record in result:
            print(f"  • {record['cuisine']}: {record['count']} places")
        
        # Test 7: Complex query - Places with multiple activities
        print("\n7️⃣  TEST: Places with multiple activities")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory)
        WITH p, collect(a.name) as activities
        WHERE size(activities) > 1
        RETURN p.name as name, activities
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} places with multiple activities:")
        for record in records:
            activities = ', '.join(record['activities'])
            print(f"  • {record['name']}: {activities}")
        
        # Test 8: Hotels in Tokyo
        print("\n8️⃣  TEST: Find hotels in Tokyo")
        print("-" * 70)
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory {name: 'hotel'})
        WHERE p.prefecture CONTAINS 'Tokyo'
        RETURN p.name as name, p.address as address
        LIMIT 5
        """
        result = session.run(query)
        records = list(result)
        print(f"Found {len(records)} hotels in Tokyo:")
        for record in records:
            print(f"  • {record['name']}")


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    print(f"Connecting to: {uri}")
    print(f"Database: {database}\n")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        test_queries(driver, database)
        driver.close()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n🎉 Your database is ready for the Streamlit chatbot!")
        print("\nTo start the chatbot, run:")
        print("  streamlit run scripts/streamlit_chatbot.py")
        print("  OR")
        print("  run_chatbot.bat\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

