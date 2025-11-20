#!/usr/bin/env python3
"""Clear all data from Neo4j database."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def main():
    uri = os.getenv("NEO4J_URI")  # Required - set in .env
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")  # Required - set in .env
    database = os.getenv("NEO4J_DATABASE", "neo4j")  # Changed from 'travel' to 'neo4j' for Aura
    
    if not password:
        print("ERROR: NEO4J_PASSWORD not set in .env file")
        return 1
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session(database=database) as session:
            # Drop all constraints
            result = session.run("SHOW CONSTRAINTS")
            for record in result:
                constraint_name = record["name"]
                session.run(f"DROP CONSTRAINT {constraint_name}")
                print(f"Dropped constraint: {constraint_name}")
            
            # Delete all relationships
            session.run("MATCH ()-[r]-() DELETE r")
            print("Deleted all relationships")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            print("Deleted all nodes")
            
            print("Database cleared successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        driver.close()
    
    return 0

if __name__ == "__main__":
    exit(main())
