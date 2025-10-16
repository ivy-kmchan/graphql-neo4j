#!/usr/bin/env python3
"""Verify the enhanced data model."""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session(database='travel') as session:
        # Check new node types
        result = session.run('CALL db.labels()')
        labels = [record['label'] for record in result]
        print('Enhanced node types:', labels)
        
        # Check new relationship types
        result = session.run('CALL db.relationshipTypes()')
        rel_types = [record['relationshipType'] for record in result]
        print('Enhanced relationship types:', rel_types)
        
        # Check activity categories
        result = session.run('''
            MATCH (a:ActivityCategory) 
            RETURN a.name, count{(a)<-[:HAS_ACTIVITY]-(p:Place)} as place_count 
            ORDER BY place_count DESC
        ''')
        print('\nActivity categories with place counts:')
        for record in result:
            name = record['a.name']
            count = record['place_count']
            print(f'  {name}: {count} places')
        
        # Check cuisine types
        result = session.run('''
            MATCH (c:CuisineType) 
            RETURN c.name, count{(c)<-[:SERVES_CUISINE]-(p:Place)} as place_count 
            ORDER BY place_count DESC
        ''')
        print('\nCuisine types with place counts:')
        for record in result:
            name = record['c.name']
            count = record['place_count']
            print(f'  {name}: {count} places')
        
        # Sample categorized places
        result = session.run('''
            MATCH (p:Place)-[:HAS_ACTIVITY]->(a:ActivityCategory)
            RETURN p.name, a.name as activity
            LIMIT 5
        ''')
        print('\nSample categorized places:')
        for record in result:
            name = record['p.name']
            activity = record['activity']
            print(f'  {name} -> {activity}')
    
    driver.close()

if __name__ == "__main__":
    main()
