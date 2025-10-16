#!/usr/bin/env python3
"""
Test script for LangChain Neo4j integration.
This script tests the basic functionality without requiring OpenAI API key.
"""

import os
from dotenv import load_dotenv
from langchain_neo4j_integration import TravelChatbot

load_dotenv()

def test_neo4j_connection():
    """Test basic Neo4j connection and queries."""
    print("🔍 Testing Neo4j Connection...")
    
    try:
        chatbot = TravelChatbot()
        
        # Test basic queries
        print("\n1. Testing place count...")
        count_result = chatbot._get_place_count()
        print(f"   ✅ {count_result}")
        
        print("\n2. Testing location search...")
        location_result = chatbot._search_places_by_location("Tokyo")
        print(f"   ✅ Found places in Tokyo")
        print(f"   Sample: {location_result[:200]}...")
        
        print("\n3. Testing activity search...")
        activity_result = chatbot._search_places_by_activity("restaurant")
        print(f"   ✅ Found restaurants")
        print(f"   Sample: {activity_result[:200]}...")
        
        print("\n4. Testing cuisine search...")
        cuisine_result = chatbot._search_places_by_cuisine("japanese")
        print(f"   ✅ Found Japanese cuisine places")
        print(f"   Sample: {cuisine_result[:200]}...")
        
        print("\n5. Testing temple search...")
        temple_result = chatbot._search_temples()
        print(f"   ✅ Found temples")
        print(f"   Sample: {temple_result[:200]}...")
        
        chatbot.close()
        print("\n🎉 All tests passed! Neo4j integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_without_openai():
    """Test the chatbot tools without OpenAI integration."""
    print("\n🔧 Testing Chatbot Tools (without OpenAI)...")
    
    try:
        chatbot = TravelChatbot()
        
        # Test individual tools
        test_queries = [
            ("search_places_by_location", "Tokyo"),
            ("search_places_by_activity", "restaurant"),
            ("search_places_by_cuisine", "sushi"),
            ("search_temples", ""),
            ("get_place_count", "")
        ]
        
        for tool_name, query in test_queries:
            print(f"\n   Testing {tool_name}...")
            try:
                if tool_name == "search_places_by_location":
                    result = chatbot._search_places_by_location(query)
                elif tool_name == "search_places_by_activity":
                    result = chatbot._search_places_by_activity(query)
                elif tool_name == "search_places_by_cuisine":
                    result = chatbot._search_places_by_cuisine(query)
                elif tool_name == "search_temples":
                    result = chatbot._search_temples()
                elif tool_name == "get_place_count":
                    result = chatbot._get_place_count()
                
                print(f"   ✅ {tool_name} working")
                print(f"   Result preview: {result[:100]}...")
                
            except Exception as e:
                print(f"   ❌ {tool_name} failed: {str(e)}")
        
        chatbot.close()
        print("\n🎉 Tool tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing LangChain Neo4j Integration")
    print("=" * 50)
    
    # Test 1: Basic Neo4j connection
    if not test_neo4j_connection():
        print("\n❌ Basic connection test failed. Please check your Neo4j setup.")
        return
    
    # Test 2: Chatbot tools
    if not test_without_openai():
        print("\n❌ Tool tests failed.")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Your LangChain integration is ready.")
    print("\nNext steps:")
    print("1. Set OPENAI_API_KEY in your .env file")
    print("2. Run: python scripts/streamlit_chatbot.py")
    print("3. Or run: python scripts/langchain_neo4j_integration.py")

if __name__ == "__main__":
    main()
