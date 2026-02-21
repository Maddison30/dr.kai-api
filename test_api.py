#!/usr/bin/env python3
"""
Test script for Dr. KAI Medical Assistant API

This script demonstrates how to use the Dr. KAI API to get medical information
from approved Swedish sources.
"""

import requests
import json

# API configuration
API_URL = "http://localhost:8000"
API_KEY = "dr-kai-api-key-2024-secure-change-in-production"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_medical_query(query, conversation_id=None):
    """Test the medical query endpoint"""
    print(f"🏥 Testing medical query: '{query}'")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {"query": query}
    if conversation_id:
        data["conversation_id"] = conversation_id

    response = requests.post(
        f"{API_URL}/api/medical-query",
        headers=headers,
        json=data
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Conversation ID: {result['conversation_id']}")
        print(f"User Language: {result['user_language']}")
        print(f"Sources Used: {len(result['sources_used'])}")
        print(f"Response:\n{result['response']}\n")
        return result['conversation_id']
    else:
        print(f"Error: {response.text}\n")
        return None

def test_invalid_api_key():
    """Test with invalid API key"""
    print("🔒 Testing invalid API key...")
    headers = {
        "X-API-Key": "invalid-key",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_URL}/api/medical-query",
        headers=headers,
        json={"query": "Test query"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def main():
    print("🩺 Dr. KAI API Test Script")
    print("=" * 50)

    # Test health
    test_health()

    # Test medical queries in different languages
    queries = [
        "What should I do if my shoulder hurts when I raise my arm?",
        "Vad ska jag göra om min axel gör ont när jag lyfter armen?",
        "¿Qué debo hacer si me duele el hombro al levantar el brazo?"
    ]

    conversation_id = None
    for query in queries:
        conversation_id = test_medical_query(query, conversation_id)

    # Test invalid API key
    test_invalid_api_key()

    print("✅ API testing completed!")

if __name__ == "__main__":
    main()