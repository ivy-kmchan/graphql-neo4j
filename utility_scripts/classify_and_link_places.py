#!/usr/bin/env python3
"""
Intelligently classify Places and link them to ActivityCategories and CuisineTypes.
Analyzes place names, addresses, and descriptions to determine appropriate categories.
"""

import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


# Keywords for activity classification
ACTIVITY_KEYWORDS = {
    'temple': [
        'temple', 'shrine', '寺', '神社', 'jinja', 'tera', 'dera', 'ji',
        'hongan', 'yasaka', 'fushimi', 'sensoji', 'kiyomizu', 'todai'
    ],
    'park': [
        'park', 'garden', 'gardens', '公園', 'koen', 'yama', 'mountain',
        'forest', 'onsen town', 'natural', 'gorge', 'valley'
    ],
    'museum': [
        'museum', 'gallery', 'art', '美術館', 'hakubutsukan', 'bijutsukan',
        'memorial', 'exhibition', 'cultural center'
    ],
    'transport': [
        'station', 'airport', 'terminal', 'port', '駅', 'eki',
        'bus stop', 'train', 'railway', 'subway'
    ],
    'hotel': [
        'hotel', 'hostel', 'inn', 'ryokan', 'resort', 'lodge',
        'accommodation', 'guesthouse', '旅館', 'villa'
    ],
    'shopping': [
        'market', 'shop', 'mall', 'store', 'shopping', 'mart',
        'center', 'depato', 'bazaar', 'arcade', 'marche'
    ],
    'entertainment': [
        'aquarium', 'zoo', 'theater', 'cinema', 'dome', 'arena',
        'entertainment', 'amusement', 'tower', 'observation'
    ],
    'historical': [
        'castle', 'fort', 'palace', 'historic', 'heritage',
        'monument', 'ruins', '城', 'shiro', 'jo'
    ],
    'nature': [
        'beach', 'lake', 'river', 'waterfall', 'island', 'cape',
        'cliff', 'cave', 'hot spring', 'onsen', 'matsuri'
    ]
}

# Keywords for cuisine classification
CUISINE_KEYWORDS = {
    'sushi': ['sushi', 'すし', '寿司', 'sushiro', 'kura'],
    'ramen': ['ramen', 'ラーメン', '拉麺', 'ichiran', 'ippudo'],
    'cafe': ['cafe', 'café', 'coffee', 'カフェ', 'kissaten', 'starbucks'],
    'tempura': ['tempura', '天ぷら', 'てんぷら'],
    'yakitori': ['yakitori', '焼き鳥', 'torikizoku'],
    'izakaya': ['izakaya', '居酒屋', 'tachinomi'],
    'japanese': ['kaiseki', '懐石', 'teishoku', 'bento', '弁当', 'washoku'],
    'italian': ['italian', 'pizza', 'pasta', 'イタリアン', 'trattoria'],
    'chinese': ['chinese', '中華', 'chuka', 'gyoza'],
    'korean': ['korean', 'yakiniku', '焼肉', '韓国', 'bulgogi'],
    'dessert': ['dessert', 'sweets', 'cake', 'ice cream', 'parfait', 'wagashi'],
    'western': ['western', 'steak', 'grill', 'bistro']
}

# Restaurant indicators
RESTAURANT_INDICATORS = [
    'restaurant', 'dining', 'kitchen', 'bar', 'grill', 'bistro',
    'eatery', 'shokudo', '食堂', 'taberu', 'gohan'
]


def classify_activity(name, address, description):
    """Classify a place into activity categories based on text analysis."""
    text = f"{name} {address} {description}".lower()
    matches = []
    
    for activity, keywords in ACTIVITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(activity)
                break  # Only count once per category
    
    # Special case: if it looks like a restaurant, it's probably not other categories
    is_restaurant = any(indicator in text for indicator in RESTAURANT_INDICATORS)
    if is_restaurant:
        matches = ['restaurant'] if 'restaurant' not in matches else matches
    
    return list(set(matches))  # Remove duplicates


def classify_cuisine(name, address, description):
    """Classify a place into cuisine types based on text analysis."""
    text = f"{name} {address} {description}".lower()
    matches = []
    
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(cuisine)
                break  # Only count once per category
    
    return list(set(matches))  # Remove duplicates


