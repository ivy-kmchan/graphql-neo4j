# Cypher Queries for Testing

This directory contains Cypher queries that you can run directly in Neo4j Browser or Neo4j Aura.

## How to Use in Neo4j Aura

1. **Open Neo4j Browser** in your Aura instance
2. **Copy and paste** the query from the `.cypher` file
3. **Run the query** (press Enter or click the play button)

## Available Queries

### `cafes_in_hokkaido.cypher`
- **Purpose**: Find all cafes in Hokkaido using exact match
- **Matches**: Direct script query logic
- **Usage**: Copy and paste directly into Neo4j Browser

### `cafes_in_hokkaido_chatbot_version.cypher`
- **Purpose**: Find cafes in Hokkaido using case-insensitive matching
- **Matches**: Chatbot query logic (after the fix)
- **Usage**: 
  - Option 1: Use with hardcoded values (copy and paste)
  - Option 2: Use with parameters (set parameters first, then run query)

## Using Parameters in Neo4j Browser

To use parameters in Neo4j Browser:

1. Type `:param` in the query box
2. Set your parameters:
   ```
   :param cuisine => 'cafe'
   :param location => 'Hokkaido'
   ```
3. Then run the query that uses `$cuisine` and `$location`

## Expected Results

Both queries should return **7 cafes** in Hokkaido:
1. CAFE de ROMAN Moiwa
2. Cafe Creperiz
3. Okurayama Tukimisou cafe
4. Popura Farm Cafe
5. Saera coffee & Sandwiches
6. cafe coucou
7. 六'cafe

