#!/usr/bin/env python3
"""
Simple chatbot test without OpenAI dependency.
This tests the core Neo4j functionality without requiring an API key.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class SimpleTravelBot:
    """Simple travel bot for testing Neo4j integration without OpenAI."""
    
    def __init__(self):
        """Initialize the bot with Neo4j connection."""
        self.uri = os.getenv("NEO4J_URI")  # Required - set in .env
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")  # Required - set in .env
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")  # Changed from 'travel' to 'neo4j' for Aura
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def _run_cypher_query(self, query: str, parameters: dict = None) -> list:
        """Execute a Cypher query and return results."""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def search_places_by_location(self, location: str) -> str:
        """Search for places in a specific location."""
        query = """
        MATCH (p:Place)
        WHERE p.prefecture CONTAINS $location OR p.address CONTAINS $location
        RETURN p.name as name, p.address as address, p.prefecture as prefecture, 
               p.latitude as latitude, p.longitude as longitude, p.description as description
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"location": location})
        
        if not results:
            return f"No places found in {location}"
        
        response = f"Found {len(results)} places in {location}:\n"
        for place in results:
            response += f"• {place['name']} - {place['address']}\n"
            if place['description']:
                response += f"  {place['description']}\n"
        
        return response
    
    def search_places_by_activity(self, activity: str) -> str:
        """Find places by activity type."""
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
        WHERE ac.name CONTAINS $activity
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               collect(ac.name) as activities
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"activity": activity.lower()})
        
        if not results:
            return f"No {activity} places found"
        
        response = f"Found {len(results)} {activity} places:\n"
        for place in results:
            response += f"• {place['name']} - {place['address']}\n"
            response += f"  Activities: {', '.join(place['activities'])}\n"
        
        return response
    
    def search_places_by_cuisine(self, cuisine: str) -> str:
        """Find places that serve specific cuisine."""
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(ct:CuisineType)
        WHERE ct.name CONTAINS $cuisine
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               collect(ct.name) as cuisines
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"cuisine": cuisine.lower()})
        
        if not results:
            return f"No places serving {cuisine} cuisine found"
        
        response = f"Found {len(results)} places serving {cuisine} cuisine:\n"
        for place in results:
            response += f"• {place['name']} - {place['address']}\n"
            response += f"  Cuisines: {', '.join(place['cuisines'])}\n"
        
        return response
    
    def get_place_count(self) -> str:
        """Get the total number of places."""
        count_query = "MATCH (p:Place) RETURN count(p) as count"
        results = self._run_cypher_query(count_query)
        count = results[0]['count'] if results else 0
        return f"There are {count} places in the travel database."
    
    def get_database_stats(self) -> dict:
        """Get comprehensive database statistics."""
        stats = {}
        
        # Total places
        place_count = self._run_cypher_query("MATCH (p:Place) RETURN count(p) as count")
        stats['total_places'] = place_count[0]['count'] if place_count else 0
        
        # Activity categories
        activities = self._run_cypher_query("""
            MATCH (ac:ActivityCategory)
            OPTIONAL MATCH (ac)<-[:HAS_ACTIVITY]-(p:Place)
            RETURN ac.name as activity, count(p) as count
            ORDER BY count DESC
        """)
        stats['activities'] = activities
        
        # Cuisine types
        cuisines = self._run_cypher_query("""
            MATCH (ct:CuisineType)
            OPTIONAL MATCH (ct)<-[:SERVES_CUISINE]-(p:Place)
            RETURN ct.name as cuisine, count(p) as count
            ORDER BY count DESC
        """)
        stats['cuisines'] = cuisines
        
        # Prefectures
        prefectures = self._run_cypher_query("""
            MATCH (p:Place)
            WHERE p.prefecture IS NOT NULL
            RETURN p.prefecture as prefecture, count(p) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['prefectures'] = prefectures
        
        return stats
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def test_bot():
    """Test the simple bot functionality."""
    print("🤖 Testing Simple Travel Bot")
    print("=" * 40)
    
    bot = SimpleTravelBot()
    
    try:
        # Test 1: Place count
        print("\n1. Testing place count...")
        count = bot.get_place_count()
        print(f"   ✅ {count}")
        
        # Test 2: Location search
        print("\n2. Testing location search...")
        tokyo_places = bot.search_places_by_location("Tokyo")
        print(f"   ✅ Tokyo search: {len(tokyo_places.split('•')) - 1} places found")
        
        # Test 3: Activity search
        print("\n3. Testing activity search...")
        restaurants = bot.search_places_by_activity("restaurant")
        print(f"   ✅ Restaurant search: {len(restaurants.split('•')) - 1} places found")
        
        # Test 4: Cuisine search
        print("\n4. Testing cuisine search...")
        japanese_food = bot.search_places_by_cuisine("japanese")
        print(f"   ✅ Japanese cuisine search: {len(japanese_food.split('•')) - 1} places found")
        
        # Test 5: Database stats
        print("\n5. Testing database statistics...")
        stats = bot.get_database_stats()
        print(f"   ✅ Total places: {stats['total_places']}")
        print(f"   ✅ Activity categories: {len(stats['activities'])}")
        print(f"   ✅ Cuisine types: {len(stats['cuisines'])}")
        print(f"   ✅ Prefectures: {len(stats['prefectures'])}")
        
        print("\n🎉 All tests passed! Neo4j integration is working perfectly.")
        
        # Show sample data
        print("\n📊 Sample Data:")
        print(f"Top activities: {[a['activity'] for a in stats['activities'][:3]]}")
        print(f"Top cuisines: {[c['cuisine'] for c in stats['cuisines'][:3]]}")
        print(f"Top prefectures: {[p['prefecture'] for p in stats['prefectures'][:3]]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    finally:
        bot.close()

def interactive_demo():
    """Run an interactive demo."""
    print("\n🎮 Interactive Demo")
    print("=" * 40)
    print("Try these commands:")
    print("- 'places in Tokyo'")
    print("- 'restaurants'")
    print("- 'temples'")
    print("- 'japanese food'")
    print("- 'stats'")
    print("- 'quit' to exit")
    
    bot = SimpleTravelBot()
    
    try:
        while True:
            user_input = input("\nYou: ").strip().lower()
            
            if user_input == 'quit':
                break
            elif 'tokyo' in user_input or 'places' in user_input:
                result = bot.search_places_by_location("Tokyo")
                print(f"Bot: {result}")
            elif 'restaurant' in user_input:
                result = bot.search_places_by_activity("restaurant")
                print(f"Bot: {result}")
            elif 'temple' in user_input:
                result = bot.search_places_by_activity("temple")
                print(f"Bot: {result}")
            elif 'japanese' in user_input or 'food' in user_input:
                result = bot.search_places_by_cuisine("japanese")
                print(f"Bot: {result}")
            elif 'stats' in user_input:
                stats = bot.get_database_stats()
                print(f"Bot: Database has {stats['total_places']} places, {len(stats['activities'])} activity types, {len(stats['cuisines'])} cuisine types")
            else:
                print("Bot: I can help you find places, restaurants, temples, or show database stats. Try 'places in Tokyo' or 'restaurants'")
    
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        bot.close()

def main():
    """Main function."""
    if test_bot():
        print("\n" + "=" * 40)
        print("✅ Setup test completed successfully!")
        print("🌐 You can now use the Streamlit chatbot at: http://localhost:8502")
        print("🔗 Or use the GraphQL API at: http://localhost:4010")

if __name__ == "__main__":
    main()
