// Query to find cafes in Hokkaido (Chatbot version - case-insensitive)
// This matches what the chatbot uses after the fix
// Note: In Neo4j Browser, you can use parameters like $cuisine and $location

// Option 1: Direct query with hardcoded values
MATCH (p:Place)-[:SERVES_CUISINE]->(ct:CuisineType)
WHERE toLower(ct.name) = toLower('cafe')
  AND (toLower(p.prefecture) CONTAINS toLower('Hokkaido') OR toLower(p.address) CONTAINS toLower('Hokkaido'))
RETURN p.name as name, 
       p.address as address, 
       p.prefecture as prefecture,
       collect(ct.name) as cuisines
ORDER BY p.name
LIMIT 20;

// Option 2: Using parameters (recommended for Neo4j Browser)
// First, set parameters in Neo4j Browser:
// :param cuisine => 'cafe'
// :param location => 'Hokkaido'
// Then run:
MATCH (p:Place)-[:SERVES_CUISINE]->(ct:CuisineType)
WHERE toLower(ct.name) = toLower($cuisine)
  AND (toLower(p.prefecture) CONTAINS toLower($location) OR toLower(p.address) CONTAINS toLower($location))
RETURN p.name as name, 
       p.address as address, 
       p.prefecture as prefecture,
       collect(ct.name) as cuisines
ORDER BY p.name
LIMIT 20;

