#!/usr/bin/env python3
"""
ArchieAI API Demo Script

This script demonstrates how to use the ArchieAI API in Python.
It shows examples of:
- Generating an API key
- Sending chat messages
- Receiving streaming responses
- Managing API keys

Prerequisites:
1. Start the ArchieAI API server: python api.py
2. Run this demo: python api_demo.py

For TypeScript/JavaScript examples, see the documentation at:
http://localhost:5001/api/v1/docs
"""

import requests
import json


# Configuration
API_BASE_URL = "http://localhost:5001/api/v1"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def demo_health_check():
    """Demonstrate the health check endpoint."""
    print_section("1. Health Check (No Authentication Required)")
    
    print("Checking API health...")
    response = requests.get(f"{API_BASE_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def demo_generate_api_key():
    """Demonstrate generating an API key."""
    print_section("2. Generate API Key")
    
    print("Generating a new API key...")
    
    payload = {
        "name": "Demo Application",
        "owner_email": "demo@example.com",
        "description": "API key for demo purposes"
    }
    
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_BASE_URL}/keys/generate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 201:
        print("\n⚠️  IMPORTANT: Save the 'api_key' value - it will NOT be shown again!")
        return result.get("api_key")
    
    return None


def demo_list_keys(owner_email: str = "demo@example.com"):
    """Demonstrate listing API keys."""
    print_section("3. List API Keys")
    
    print(f"Listing keys for: {owner_email}")
    
    response = requests.get(
        f"{API_BASE_URL}/keys",
        params={"owner_email": owner_email}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def demo_chat(api_key: str, message: str = "Hello! What can you help me with?"):
    """Demonstrate the chat endpoint."""
    print_section("4. Chat with ArchieAI")
    
    print(f"Sending message: {message}")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    payload = {"message": message}
    
    print(f"\nHeaders: X-API-Key: {api_key[:20]}...")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json=payload,
        headers=headers
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def demo_chat_stream(api_key: str, message: str = "Tell me a short joke"):
    """Demonstrate the streaming chat endpoint."""
    print_section("5. Streaming Chat with ArchieAI")
    
    print(f"Sending message (streaming): {message}")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    payload = {"message": message}
    
    print(f"\nHeaders: X-API-Key: {api_key[:20]}...")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:")
    print("-" * 40)
    
    response = requests.post(
        f"{API_BASE_URL}/chat/stream",
        json=payload,
        headers=headers,
        stream=True
    )
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data = json.loads(line_str[6:])
                if 'token' in data:
                    print(data['token'], end='', flush=True)
                    full_response += data['token']
                elif 'done' in data:
                    print("\n" + "-" * 40)
                    print("Stream complete!")
    
    return full_response


def demo_usage(api_key: str):
    """Demonstrate the usage statistics endpoint."""
    print_section("6. Check API Key Usage")
    
    print("Retrieving usage statistics...")
    
    headers = {"X-API-Key": api_key}
    
    response = requests.get(
        f"{API_BASE_URL}/usage",
        headers=headers
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def demo_revoke_key(api_key: str, key_id: str, owner_email: str = "demo@example.com"):
    """Demonstrate revoking an API key."""
    print_section("7. Revoke API Key")
    
    print(f"Revoking key: {key_id}")
    
    payload = {"owner_email": owner_email}
    
    response = requests.post(
        f"{API_BASE_URL}/keys/{key_id}/revoke",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def demo_authentication_error():
    """Demonstrate authentication error handling."""
    print_section("8. Authentication Error Handling")
    
    print("Attempting to access chat without API key...")
    
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "Hello"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\nAttempting to access chat with invalid API key...")
    
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "Hello"},
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "invalid_key_12345"
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def main():
    """Run the full API demonstration."""
    print("\n" + "=" * 60)
    print("       ArchieAI API Demo")
    print("=" * 60)
    
    print("\nThis demo will walk you through all API endpoints.")
    print("Make sure the API server is running: python api.py")
    print("\nPress Enter to start...")
    input()
    
    # 1. Health check
    if not demo_health_check():
        print("\n❌ API server is not responding. Please start it with: python api.py")
        return
    
    # 2. Generate API key
    api_key = demo_generate_api_key()
    if not api_key:
        print("\n❌ Failed to generate API key. Exiting.")
        return
    
    input("\nPress Enter to continue to list keys...")
    
    # 3. List keys
    demo_list_keys()
    
    input("\nPress Enter to continue to chat demo...")
    
    # 4. Regular chat
    demo_chat(api_key, "What is Arcadia University known for?")
    
    input("\nPress Enter to continue to streaming chat demo...")
    
    # 5. Streaming chat
    demo_chat_stream(api_key, "Tell me a fun fact about Pennsylvania")
    
    input("\nPress Enter to continue to usage stats...")
    
    # 6. Usage statistics
    demo_usage(api_key)
    
    input("\nPress Enter to see authentication error handling...")
    
    # 7. Authentication errors
    demo_authentication_error()
    
    print_section("Demo Complete!")
    print("You've seen all the main API endpoints in action.")
    print(f"\nYour API key for further testing: {api_key[:30]}...")
    print("\nFor more examples in TypeScript, visit: http://localhost:5001/api/v1/docs")


if __name__ == "__main__":
    main()
