#!/usr/bin/env python3
"""Verify environment configuration for Streamlit chatbot."""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("ENVIRONMENT CONFIGURATION CHECK")
print("=" * 70)

# Check Neo4j settings
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_database = os.getenv("NEO4J_DATABASE")
openai_key = os.getenv("OPENAI_API_KEY")

print("\n📊 Neo4j Configuration:")
print(f"  URI: {neo4j_uri}")
print(f"  User: {neo4j_user}")
print(f"  Password: {'*' * len(neo4j_password) if neo4j_password else 'NOT SET'}")
print(f"  Database: {neo4j_database if neo4j_database else 'neo4j (default)'}")

print("\n🤖 OpenAI Configuration:")
print(f"  API Key: {'✅ SET' if openai_key else '❌ NOT SET'}")

print("\n" + "=" * 70)

# Check for issues
issues = []
if not neo4j_uri:
    issues.append("❌ NEO4J_URI is not set")
elif "localhost" in neo4j_uri or "bolt://" in neo4j_uri:
    if "neo4j.io" not in neo4j_uri:
        issues.append("⚠️  NEO4J_URI appears to be localhost, not Neo4j Aura")
        
if not neo4j_password:
    issues.append("❌ NEO4J_PASSWORD is not set")

if not openai_key:
    issues.append("❌ OPENAI_API_KEY is not set (required for chatbot)")

if neo4j_database and neo4j_database != "neo4j":
    issues.append(f"⚠️  NEO4J_DATABASE is set to '{neo4j_database}', but Aura uses 'neo4j'")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
    print("\n💡 Tip: Make sure your .env file has:")
    print("  NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io")
    print("  NEO4J_USER=neo4j")
    print("  NEO4J_PASSWORD=your_password")
    print("  NEO4J_DATABASE=neo4j")
    print("  OPENAI_API_KEY=your_openai_key")
else:
    print("✅ All configuration looks good!")
    print("\n🚀 You can now run:")
    print("  streamlit run scripts/streamlit_chatbot.py")

print("=" * 70)

