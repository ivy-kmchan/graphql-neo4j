#!/usr/bin/env python3
"""
Streamlit web interface for the travel chatbot.
This provides a user-friendly web interface for interacting with the travel data.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Add scripts directory to Python path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from langchain_neo4j_integration import TravelChatbot

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Japan Travel Chatbot",
    page_icon="🗾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        margin-right: 20%;
    }
    .stats-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Better list formatting */
    .bot-message ul, .bot-message ol {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
    }
    .bot-message li {
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False

def initialize_chatbot():
    """Initialize the chatbot if not already done."""
    if not st.session_state.initialized:
        with st.spinner("Initializing travel chatbot..."):
            try:
                st.session_state.chatbot = TravelChatbot()
                st.session_state.initialized = True
                st.success("✅ Chatbot initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize chatbot: {str(e)}")
                return False
    return True

def display_message(role: str, content: str):
    """Display a chat message with proper styling."""
    if role == "user":
        # User message with styling
        st.markdown(f"""
        <div class="user-message">
            <strong>👤 You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Bot message with styling and proper markdown rendering
        st.markdown(f"""
        <div class="bot-message">
            <strong>🤖 Travel Bot:</strong><br>
        </div>
        """, unsafe_allow_html=True)
        # Use st.markdown to properly render lists and formatting
        st.markdown(content)

def display_database_stats():
    """Display database statistics in the sidebar."""
    if st.session_state.chatbot:
        try:
            # Get place count
            place_count = st.session_state.chatbot._get_place_count()
            
            # Get activity categories
            activity_query = """
            MATCH (ac:ActivityCategory)
            OPTIONAL MATCH (ac)<-[:HAS_ACTIVITY]-(p:Place)
            RETURN ac.name as activity, count(p) as count
            ORDER BY count DESC
            """
            activities = st.session_state.chatbot._run_cypher_query(activity_query)
            
            # Get cuisine types
            cuisine_query = """
            MATCH (ct:CuisineType)
            OPTIONAL MATCH (ct)<-[:SERVES_CUISINE]-(p:Place)
            RETURN ct.name as cuisine, count(p) as count
            ORDER BY count DESC
            """
            cuisines = st.session_state.chatbot._run_cypher_query(cuisine_query)
            
            st.markdown("### 📊 Database Statistics")
            st.markdown(f"**{place_count}**")
            
            st.markdown("### 🏛️ Top Activities")
            for activity in activities[:5]:
                st.markdown(f"• **{activity['activity']}**: {activity['count']} places")
            
            st.markdown("### 🍜 Top Cuisines")
            for cuisine in cuisines[:5]:
                st.markdown(f"• **{cuisine['cuisine']}**: {cuisine['count']} places")
                
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🗾 Japan Travel Chatbot</h1>', unsafe_allow_html=True)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ Please set OPENAI_API_KEY in your .env file")
        st.code("OPENAI_API_KEY=your_openai_api_key_here")
        st.stop()
    
    # Initialize chatbot on page load to show stats
    if not st.session_state.initialized:
        initialize_chatbot()
    
    # Sidebar
    with st.sidebar:
        # Display database stats
        if st.session_state.initialized:
            display_database_stats()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 💬 Chat with your Travel Assistant")
        
        # Display chat messages
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])
        
        # Chat input - this will persist after each message
        prompt = st.chat_input("Ask me about places, restaurants, temples, or anything about your travel data...")
        
        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get bot response (chatbot already initialized on page load)
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chatbot.chat(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # Force a rerun to show the new messages
            st.rerun()
    
    with col2:
        st.markdown("### 💡 Example Questions")
        st.markdown("""
        **🏛️ Temples & Shrines:**
        - "Show me temples in Kyoto"
        - "Find shrines near Tokyo"
        
        **🍜 Food & Restaurants:**
        - "Where can I eat sushi?"
        - "Find ramen restaurants"
        - "Show me Japanese food places"
        
        **🗾 Locations:**
        - "What's in Tokyo?"
        - "Places in Osaka"
        - "Show me Kyoto attractions"
        
        **🔍 Specific Places:**
        - "Tell me about Senso-ji Temple"
        - "Details about Tokyo Station"
        """)
        
        st.markdown("### 🛠️ Available Tools")
        st.markdown("""
        The chatbot can help you:
        - 🔍 Search places by location
        - 🏛️ Find temples and shrines
        - 🍜 Locate restaurants by cuisine
        - 📍 Get place details
        - 🗾 Explore by prefecture
        """)

if __name__ == "__main__":
    main()
