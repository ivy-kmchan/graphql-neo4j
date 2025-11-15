#!/usr/bin/env python3
"""Enhance the travel data model with categories, activities, and cuisine types."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import Counter
import re

load_dotenv()

class DataModelEnhancer:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')  # Changed from 'travel' to 'neo4j' for Aura
    
    def analyze_place_names(self):
        """Analyze place names to identify categories."""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (p:Place)
                RETURN p.name, p.address, p.description
                LIMIT 100
            """)
            
            categories = Counter()
            cuisine_keywords = {
                'restaurant': ['restaurant', 'dining', 'cafe', 'coffee', 'tea', 'bar', 'pub', 'izakaya'],
                'temple': ['temple', 'shrine', 'jinja', 'ji', 'dera', 'buddhist', 'shinto'],
                'park': ['park', 'garden', 'botanical', 'nature'],
                'museum': ['museum', 'gallery', 'art', 'history', 'cultural'],
                'shopping': ['market', 'shopping', 'store', 'mall', 'department'],
                'hotel': ['hotel', 'ryokan', 'inn', 'accommodation'],
                'transport': ['station', 'airport', 'port', 'terminal']
            }
            
            print("Analyzing place names for categories...")
            for record in result:
                name = record['p.name'].lower() if record['p.name'] else ''
                address = record['p.address'].lower() if record['p.address'] else ''
                description = record['p.description'].lower() if record['p.description'] else ''
                
                text = f"{name} {address} {description}"
                
                for category, keywords in cuisine_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        categories[category] += 1
            
            print("Detected categories:")
            for category, count in categories.most_common():
                print(f"  {category}: {count}")
            
            return categories
    
    def create_activity_categories(self):
        """Create ActivityCategory nodes."""
        with self.driver.session(database=self.database) as session:
            activities = [
                ('restaurant', 'Places to eat and drink'),
                ('temple', 'Religious and spiritual sites'),
                ('park', 'Parks and gardens'),
                ('museum', 'Museums and cultural sites'),
                ('shopping', 'Shopping areas and markets'),
                ('hotel', 'Accommodation options'),
                ('transport', 'Transportation hubs'),
                ('entertainment', 'Entertainment venues'),
                ('nature', 'Natural attractions'),
                ('historical', 'Historical sites')
            ]
            
            print("Creating ActivityCategory nodes...")
            for name, description in activities:
                session.run("""
                    MERGE (a:ActivityCategory {name: $name})
                    SET a.description = $description
                """, name=name, description=description)
            
            print(f"Created {len(activities)} activity categories")
    
    def create_cuisine_types(self):
        """Create CuisineType nodes."""
        with self.driver.session(database=self.database) as session:
            cuisines = [
                ('japanese', 'Traditional Japanese cuisine'),
                ('sushi', 'Sushi and sashimi'),
                ('ramen', 'Ramen noodles'),
                ('tempura', 'Tempura dishes'),
                ('yakitori', 'Grilled chicken skewers'),
                ('izakaya', 'Japanese pub food'),
                ('western', 'Western cuisine'),
                ('chinese', 'Chinese cuisine'),
                ('korean', 'Korean cuisine'),
                ('italian', 'Italian cuisine'),
                ('cafe', 'Coffee and light meals'),
                ('dessert', 'Desserts and sweets')
            ]
            
            print("Creating CuisineType nodes...")
            for name, description in cuisines:
                session.run("""
                    MERGE (c:CuisineType {name: $name})
                    SET c.description = $description
                """, name=name, description=description)
            
            print(f"Created {len(cuisines)} cuisine types")
    
    def categorize_places(self):
        """Categorize existing places based on their names and descriptions."""
        with self.driver.session(database=self.database) as session:
            # Get all places
            result = session.run("MATCH (p:Place) RETURN p")
            
            categorized = 0
            for record in result:
                place = record['p']
                name = place.get('name', '').lower()
                address = place.get('address', '').lower()
                description = place.get('description', '').lower()
                
                text = f"{name} {address} {description}"
                
                # Determine activity category
                activity_category = self._determine_activity_category(text)
                if activity_category:
                    session.run("""
                        MATCH (p:Place {name: $place_name})
                        MATCH (a:ActivityCategory {name: $activity})
                        MERGE (p)-[:HAS_ACTIVITY]->(a)
                    """, place_name=place['name'], activity=activity_category)
                    categorized += 1
                
                # Determine cuisine type
                cuisine_type = self._determine_cuisine_type(text)
                if cuisine_type:
                    session.run("""
                        MATCH (p:Place {name: $place_name})
                        MATCH (c:CuisineType {name: $cuisine})
                        MERGE (p)-[:SERVES_CUISINE]->(c)
                    """, place_name=place['name'], cuisine=cuisine_type)
            
            print(f"Categorized {categorized} places")
    
    def _determine_activity_category(self, text):
        """Determine activity category from text."""
        categories = {
            'restaurant': ['restaurant', 'dining', 'cafe', 'coffee', 'tea', 'bar', 'pub', 'izakaya', 'ramen', 'sushi'],
            'temple': ['temple', 'shrine', 'jinja', 'ji', 'dera', 'buddhist', 'shinto'],
            'park': ['park', 'garden', 'botanical', 'nature'],
            'museum': ['museum', 'gallery', 'art', 'history', 'cultural'],
            'shopping': ['market', 'shopping', 'store', 'mall', 'department'],
            'hotel': ['hotel', 'ryokan', 'inn', 'accommodation'],
            'transport': ['station', 'airport', 'port', 'terminal']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None
    
    def _determine_cuisine_type(self, text):
        """Determine cuisine type from text."""
        cuisines = {
            'japanese': ['japanese', 'washoku', 'traditional'],
            'sushi': ['sushi', 'sashimi', 'sushiya'],
            'ramen': ['ramen', 'noodle'],
            'tempura': ['tempura'],
            'yakitori': ['yakitori', 'grilled'],
            'izakaya': ['izakaya', 'pub'],
            'western': ['western', 'american', 'european'],
            'chinese': ['chinese', 'chuka'],
            'korean': ['korean', 'kankoku'],
            'italian': ['italian', 'pasta', 'pizza'],
            'cafe': ['cafe', 'coffee', 'tea'],
            'dessert': ['dessert', 'sweet', 'cake', 'ice cream']
        }
        
        for cuisine, keywords in cuisines.items():
            if any(keyword in text for keyword in keywords):
                return cuisine
        return None
    
    def run_enhancement(self):
        """Run the complete enhancement process."""
        print("Starting data model enhancement...")
        
        # Step 1: Analyze current data
        self.analyze_place_names()
        
        # Step 2: Create new node types
        self.create_activity_categories()
        self.create_cuisine_types()
        
        # Step 3: Categorize existing places
        self.categorize_places()
        
        print("Data model enhancement completed!")
    
    def close(self):
        self.driver.close()

def main():
    enhancer = DataModelEnhancer()
    try:
        enhancer.run_enhancement()
    finally:
        enhancer.close()

if __name__ == "__main__":
    main()
