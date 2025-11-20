#!/usr/bin/env python3
"""
Export Neo4j database to CSV files for data inspection.
Creates separate CSV files for places, activities, cuisines, and relationships.
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def export_places(session, output_dir='exports'):
    """Export all Place nodes to CSV."""
    
    query = """
    MATCH (p:Place)
    OPTIONAL MATCH (p)-[:HAS_ACTIVITY]->(a:ActivityCategory)
    OPTIONAL MATCH (p)-[:SERVES_CUISINE]->(c:CuisineType)
    OPTIONAL MATCH (p)<-[:HAS_PLACE]-(r:Region)
    RETURN p.name as name,
           p.address as address,
           p.prefecture as prefecture,
           p.latitude as latitude,
           p.longitude as longitude,
           p.description as description,
           p.type as type,
           p.savedList as savedList,
           p.visited as visited,
           p.dateSaved as dateSaved,
           p.googleMapsUrl as googleMapsUrl,
           collect(DISTINCT a.name) as activities,
           collect(DISTINCT c.name) as cuisines,
           collect(DISTINCT r.name) as regions
    ORDER BY p.name
    """
    
    result = session.run(query)
    records = list(result)
    
    if not records:
        print("No places found in database")
        return 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Export to CSV
    csv_file = os.path.join(output_dir, 'places.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'name', 'address', 'prefecture', 'latitude', 'longitude',
            'description', 'type', 'savedList', 'visited', 'dateSaved',
            'googleMapsUrl', 'activities', 'cuisines', 'regions'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            row = {
                'name': record['name'],
                'address': record['address'],
                'prefecture': record['prefecture'],
                'latitude': record['latitude'],
                'longitude': record['longitude'],
                'description': record['description'],
                'type': record['type'],
                'savedList': record['savedList'],
                'visited': record['visited'],
                'dateSaved': record['dateSaved'],
                'googleMapsUrl': record['googleMapsUrl'],
                'activities': ', '.join([a for a in record['activities'] if a]),
                'cuisines': ', '.join([c for c in record['cuisines'] if c]),
                'regions': ', '.join([r for r in record['regions'] if r])
            }
            writer.writerow(row)
    
    print(f"✅ Exported {len(records)} places to {csv_file}")
    return len(records)


def export_activity_categories(session, output_dir='exports'):
    """Export ActivityCategory nodes with place counts."""
    
    query = """
    MATCH (ac:ActivityCategory)
    OPTIONAL MATCH (ac)<-[:HAS_ACTIVITY]-(p:Place)
    RETURN ac.name as name,
           ac.description as description,
           count(p) as place_count
    ORDER BY place_count DESC
    """
    
    result = session.run(query)
    records = list(result)
    
    csv_file = os.path.join(output_dir, 'activity_categories.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'description', 'place_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'name': record['name'],
                'description': record['description'],
                'place_count': record['place_count']
            })
    
    print(f"✅ Exported {len(records)} activity categories to {csv_file}")
    return len(records)


def export_cuisine_types(session, output_dir='exports'):
    """Export CuisineType nodes with place counts."""
    
    query = """
    MATCH (ct:CuisineType)
    OPTIONAL MATCH (ct)<-[:SERVES_CUISINE]-(p:Place)
    RETURN ct.name as name,
           ct.description as description,
           count(p) as place_count
    ORDER BY place_count DESC
    """
    
    result = session.run(query)
    records = list(result)
    
    csv_file = os.path.join(output_dir, 'cuisine_types.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'description', 'place_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'name': record['name'],
                'description': record['description'],
                'place_count': record['place_count']
            })
    
    print(f"✅ Exported {len(records)} cuisine types to {csv_file}")
    return len(records)


def export_regions(session, output_dir='exports'):
    """Export Region nodes with place counts."""
    
    query = """
    MATCH (r:Region)
    OPTIONAL MATCH (r)-[:HAS_PLACE]->(p:Place)
    RETURN r.name as name,
           count(p) as place_count
    ORDER BY place_count DESC
    """
    
    result = session.run(query)
    records = list(result)
    
    csv_file = os.path.join(output_dir, 'regions.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'place_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'name': record['name'],
                'place_count': record['place_count']
            })
    
    print(f"✅ Exported {len(records)} regions to {csv_file}")
    return len(records)


def export_sample_relationships(session, output_dir='exports'):
    """Export sample relationships for inspection."""
    
    # HAS_ACTIVITY relationships
    query = """
    MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory)
    RETURN p.name as place_name,
           a.name as activity,
           p.prefecture as prefecture
    LIMIT 100
    """
    
    result = session.run(query)
    records = list(result)
    
    csv_file = os.path.join(output_dir, 'sample_activity_relationships.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['place_name', 'activity', 'prefecture']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'place_name': record['place_name'],
                'activity': record['activity'],
                'prefecture': record['prefecture']
            })
    
    print(f"✅ Exported {len(records)} sample activity relationships to {csv_file}")
    
    # SERVES_CUISINE relationships
    query = """
    MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType)
    RETURN p.name as place_name,
           c.name as cuisine,
           p.prefecture as prefecture
    LIMIT 100
    """
    
    result = session.run(query)
    records = list(result)
    
    csv_file = os.path.join(output_dir, 'sample_cuisine_relationships.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['place_name', 'cuisine', 'prefecture']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'place_name': record['place_name'],
                'cuisine': record['cuisine'],
                'prefecture': record['prefecture']
            })
    
    print(f"✅ Exported {len(records)} sample cuisine relationships to {csv_file}")


def export_database_summary(session, output_dir='exports'):
    """Export database statistics summary."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    queries = {
        'total_places': "MATCH (p:Place) RETURN count(p) as count",
        'total_regions': "MATCH (r:Region) RETURN count(r) as count",
        'total_activities': "MATCH (a:ActivityCategory) RETURN count(a) as count",
        'total_cuisines': "MATCH (c:CuisineType) RETURN count(c) as count",
        'has_activity_rels': "MATCH ()-[r:HAS_ACTIVITY]->() RETURN count(r) as count",
        'serves_cuisine_rels': "MATCH ()-[r:SERVES_CUISINE]->() RETURN count(r) as count",
        'has_place_rels': "MATCH ()-[r:HAS_PLACE]->() RETURN count(r) as count",
        'places_with_coordinates': "MATCH (p:Place) WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL RETURN count(p) as count",
        'visited_places': "MATCH (p:Place) WHERE p.visited = true RETURN count(p) as count"
    }
    
    summary = {}
    for key, query in queries.items():
        result = session.run(query)
        summary[key] = result.single()['count']
    
    csv_file = os.path.join(output_dir, 'database_summary.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['metric', 'count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for key, value in summary.items():
            writer.writerow({'metric': key, 'count': value})
    
    print(f"✅ Exported database summary to {csv_file}")
    
    # Print summary to console
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("=" * 60)


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f'exports/export_{timestamp}'
    
    print("=" * 60)
    print("EXPORT NEO4J DATABASE TO CSV")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    print(f"Output directory: {output_dir}\n")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Export all data
            export_database_summary(session, output_dir)
            print()
            export_places(session, output_dir)
            export_activity_categories(session, output_dir)
            export_cuisine_types(session, output_dir)
            export_regions(session, output_dir)
            export_sample_relationships(session, output_dir)
        
        driver.close()
        
        print("\n" + "=" * 60)
        print("✅ EXPORT COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nAll files exported to: {output_dir}/")
        print("\nFiles created:")
        print("  - database_summary.csv")
        print("  - places.csv (all places with activities & cuisines)")
        print("  - activity_categories.csv")
        print("  - cuisine_types.csv")
        print("  - regions.csv")
        print("  - sample_activity_relationships.csv (first 100)")
        print("  - sample_cuisine_relationships.csv (first 100)")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

