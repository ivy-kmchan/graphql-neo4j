// Query to find all cafes in Hokkaido
// This matches the direct script query (exact match for cuisine type)

MATCH (p:Place)-[:SERVES_CUISINE]->(c:CuisineType {name: 'cafe'})
WHERE p.prefecture CONTAINS 'Hokkaido'
RETURN p.name as name, 
       p.address as address, 
       p.prefecture as prefecture,
       p.latitude as latitude,
       p.longitude as longitude,
       p.google_maps_url as maps_url,
       p.visited as visited
ORDER BY p.name;