def classify_and_link_places(session, batch_size=100):
    """Classify all places and create relationships."""
    
    print("\n🔍 Analyzing places and creating relationships...\n")
    
    # Get all places
    query = """
    MATCH (p:Place)
    RETURN p.name as name, 
           p.address as address, 
           p.description as description,
           id(p) as id
    """
    
    result = session.run(query)
    places = [
        {
            'id': record['id'],
            'name': record['name'] or '',
            'address': record['address'] or '',
            'description': record['description'] or ''
        }
        for record in result
    ]
    
    print(f"Found {len(places)} places to classify")
    
    activity_stats = {}
    cuisine_stats = {}
    activity_links = 0
    cuisine_links = 0
    
    # Process in batches
    for i in range(0, len(places), batch_size):
        batch = places[i:i + batch_size]
        
        for place in batch:
            # Classify activities
            activities = classify_activity(
                place['name'], 
                place['address'], 
                place['description']
            )
            
            if activities:
                # Create HAS_ACTIVITY relationships
                for activity in activities:
                    link_query = """
                    MATCH (p:Place), (ac:ActivityCategory {name: $activity})
                    WHERE id(p) = $place_id
                      AND NOT EXISTS((p)-[:HAS_ACTIVITY]->(ac))
                    CREATE (p)-[:HAS_ACTIVITY]->(ac)
                    RETURN count(*) as created
                    """
                    result = session.run(link_query, place_id=place['id'], activity=activity)
                    created = result.single()['created']
                    activity_links += created
                    activity_stats[activity] = activity_stats.get(activity, 0) + created
            
            # Classify cuisines
            cuisines = classify_cuisine(
                place['name'], 
                place['address'], 
                place['description']
            )
            
            if cuisines:
                # Create SERVES_CUISINE relationships
                for cuisine in cuisines:
                    link_query = """
                    MATCH (p:Place), (c:CuisineType {name: $cuisine})
                    WHERE id(p) = $place_id
                      AND NOT EXISTS((p)-[:SERVES_CUISINE]->(c))
                    CREATE (p)-[:SERVES_CUISINE]->(c)
                    RETURN count(*) as created
                    """
                    result = session.run(link_query, place_id=place['id'], cuisine=cuisine)
                    created = result.single()['created']
                    cuisine_links += created
                    cuisine_stats[cuisine] = cuisine_stats.get(cuisine, 0) + created
        
        # Progress indicator
        if (i + batch_size) % 500 == 0:
            print(f"  Processed {min(i + batch_size, len(places))} / {len(places)} places...")
    
    print(f"\n✅ Created {activity_links} HAS_ACTIVITY relationships")
    print(f"✅ Created {cuisine_links} SERVES_CUISINE relationships\n")
    
    # Show activity distribution
    if activity_stats:
        print("Activity distribution:")
        for activity, count in sorted(activity_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {activity}: {count} places")
    
    # Show cuisine distribution
    if cuisine_stats:
        print("\nCuisine distribution:")
        for cuisine, count in sorted(cuisine_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cuisine}: {count} places")
    
    return activity_links, cuisine_links


def verify_results(session):
    """Show final statistics."""
    
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION")
    print("=" * 60)
    
    # Count nodes
    result = session.run("MATCH (ac:ActivityCategory) RETURN count(ac) as count")
    ac_count = result.single()['count']
    
    result = session.run("MATCH (c:CuisineType) RETURN count(c) as count")
    cuisine_count = result.single()['count']
    
    result = session.run("MATCH (p:Place) RETURN count(p) as count")
    place_count = result.single()['count']
    
    print(f"\nNodes:")
    print(f"  - Places: {place_count}")
    print(f"  - ActivityCategories: {ac_count}")
    print(f"  - CuisineTypes: {cuisine_count}")
    
    # Count relationships
    result = session.run("MATCH ()-[r:HAS_ACTIVITY]->() RETURN count(r) as count")
    activity_rel = result.single()['count']
    
    result = session.run("MATCH ()-[r:SERVES_CUISINE]->() RETURN count(r) as count")
    cuisine_rel = result.single()['count']
    
    print(f"\nRelationships:")
    print(f"  - HAS_ACTIVITY: {activity_rel}")
    print(f"  - SERVES_CUISINE: {cuisine_rel}")
    
    # Sample relationships
    if activity_rel > 0:
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
        RETURN p.name as place, collect(ac.name) as activities
        LIMIT 5
        """
        result = session.run(query)
        print(f"\nSample HAS_ACTIVITY relationships:")
        for record in result:
            activities = ', '.join(record['activities'])
            print(f"  - {record['place']}: {activities}")
    
    if cuisine_rel > 0:
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType)
        RETURN p.name as place, collect(c.name) as cuisines
        LIMIT 5
        """
        result = session.run(query)
        print(f"\nSample SERVES_CUISINE relationships:")
        for record in result:
            cuisines = ', '.join(record['cuisines'])
            print(f"  - {record['place']}: {cuisines}")


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print("=" * 60)
    print("CLASSIFY AND LINK PLACES")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Classify and link places
            classify_and_link_places(session)
            
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

