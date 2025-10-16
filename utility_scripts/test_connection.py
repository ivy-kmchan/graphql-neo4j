#!/usr/bin/env python3
"""Test Neo4j connection."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "travel")
    
    print(f"Testing connection to: {uri}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set")
        return 1
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as session:
            result = session.run("RETURN 'Hello Neo4j!' as message")
            record = result.single()
            print(f"SUCCESS: {record['message']}")
            
            # Test database
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]
            print(f"Available databases: {databases}")
            
        driver.close()
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
