# 🚀 How to Start Your Japan Travel Chatbot

This guide explains the different ways to initiate and run your travel chatbot system.

## 📋 Prerequisites

Before starting the chatbot, ensure these services are running:

1. **Neo4j Desktop** - Your graph database
2. **GraphQL API Server** - Provides data access layer

## 🎯 Main Chatbot Scripts

### **1. Streamlit Chatbot (Recommended)**
The primary web-based interface for interacting with your travel data.

```bash
.\.venv\Scripts\python.exe -m streamlit run scripts/streamlit_chatbot.py
```

- **URL**: `http://localhost:8501`
- **Features**: 
  - Interactive web interface
  - Database statistics sidebar
  - Example questions
  - Real-time chat
- **Best for**: Daily use and interactive exploration

### **2. Batch Files (Easiest)**
Pre-configured batch files for quick startup.

#### Start Everything
```bash
start_chatbot.bat
```
- Starts both GraphQL API and Streamlit chatbot
- Opens browser automatically

#### Start Chatbot Only
```bash
run_chatbot.bat
```
- Starts only the Streamlit chatbot
- Requires GraphQL API to be running separately

### **3. Direct Python Script**
For testing without web interface.

```bash
.\.venv\Scripts\python.exe utility_scripts/simple_chatbot_test.py
```
- Command-line interface
- Good for debugging and testing

## 📁 File Structure

```
scripts/
├── streamlit_chatbot.py          # Main web interface
├── langchain_neo4j_integration.py # Core chatbot logic
└── index.js                      # GraphQL API server

utility_scripts/
├── simple_chatbot_test.py        # Command-line test
└── test_connection.py            # Database connection test

Batch Files:
├── start_chatbot.bat             # Start everything
└── run_chatbot.bat               # Start chatbot only
```

## 🔄 Complete Startup Workflow

### **Step 1: Start Neo4j Desktop**
1. Open Neo4j Desktop
2. Start your "travel" database instance
3. Verify it's running (green status)

### **Step 2: Start GraphQL API**
```bash
node scripts/index.js
```
- **URL**: `http://localhost:4010`
- **Status**: Look for "🚀 GraphQL API ready at http://localhost:4010/ (DB: travel)"

### **Step 3: Start Streamlit Chatbot**
```bash
.\.venv\Scripts\python.exe -m streamlit run scripts/streamlit_chatbot.py
```
- **URL**: `http://localhost:8501`
- **Status**: Look for "You can now view your Streamlit app in your browser"

### **Step 4: Open Browser**
Navigate to `http://localhost:8501` to start chatting!

## 🛠️ Troubleshooting

### **Common Issues:**

1. **"ModuleNotFoundError: No module named 'neo4j'"**
   - Solution: Use the virtual environment Python executable
   - Command: `.\.venv\Scripts\python.exe -m streamlit run scripts/streamlit_chatbot.py`

2. **"EADDRINUSE: address already in use"**
   - Solution: Kill existing processes or change ports
   - Check: `netstat -ano | findstr :4010` or `netstat -ano | findstr :8501`

3. **"Database not found"**
   - Solution: Ensure Neo4j Desktop is running and database is started
   - Check: Neo4j Browser connection

4. **"OpenAI API key not found"**
   - Solution: Add `OPENAI_API_KEY=your_key_here` to `.env` file

### **Quick Health Check:**
```bash
# Test database connection
.\.venv\Scripts\python.exe utility_scripts/test_connection.py

# Test GraphQL API
curl http://localhost:4010/graphql -H "Content-Type: application/json" -d "{\"query\":\"query { placesCount }\"}"
```

## 🎯 Recommended Usage

### **For Daily Use:**
1. Use `start_chatbot.bat` for one-click startup
2. Bookmark `http://localhost:8501` in your browser
3. Keep Neo4j Desktop running in background

### **For Development:**
1. Start services individually for better debugging
2. Use `utility_scripts/simple_chatbot_test.py` for quick tests
3. Monitor terminal output for errors

## 📊 What You'll See

### **Streamlit Interface:**
- **Left Sidebar**: Database statistics, clear chat button
- **Main Chat**: Interactive conversation area
- **Right Panel**: Example questions and available tools

### **Database Statistics:**
- Total places count (2,625 places)
- Top activity categories
- Top cuisine types
- Real-time data from your Neo4j database

## 🔧 Advanced Configuration

### **Environment Variables (.env):**
```env
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testtest
NEO4J_DATABASE=travel
OPENAI_API_KEY=your_openai_api_key_here
PORT=4010
```

### **Custom Ports:**
- GraphQL API: Change `PORT` in `.env` or `scripts/index.js`
- Streamlit: Use `--server.port` flag
- Neo4j: Configure in Neo4j Desktop

## 🎉 You're Ready!

Once all services are running, you can:
- Ask about temples in Kyoto
- Find restaurants in Tokyo
- Explore places by prefecture
- Get detailed information about specific locations
- Search by cuisine type or activity

Your chatbot is now ready to help you explore your Japan travel data! 🗾
