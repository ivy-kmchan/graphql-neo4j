#!/usr/bin/env python3
"""
LangChain integration with Neo4j for travel chatbot.
This module provides natural language querying capabilities for the travel database.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

load_dotenv()

class TravelChatbot:
    """Travel chatbot using LangChain and Neo4j integration."""
    
    def __init__(self):
        """Initialize the chatbot with Neo4j connection and LLM."""
        self.uri = os.getenv("NEO4J_URI")  # Required - set in .env
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")  # Required - set in .env
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")  # Changed from 'travel' to 'neo4j' for Aura
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize LLM (you'll need to set OPENAI_API_KEY in .env)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,  # Lower temperature for more factual responses
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define tools for the agent
        self.tools = self._create_tools()
        
        # Initialize agent with strict database-only mode
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            max_iterations=3,  # Limit attempts to prevent hallucination
            early_stopping_method="force",  # Stop early instead of guessing
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the LangChain agent."""
        return [
            Tool(
                name="search_places_by_location",
                description="Search for places in a specific prefecture or region",
                func=self._search_places_by_location
            ),
            Tool(
                name="search_places_by_activity",
                description="Find places by activity type (restaurant, temple, park, etc.)",
                func=self._search_places_by_activity
            ),
            Tool(
                name="search_places_by_cuisine",
                description="Find places that serve specific cuisine types (sushi, ramen, cafe, etc.). Can handle singular or plural forms.",
                func=self._search_places_by_cuisine
            ),
            Tool(
                name="search_cuisine_by_location",
                description="Find places serving specific cuisine in a specific location (e.g., 'cafes in Tokyo', 'sushi in Kyoto'). Use this when the query includes both a cuisine type AND a location.",
                func=self._search_cuisine_by_location
            ),
            Tool(
                name="search_places_nearby",
                description="Find places near specific coordinates or within a prefecture",
                func=self._search_places_nearby
            ),
            Tool(
                name="get_place_details",
                description="Get detailed information about a specific place. Returns 'Place not found' if the place doesn't exist in the database. DO NOT make up information if the place is not found.",
                func=self._get_place_details
            ),
            Tool(
                name="search_restaurants",
                description="Find restaurants with optional cuisine filtering",
                func=self._search_restaurants
            ),
            Tool(
                name="search_temples",
                description="Find temples and shrines",
                func=self._search_temples
            ),
            Tool(
                name="get_place_count",
                description="Get the total number of places in the database",
                func=self._get_place_count
            )
        ]
    
    def _run_cypher_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def _search_places_by_location(self, location: str) -> str:
        """Search for places in a specific location."""
        query = """
        MATCH (p:Place)
        WHERE p.prefecture CONTAINS $location OR p.address CONTAINS $location
        RETURN p.name as name, p.address as address, p.prefecture as prefecture, 
               p.latitude as latitude, p.longitude as longitude, p.description as description
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"location": location})
        
        if not results:
            return f"No places found in {location}"
        
        response = f"🗾 **Found {len(results)} places in {location}:**\n\n"
        for i, place in enumerate(results, 1):
            response += f"**{i}. {place['name']}**\n"
            response += f"📍 {place['address']}\n"
            if place['description']:
                response += f"📝 {place['description']}\n"
            response += "\n"
        
        return response
    
    def _search_places_by_activity(self, activity: str) -> str:
        """Find places by activity type."""
        query = """
        MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
        WHERE ac.name CONTAINS $activity
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               collect(ac.name) as activities
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"activity": activity.lower()})
        
        if not results:
            return f"No {activity} places found"
        
        response = f"🏛️ **Found {len(results)} {activity} places:**\n\n"
        for i, place in enumerate(results, 1):
            response += f"**{i}. {place['name']}**\n"
            response += f"📍 {place['address']}\n"
            response += f"🎯 Activities: {', '.join(place['activities'])}\n\n"
        
        return response
    
    def _search_places_by_cuisine(self, cuisine: str) -> str:
        """Find places that serve specific cuisine."""
        # Normalize common plural forms and variations
        cuisine_normalized = cuisine.lower().rstrip('s')  # Remove trailing 's' for plural
        
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(ct:CuisineType)
        WHERE toLower(ct.name) CONTAINS $cuisine OR $cuisine CONTAINS toLower(ct.name)
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               collect(ct.name) as cuisines
        LIMIT 10
        """
        results = self._run_cypher_query(query, {"cuisine": cuisine_normalized})
        
        if not results:
            return f"No places serving {cuisine} cuisine found"
        
        response = f"🍜 **Found {len(results)} places serving {cuisine} cuisine:**\n\n"
        for i, place in enumerate(results, 1):
            response += f"**{i}. {place['name']}**\n"
            response += f"📍 {place['address']}\n"
            response += f"🍽️ Cuisines: {', '.join(place['cuisines'])}\n\n"
        
        return response
    
    def _search_cuisine_by_location(self, query_input: str) -> str:
        """Find places serving specific cuisine in a specific location.
        Handles queries like 'cafes in Tokyo' or 'sushi restaurants in Kyoto'.
        """
        # Try to parse the input to extract cuisine and location
        # Common patterns: "X in Y", "Y X"
        parts = query_input.lower().split(' in ')
        
        if len(parts) == 2:
            cuisine = parts[0].strip().rstrip('s')  # Remove trailing 's'
            location = parts[1].strip()
        else:
            # Try to split by common location keywords
            words = query_input.lower().split()
            if len(words) >= 2:
                cuisine = words[0].rstrip('s')
                location = ' '.join(words[1:])
            else:
                return "Please specify both a cuisine type and location (e.g., 'cafes in Tokyo')"
        
        query = """
        MATCH (p:Place)-[:SERVES_CUISINE]->(ct:CuisineType)
        WHERE (toLower(ct.name) CONTAINS $cuisine OR $cuisine CONTAINS toLower(ct.name))
          AND (p.prefecture CONTAINS $location OR p.address CONTAINS $location)
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               collect(ct.name) as cuisines
        LIMIT 15
        """
        results = self._run_cypher_query(query, {
            "cuisine": cuisine,
            "location": location.title()  # Capitalize location for better matching
        })
        
        if not results:
            return f"No {cuisine} places found in {location}. Try a broader search or check the spelling."
        
        response = f"🍜 **Found {len(results)} {cuisine} places in {location}:**\n\n"
        for i, place in enumerate(results, 1):
            response += f"**{i}. {place['name']}**\n"
            response += f"📍 {place['address']}\n"
            if place['prefecture']:
                response += f"🗾 Prefecture: {place['prefecture']}\n"
            response += f"🍽️ Cuisines: {', '.join(place['cuisines'])}\n\n"
        
        return response
    
    def _search_places_nearby(self, location: str) -> str:
        """Find places near a location."""
        # This is a simplified version - in a real app, you'd use spatial queries
        return self._search_places_by_location(location)
    
    def _get_place_details(self, place_name: str) -> str:
        """Get detailed information about a specific place."""
        query = """
        MATCH (p:Place)
        WHERE p.name CONTAINS $place_name
        OPTIONAL MATCH (p)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
        OPTIONAL MATCH (p)-[:SERVES_CUISINE]->(ct:CuisineType)
        OPTIONAL MATCH (p)-[:HAS_PLACE]-(r:Region)
        RETURN p.name as name, p.address as address, p.prefecture as prefecture,
               p.latitude as latitude, p.longitude as longitude, p.description as description,
               p.google_maps_url as maps_url, p.visited as visited,
               collect(DISTINCT ac.name) as activities,
               collect(DISTINCT ct.name) as cuisines,
               collect(DISTINCT r.name) as regions
        LIMIT 1
        """
        results = self._run_cypher_query(query, {"place_name": place_name})
        
        if not results:
            return f"❌ '{place_name}' not found in your travel database. This place is not in your saved places. Only information about places you have saved is available."
        
        place = results[0]
        response = f"📍 {place['name']}\n"
        response += f"Address: {place['address']}\n"
        response += f"Prefecture: {place['prefecture']}\n"
        if place['description']:
            response += f"Description: {place['description']}\n"
        if place['activities']:
            response += f"Activities: {', '.join(place['activities'])}\n"
        if place['cuisines']:
            response += f"Cuisines: {', '.join(place['cuisines'])}\n"
        if place['maps_url']:
            response += f"Maps: {place['maps_url']}\n"
        response += f"Visited: {'Yes' if place['visited'] else 'No'}\n"
        
        return response
    
    def _search_restaurants(self, cuisine: str = None) -> str:
        """Find restaurants with optional cuisine filtering."""
        if cuisine:
            query = """
            MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
            WHERE ac.name = 'restaurant'
            OPTIONAL MATCH (p)-[:SERVES_CUISINE]->(ct:CuisineType)
            WHERE ct.name CONTAINS $cuisine
            RETURN p.name as name, p.address as address, p.prefecture as prefecture,
                   collect(DISTINCT ct.name) as cuisines
            LIMIT 10
            """
            results = self._run_cypher_query(query, {"cuisine": cuisine.lower()})
        else:
            query = """
            MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
            WHERE ac.name = 'restaurant'
            OPTIONAL MATCH (p)-[:SERVES_CUISINE]->(ct:CuisineType)
            RETURN p.name as name, p.address as address, p.prefecture as prefecture,
                   collect(DISTINCT ct.name) as cuisines
            LIMIT 10
            """
            results = self._run_cypher_query(query)
        
        if not results:
            cuisine_text = f" serving {cuisine}" if cuisine else ""
            return f"No restaurants{cuisine_text} found"
        
        response = f"Found {len(results)} restaurants"
        if cuisine:
            response += f" serving {cuisine} cuisine"
        response += ":\n"
        
        for place in results:
            response += f"• {place['name']} - {place['address']}\n"
            if place['cuisines']:
                response += f"  Cuisines: {', '.join(place['cuisines'])}\n"
        
        return response
    
    def _search_temples(self, location: str = None) -> str:
        """Find temples and shrines."""
        if location:
            query = """
            MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
            WHERE ac.name = 'temple' AND (p.prefecture CONTAINS $location OR p.address CONTAINS $location)
            RETURN p.name as name, p.address as address, p.prefecture as prefecture
            LIMIT 10
            """
            results = self._run_cypher_query(query, {"location": location})
        else:
            query = """
            MATCH (p:Place)-[:HAS_ACTIVITY]->(ac:ActivityCategory)
            WHERE ac.name = 'temple'
            RETURN p.name as name, p.address as address, p.prefecture as prefecture
            LIMIT 10
            """
            results = self._run_cypher_query(query)
        
        if not results:
            location_text = f" in {location}" if location else ""
            return f"No temples found{location_text}"
        
        response = f"Found {len(results)} temples"
        if location:
            response += f" in {location}"
        response += ":\n"
        
        for place in results:
            response += f"• {place['name']} - {place['address']}\n"
        
        return response
    
    def _get_place_count(self, query: str = "") -> str:
        """Get the total number of places."""
        count_query = "MATCH (p:Place) RETURN count(p) as count"
        results = self._run_cypher_query(count_query)
        count = results[0]['count'] if results else 0
        return f"There are {count} places in the travel database."
    
    def chat(self, user_input: str) -> str:
        """Process user input and return response."""
        try:
            response = self.agent.run(input=user_input)
            return response
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def main():
    """Test the chatbot functionality."""
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY in your .env file")
        print("Add this line to your .env file:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        return
    
    print("🤖 Travel Chatbot initialized!")
    print("✅ Use the Streamlit interface at: http://localhost:8502")
    print("🔗 Or use the GraphQL API at: http://localhost:4010")
    print("\nThe chatbot is ready to answer questions about your travel data!")

if __name__ == "__main__":
    main()
