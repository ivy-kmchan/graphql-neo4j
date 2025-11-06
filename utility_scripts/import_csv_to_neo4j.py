#!/usr/bin/env python3
"""
Import travel_places.csv into Neo4j database
Handles activities, cuisines, and regions
"""

import csv
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class CSVImporter:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "travel")
        
        if not self.password:
            raise ValueError("NEO4J_PASSWORD not set in .env file")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print(f"✅ Connected to Neo4j at {self.uri} (database: {self.database})")
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all existing data"""
        print("\n⚠️  Clearing existing database...")
        with self.driver.session(database=self.database) as session:
            # Delete all relationships and nodes
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")
    
    def create_categories(self):
        """Create Activity and Cuisine category nodes"""
        print("\n📦 Creating category nodes...")
        
        activities = ['temple', 'restaurant', 'park', 'museum', 'shopping', 
                     'transport', 'hotel', 'entertainment', 'nature', 'historical']
        cuisines = ['cafe', 'sushi', 'ramen', 'japanese', 'dessert', 'tempura', 
                   'chinese', 'izakaya', 'italian', 'yakitori', 'western', 'korean']
        
        with self.driver.session(database=self.database) as session:
            # Create ActivityCategory nodes
            for activity in activities:
                session.run("""
                    MERGE (a:ActivityCategory {name: $name})
                """, name=activity)
            
            # Create CuisineType nodes
            for cuisine in cuisines:
                session.run("""
                    MERGE (c:CuisineType {name: $name})
                """, name=cuisine)
        
        print(f"✅ Created {len(activities)} activity categories and {len(cuisines)} cuisine types")
    
    def import_places(self, csv_file='seed-data/travel_places.csv', batch_size=100):
        """Import places from CSV with batching"""
        
        print(f"\n📂 Reading CSV: {csv_file}")
        
        places = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            places = list(reader)
        
        total = len(places)
        print(f"✅ Found {total} places to import")
        
        print(f"\n🚀 Importing places in batches of {batch_size}...")
        
        imported = 0
        skipped = 0
        
        with self.driver.session(database=self.database) as session:
            for i in range(0, total, batch_size):
                batch = places[i:i+batch_size]
                
                for place in batch:
                    try:
                        name = place.get('place_name', '').strip()
                        if not name:
                            skipped += 1
                            continue
                        
                        # Prepare place data
                        place_data = {
                            'name': name,
                            'address': place.get('address', '').strip(),
                            'prefecture': place.get('prefecture', '').strip(),
                            'category': place.get('category', '').strip(),
                            'saved_list': place.get('saved_list', '').strip(),
                            'visited': place.get('visited', '').strip().upper() == 'TRUE',
                            'maps_url': place.get('maps_url', '').strip(),
                            'latitude': float(place['latitude']) if place.get('latitude') else None,
                            'longitude': float(place['longitude']) if place.get('longitude') else None,
                            'description': place.get('description', '').strip(),
                            'activity': place.get('activities', '').strip(),
                            'cuisine': place.get('cuisines', '').strip(),
                            'region': place.get('regions', '').strip() or place.get('prefecture', '').strip()
                        }
                        
                        # Create Place node
                        session.run("""
                            MERGE (p:Place {name: $name})
                            SET p.address = $address,
                                p.prefecture = $prefecture,
                                p.category = $category,
                                p.saved_list = $saved_list,
                                p.visited = $visited,
                                p.google_maps_url = $maps_url,
                                p.latitude = $latitude,
                                p.longitude = $longitude,
                                p.description = $description
                        """, **place_data)
                        
                        # Link to Region
                        if place_data['region']:
                            session.run("""
                                MATCH (p:Place {name: $name})
                                MERGE (r:Region {name: $region})
                                MERGE (r)-[:HAS_PLACE]->(p)
                            """, name=place_data['name'], region=place_data['region'])
                        
                        # Link to ActivityCategory
                        if place_data['activity']:
                            session.run("""
                                MATCH (p:Place {name: $name})
                                MERGE (a:ActivityCategory {name: $activity})
                                MERGE (p)-[:HAS_ACTIVITY]->(a)
                            """, name=place_data['name'], activity=place_data['activity'])
                        
                        # Link to CuisineType
                        if place_data['cuisine']:
                            session.run("""
                                MATCH (p:Place {name: $name})
                                MERGE (c:CuisineType {name: $cuisine})
                                MERGE (p)-[:SERVES_CUISINE]->(c)
                            """, name=place_data['name'], cuisine=place_data['cuisine'])
                        
                        imported += 1
                        
                    except Exception as e:
                        print(f"  ⚠️  Error importing {place.get('place_name', 'unknown')}: {e}")
                        skipped += 1
                
                # Progress update
                print(f"  Progress: {min(i+batch_size, total)}/{total} ({imported} imported, {skipped} skipped)")
        
        print(f"\n✅ Import complete!")
        print(f"   Imported: {imported}")
        print(f"   Skipped: {skipped}")
        
        return imported, skipped
    
    def print_stats(self):
        """Print database statistics"""
        print(f"\n{'='*70}")
        print("DATABASE STATISTICS")
        print(f"{'='*70}")
        
        with self.driver.session(database=self.database) as session:
            # Count places
            result = session.run("MATCH (p:Place) RETURN count(p) as count")
            places_count = result.single()['count']
            
            # Count regions
            result = session.run("MATCH (r:Region) RETURN count(r) as count")
            regions_count = result.single()['count']
            
            # Count activities
            result = session.run("MATCH (a:ActivityCategory) RETURN count(a) as count")
            activities_count = result.single()['count']
            
            # Count cuisines
            result = session.run("MATCH (c:CuisineType) RETURN count(c) as count")
            cuisines_count = result.single()['count']
            
            # Count places with activities
            result = session.run("MATCH (p:Place)-[:HAS_ACTIVITY]->() RETURN count(DISTINCT p) as count")
            places_with_activity = result.single()['count']
            
            # Count places with cuisines
            result = session.run("MATCH (p:Place)-[:SERVES_CUISINE]->() RETURN count(DISTINCT p) as count")
            places_with_cuisine = result.single()['count']
            
            print(f"\n📊 Node Counts:")
            print(f"   Places: {places_count}")
            print(f"   Regions: {regions_count}")
            print(f"   Activity Categories: {activities_count}")
            print(f"   Cuisine Types: {cuisines_count}")
            
            print(f"\n📈 Data Completeness:")
            print(f"   Places with activities: {places_with_activity} ({places_with_activity/places_count*100:.1f}%)")
            print(f"   Places with cuisines: {places_with_cuisine} ({places_with_cuisine/places_count*100:.1f}%)")
            
            # Top activities
            print(f"\n🏆 Top 5 Activities:")
            result = session.run("""
                MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory)
                RETURN a.name as activity, count(p) as count
                ORDER BY count DESC LIMIT 5
            """)
            for record in result:
                print(f"   {record['activity']}: {record['count']}")
            
            # Top cuisines
            print(f"\n🍽️  Top 5 Cuisines:")
            result = session.run("""
                MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType)
                RETURN c.name as cuisine, count(p) as count
                ORDER BY count DESC LIMIT 5
            """)
            for record in result:
                print(f"   {record['cuisine']}: {record['count']}")
        
        print(f"\n{'='*70}\n")

def main():
    """Main import function"""
    
    print("=" * 70)
    print("CSV TO NEO4J IMPORTER")
    print("=" * 70)
    
    importer = CSVImporter()
    
    try:
        # Ask user if they want to clear existing data
        print("\n⚠️  WARNING: This will CLEAR all existing data and import from CSV")
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("❌ Import cancelled")
            return
        
        # Clear database
        importer.clear_database()
        
        # Create category nodes
        importer.create_categories()
        
        # Import places
        imported, skipped = importer.import_places()
        
        # Print statistics
        importer.print_stats()
        
        print("✨ Import complete! Your Neo4j database is now updated with validated data.")
        
    finally:
        importer.close()

if __name__ == '__main__':
    main()

