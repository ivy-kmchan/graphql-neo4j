@echo off
echo 🚀 Starting Travel Chatbot System...
echo.

echo Step 1: Starting GraphQL API Server...
start "GraphQL API" cmd /k "node scripts/index.js"

echo Waiting 5 seconds for GraphQL server to start...
timeout /t 5 /nobreak > nul

echo Step 2: Starting Streamlit Chatbot...
start "Streamlit Chatbot" cmd /k ".venv\Scripts\python.exe -m streamlit run scripts/streamlit_chatbot.py"

echo.
echo ✅ Both services are starting up!
echo 🌐 GraphQL API: http://localhost:4010
echo 🤖 Chatbot UI: http://localhost:8501
echo.
echo Press any key to exit this window...
pause > nul
