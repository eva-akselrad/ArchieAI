"""
External API module for ArchieAI.
Provides API key authentication and endpoints for third-party applications.
"""
import os
import json
import secrets
import hashlib
import re
import logging
import threading
from datetime import datetime
from functools import wraps
from typing import Optional, Dict, List
import flask as fk
import asyncio
import time

# Import from src directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from lib import GemInterface
from lib.DataCollector import DataCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOOL_RESULT_PREVIEW_LENGTH = 500

# Initialize AI interface
gemini = GemInterface.AiInterface()

# API-specific data collector (separate from main app)
api_data_collector = DataCollector(data_dir="data/api")


class APIKeyManager:
    """Manages API keys for external access to ArchieAI."""
    
    def __init__(self, data_dir: str = "data/api"):
        self.data_dir = data_dir
        self.keys_file = os.path.join(data_dir, "api_keys.json")
        self._lock = threading.Lock()
        
        # Ensure directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize keys file if it doesn't exist
        if not os.path.exists(self.keys_file):
            self._save_keys({})
    
    def _load_keys(self) -> Dict:
        """Load API keys from JSON file."""
        try:
            with open(self.keys_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_keys(self, keys: Dict):
        """Save API keys to JSON file."""
        with open(self.keys_file, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=4, ensure_ascii=False)
    
    def _hash_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self, name: str, owner_email: str, description: str = "") -> Dict:
        """
        Generate a new API key.
        
        Args:
            name: A friendly name for the API key
            owner_email: Email of the key owner
            description: Optional description of the key's purpose
            
        Returns:
            Dict with key_id, api_key (only shown once), and metadata
        """
        keys = self._load_keys()
        
        # Generate unique key ID and API key
        key_id = secrets.token_urlsafe(16)
        api_key = f"archie_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(api_key)
        
        # Store key metadata (never store the raw key)
        keys[key_id] = {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": name,
            "owner_email": owner_email,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0
        }
        
        self._save_keys(keys)
        
        # Return the key (only shown once at creation)
        return {
            "key_id": key_id,
            "api_key": api_key,  # Only returned once!
            "name": name,
            "owner_email": owner_email,
            "created_at": keys[key_id]["created_at"],
            "message": "Save this API key - it will not be shown again!"
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate an API key and return its metadata if valid.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Key metadata if valid, None otherwise
        """
        if not api_key:
            return None
            
        key_hash = self._hash_key(api_key)
        
        with self._lock:
            keys = self._load_keys()
            
            for key_id, key_data in keys.items():
                if key_data["key_hash"] == key_hash and key_data["is_active"]:
                    # Update usage statistics atomically
                    key_data["last_used"] = datetime.now().isoformat()
                    key_data["usage_count"] += 1
                    self._save_keys(keys)
                    return key_data.copy()
        
        return None
    
    def revoke_api_key(self, key_id: str, owner_email: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: The ID of the key to revoke
            owner_email: Email of the key owner (for authorization)
            
        Returns:
            True if revoked successfully, False otherwise
        """
        keys = self._load_keys()
        
        if key_id not in keys:
            return False
            
        if keys[key_id]["owner_email"] != owner_email:
            return False
        
        keys[key_id]["is_active"] = False
        self._save_keys(keys)
        return True
    
    def list_keys(self, owner_email: str) -> List[Dict]:
        """
        List all API keys for a user.
        
        Args:
            owner_email: Email of the key owner
            
        Returns:
            List of key metadata (excluding hashes)
        """
        keys = self._load_keys()
        user_keys = []
        
        for key_id, key_data in keys.items():
            if key_data["owner_email"] == owner_email:
                # Return metadata without the hash
                user_keys.append({
                    "key_id": key_data["key_id"],
                    "name": key_data["name"],
                    "description": key_data["description"],
                    "created_at": key_data["created_at"],
                    "last_used": key_data["last_used"],
                    "is_active": key_data["is_active"],
                    "usage_count": key_data["usage_count"]
                })
        
        return user_keys


# Initialize API key manager
api_key_manager = APIKeyManager()

# Create Flask Blueprint for API routes
api_bp = fk.Blueprint("api", __name__, url_prefix="/api/v1")


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in header
        api_key = fk.request.headers.get("X-API-Key")
        
        # Also check Authorization header (Bearer token)
        if not api_key:
            auth_header = fk.request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
        
        if not api_key:
            return fk.jsonify({
                "error": "API key required",
                "message": "Please provide an API key via X-API-Key header or Authorization: Bearer <key>"
            }), 401
        
        key_data = api_key_manager.validate_api_key(api_key)
        if not key_data:
            return fk.jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is invalid or has been revoked"
            }), 401
        
        # Add key data to request context
        fk.g.api_key_data = key_data
        return f(*args, **kwargs)
    
    return decorated_function


# API Key Management Endpoints

@api_bp.route("/keys/generate", methods=["POST"])
def generate_key():
    """
    Generate a new API key.
    
    Request body:
    {
        "name": "My App",
        "owner_email": "user@example.com",
        "description": "API key for my application"
    }
    """
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    name = data.get("name")
    owner_email = data.get("owner_email")
    description = data.get("description", "")
    
    if not name:
        return fk.jsonify({"error": "name is required"}), 400
    if not owner_email:
        return fk.jsonify({"error": "owner_email is required"}), 400
    
    # Email validation using regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, owner_email) or len(owner_email) > 255:
        return fk.jsonify({"error": "Invalid email address"}), 400
    
    result = api_key_manager.generate_api_key(name, owner_email, description)
    return fk.jsonify(result), 201


# API Documentation HTML
API_DOCUMENTATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArchieAI API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 40px 20px;
            color: white;
        }
        header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            overflow: hidden;
        }
        .card-header {
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 1px solid #e9ecef;
        }
        .card-header h2 {
            color: #495057;
            font-size: 1.5rem;
        }
        .card-body {
            padding: 30px;
        }
        .endpoint {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        .endpoint h3 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        .method {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            color: white;
        }
        .method-get { background: #28a745; }
        .method-post { background: #007bff; }
        .method-delete { background: #dc3545; }
        .endpoint-path {
            font-family: 'Monaco', 'Menlo', monospace;
            color: #495057;
        }
        .endpoint p {
            color: #6c757d;
            margin-bottom: 15px;
        }
        .auth-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            background: #ffc107;
            color: #000;
            margin-left: 10px;
        }
        .auth-badge.none {
            background: #28a745;
            color: white;
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        code {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        }
        .code-tabs {
            display: flex;
            gap: 0;
            margin-bottom: 0;
        }
        .code-tab {
            padding: 10px 20px;
            background: #495057;
            color: white;
            cursor: pointer;
            border: none;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        .code-tab:first-child {
            border-radius: 8px 0 0 0;
        }
        .code-tab:last-child {
            border-radius: 0 8px 0 0;
        }
        .code-tab.active {
            background: #2d2d2d;
        }
        .code-tab:hover:not(.active) {
            background: #5a6268;
        }
        .code-content {
            display: none;
        }
        .code-content.active {
            display: block;
        }
        .code-content pre {
            border-radius: 0 8px 8px 8px;
            margin: 0;
        }
        .response-example {
            margin-top: 15px;
        }
        .response-example h4 {
            color: #495057;
            margin-bottom: 10px;
            font-size: 0.95rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .param-required {
            color: #dc3545;
            font-size: 0.8rem;
        }
        .param-optional {
            color: #6c757d;
            font-size: 0.8rem;
        }
        .quick-start {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        .quick-start h2 {
            margin-bottom: 20px;
        }
        .quick-start ol {
            padding-left: 20px;
        }
        .quick-start li {
            margin-bottom: 15px;
        }
        .quick-start code {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 4px;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px 0;
            color: #856404;
        }
        .warning strong {
            display: block;
            margin-bottom: 5px;
        }
        footer {
            text-align: center;
            padding: 40px 20px;
            color: white;
            opacity: 0.8;
        }
        .toc {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px 30px;
            margin-bottom: 30px;
        }
        .toc h3 {
            margin-bottom: 15px;
            color: #495057;
        }
        .toc ul {
            list-style: none;
        }
        .toc li {
            margin-bottom: 8px;
        }
        .toc a {
            color: #667eea;
            text-decoration: none;
        }
        .toc a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 ArchieAI API</h1>
            <p>External API for integrating ArchieAI into your applications</p>
            <p style="margin-top: 10px; font-size: 0.9rem;">Version 1.0.0 | Base URL: <code>/api/v1</code></p>
        </header>

        <div class="quick-start">
            <h2>🚀 Quick Start</h2>
            <ol>
                <li><strong>Generate an API Key:</strong> Send a POST request to <code>/api/v1/keys/generate</code> with your email</li>
                <li><strong>Save Your Key:</strong> The API key is only shown once - save it securely!</li>
                <li><strong>Make Requests:</strong> Include your API key in the <code>X-API-Key</code> header</li>
                <li><strong>Start Chatting:</strong> Send messages to <code>/api/v1/chat</code></li>
            </ol>
        </div>

        <div class="card">
            <div class="card-header">
                <h2>📚 Table of Contents</h2>
            </div>
            <div class="card-body toc">
                <ul>
                    <li><a href="#authentication">Authentication</a></li>
                    <li><a href="#key-management">API Key Management</a></li>
                    <li><a href="#chat-endpoints">Chat Endpoints</a></li>
                    <li><a href="#utility-endpoints">Utility Endpoints</a></li>
                    <li><a href="#error-handling">Error Handling</a></li>
                    <li><a href="#rate-limits">Rate Limits & Best Practices</a></li>
                </ul>
            </div>
        </div>

        <div class="card" id="authentication">
            <div class="card-header">
                <h2>🔐 Authentication</h2>
            </div>
            <div class="card-body">
                <p>Most API endpoints require authentication using an API key. You can provide your API key in two ways:</p>
                
                <h3 style="margin: 20px 0 10px;">Option 1: X-API-Key Header (Recommended)</h3>
                <pre><code>X-API-Key: archie_your_api_key_here</code></pre>
                
                <h3 style="margin: 20px 0 10px;">Option 2: Authorization Bearer Token</h3>
                <pre><code>Authorization: Bearer archie_your_api_key_here</code></pre>
                
                <div class="warning">
                    <strong>⚠️ Important Security Notes:</strong>
                    <ul style="margin-top: 10px; padding-left: 20px;">
                        <li>Never expose your API key in client-side code or public repositories</li>
                        <li>API keys are hashed when stored - they cannot be recovered if lost</li>
                        <li>Rotate your keys periodically and revoke unused keys</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="card" id="key-management">
            <div class="card-header">
                <h2>🔑 API Key Management</h2>
            </div>
            <div class="card-body">
                
                <!-- Generate Key -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-post">POST</span>
                        <span class="endpoint-path">/api/v1/keys/generate</span>
                        <span class="auth-badge none">No Auth Required</span>
                    </h3>
                    <p>Generate a new API key for your application. The key is only displayed once at creation time.</p>
                    
                    <h4>Request Body Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>name</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>A friendly name for your API key (e.g., "My Production App")</td>
                        </tr>
                        <tr>
                            <td><code>owner_email</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>Your email address for key management</td>
                        </tr>
                        <tr>
                            <td><code>description</code> <span class="param-optional">optional</span></td>
                            <td>string</td>
                            <td>A description of what this key will be used for</td>
                        </tr>
                    </table>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'gen-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'gen-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'gen-curl')">cURL</button>
                    </div>
                    <div id="gen-python" class="code-content active">
                        <pre><code>import requests

response = requests.post(
    "http://localhost:5001/api/v1/keys/generate",
    json={
        "name": "My Application",
        "owner_email": "developer@example.com",
        "description": "Production API key for my app"
    }
)

result = response.json()
print(f"API Key: {result['api_key']}")
print("⚠️ Save this key - it won't be shown again!")</code></pre>
                    </div>
                    <div id="gen-typescript" class="code-content">
                        <pre><code>// Using fetch API
const response = await fetch("http://localhost:5001/api/v1/keys/generate", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        name: "My Application",
        owner_email: "developer@example.com",
        description: "Production API key for my app"
    })
});

const result = await response.json();
console.log(`API Key: ${result.api_key}`);
console.log("⚠️ Save this key - it won't be shown again!");

// Using axios
import axios from "axios";

const { data } = await axios.post("http://localhost:5001/api/v1/keys/generate", {
    name: "My Application",
    owner_email: "developer@example.com",
    description: "Production API key for my app"
});

console.log(`API Key: ${data.api_key}`);</code></pre>
                    </div>
                    <div id="gen-curl" class="code-content">
                        <pre><code>curl -X POST http://localhost:5001/api/v1/keys/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My Application",
    "owner_email": "developer@example.com",
    "description": "Production API key for my app"
  }'</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h4>Response (201 Created)</h4>
                        <pre><code>{
    "key_id": "abc123xyz789",
    "api_key": "archie_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789",
    "name": "My Application",
    "owner_email": "developer@example.com",
    "created_at": "2024-01-15T10:30:00.000000",
    "message": "Save this API key - it will not be shown again!"
}</code></pre>
                    </div>
                </div>
                
                <!-- List Keys -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-get">GET</span>
                        <span class="endpoint-path">/api/v1/keys</span>
                        <span class="auth-badge none">No Auth Required</span>
                    </h3>
                    <p>List all API keys associated with an email address. Keys are returned without the actual key value.</p>
                    
                    <h4>Query Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>owner_email</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>Email address to list keys for</td>
                        </tr>
                    </table>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'list-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'list-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'list-curl')">cURL</button>
                    </div>
                    <div id="list-python" class="code-content active">
                        <pre><code>import requests

response = requests.get(
    "http://localhost:5001/api/v1/keys",
    params={"owner_email": "developer@example.com"}
)

keys = response.json()["keys"]
for key in keys:
    print(f"Key: {key['name']} - Active: {key['is_active']} - Uses: {key['usage_count']}")</code></pre>
                    </div>
                    <div id="list-typescript" class="code-content">
                        <pre><code>// Using fetch API
const response = await fetch(
    "http://localhost:5001/api/v1/keys?owner_email=developer@example.com"
);

const { keys } = await response.json();
keys.forEach(key => {
    console.log(`Key: ${key.name} - Active: ${key.is_active} - Uses: ${key.usage_count}`);
});

// Using axios
import axios from "axios";

const { data } = await axios.get("http://localhost:5001/api/v1/keys", {
    params: { owner_email: "developer@example.com" }
});

data.keys.forEach(key => {
    console.log(`Key: ${key.name} - Active: ${key.is_active}`);
});</code></pre>
                    </div>
                    <div id="list-curl" class="code-content">
                        <pre><code>curl "http://localhost:5001/api/v1/keys?owner_email=developer@example.com"</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h4>Response (200 OK)</h4>
                        <pre><code>{
    "keys": [
        {
            "key_id": "abc123xyz789",
            "name": "My Application",
            "description": "Production API key",
            "created_at": "2024-01-15T10:30:00.000000",
            "last_used": "2024-01-15T14:22:00.000000",
            "is_active": true,
            "usage_count": 42
        }
    ]
}</code></pre>
                    </div>
                </div>
                
                <!-- Revoke Key -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-post">POST</span>
                        <span class="endpoint-path">/api/v1/keys/{key_id}/revoke</span>
                        <span class="auth-badge none">No Auth Required</span>
                    </h3>
                    <p>Revoke an API key. Once revoked, the key can no longer be used for authentication.</p>
                    
                    <h4>Path Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>key_id</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>The ID of the key to revoke</td>
                        </tr>
                    </table>
                    
                    <h4>Request Body Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>owner_email</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>Email of the key owner (for verification)</td>
                        </tr>
                    </table>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'revoke-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'revoke-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'revoke-curl')">cURL</button>
                    </div>
                    <div id="revoke-python" class="code-content active">
                        <pre><code>import requests

key_id = "abc123xyz789"
response = requests.post(
    f"http://localhost:5001/api/v1/keys/{key_id}/revoke",
    json={"owner_email": "developer@example.com"}
)

if response.status_code == 200:
    print("Key revoked successfully!")
else:
    print(f"Error: {response.json()['error']}")</code></pre>
                    </div>
                    <div id="revoke-typescript" class="code-content">
                        <pre><code>// Using fetch API
const keyId = "abc123xyz789";
const response = await fetch(`http://localhost:5001/api/v1/keys/${keyId}/revoke`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        owner_email: "developer@example.com"
    })
});

if (response.ok) {
    console.log("Key revoked successfully!");
} else {
    const error = await response.json();
    console.error(`Error: ${error.error}`);
}

// Using axios
import axios from "axios";

try {
    await axios.post(`http://localhost:5001/api/v1/keys/${keyId}/revoke`, {
        owner_email: "developer@example.com"
    });
    console.log("Key revoked successfully!");
} catch (error) {
    console.error(`Error: ${error.response.data.error}`);
}</code></pre>
                    </div>
                    <div id="revoke-curl" class="code-content">
                        <pre><code>curl -X POST "http://localhost:5001/api/v1/keys/abc123xyz789/revoke" \\
  -H "Content-Type: application/json" \\
  -d '{"owner_email": "developer@example.com"}'</code></pre>
                    </div>
                </div>
            </div>
        </div>

        <div class="card" id="chat-endpoints">
            <div class="card-header">
                <h2>💬 Chat Endpoints</h2>
            </div>
            <div class="card-body">
                
                <!-- Chat -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-post">POST</span>
                        <span class="endpoint-path">/api/v1/chat</span>
                        <span class="auth-badge">Requires API Key</span>
                    </h3>
                    <p>Send a message to ArchieAI and receive a complete response. This is a synchronous endpoint - the response is returned only after the AI has finished generating the complete answer.</p>
                    
                    <h4>Request Headers</h4>
                    <table>
                        <tr>
                            <th>Header</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>X-API-Key</code> <span class="param-required">required</span></td>
                            <td>Your API key</td>
                        </tr>
                        <tr>
                            <td><code>Content-Type</code></td>
                            <td>application/json</td>
                        </tr>
                    </table>
                    
                    <h4>Request Body Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>message</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>The message/question to send to ArchieAI</td>
                        </tr>
                    </table>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'chat-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'chat-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'chat-curl')">cURL</button>
                    </div>
                    <div id="chat-python" class="code-content active">
                        <pre><code>import requests

API_KEY = "archie_your_api_key_here"

response = requests.post(
    "http://localhost:5001/api/v1/chat",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    json={
        "message": "What are the dining hall hours at Arcadia University?"
    }
)

result = response.json()
print(f"Response: {result['response']}")
print(f"Generation time: {result['generation_time_seconds']}s")</code></pre>
                    </div>
                    <div id="chat-typescript" class="code-content">
                        <pre><code>// Using fetch API
const API_KEY = "archie_your_api_key_here";

const response = await fetch("http://localhost:5001/api/v1/chat", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    body: JSON.stringify({
        message: "What are the dining hall hours at Arcadia University?"
    })
});

const result = await response.json();
console.log(`Response: ${result.response}`);
console.log(`Generation time: ${result.generation_time_seconds}s`);

// Using axios
import axios from "axios";

const API_KEY = "archie_your_api_key_here";

const { data } = await axios.post(
    "http://localhost:5001/api/v1/chat",
    { message: "What are the dining hall hours at Arcadia University?" },
    { headers: { "X-API-Key": API_KEY } }
);

console.log(`Response: ${data.response}`);</code></pre>
                    </div>
                    <div id="chat-curl" class="code-content">
                        <pre><code>curl -X POST http://localhost:5001/api/v1/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: archie_your_api_key_here" \\
  -d '{"message": "What are the dining hall hours at Arcadia University?"}'</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h4>Response (200 OK)</h4>
                        <pre><code>{
    "response": "The dining hall at Arcadia University typically operates during the following hours...",
    "generation_time_seconds": 2.34
}</code></pre>
                    </div>
                </div>
                
                <!-- Streaming Chat -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-post">POST</span>
                        <span class="endpoint-path">/api/v1/chat/stream</span>
                        <span class="auth-badge">Requires API Key</span>
                    </h3>
                    <p>Send a message to ArchieAI and receive a streaming response using Server-Sent Events (SSE). This allows you to display the AI's response in real-time as it's generated.</p>
                    
                    <h4>Request Headers</h4>
                    <table>
                        <tr>
                            <th>Header</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>X-API-Key</code> <span class="param-required">required</span></td>
                            <td>Your API key</td>
                        </tr>
                        <tr>
                            <td><code>Content-Type</code></td>
                            <td>application/json</td>
                        </tr>
                    </table>
                    
                    <h4>Request Body Parameters</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>message</code> <span class="param-required">required</span></td>
                            <td>string</td>
                            <td>The message/question to send to ArchieAI</td>
                        </tr>
                    </table>
                    
                    <h4>SSE Event Types</h4>
                    <table>
                        <tr>
                            <th>Event Data</th>
                            <th>Description</th>
                        </tr>
                        <tr>
                            <td><code>{"token": "..."}</code></td>
                            <td>A chunk of the response text</td>
                        </tr>
                        <tr>
                            <td><code>{"tool_call": {...}}</code></td>
                            <td>Information about a tool being used (e.g., web search)</td>
                        </tr>
                        <tr>
                            <td><code>{"done": true}</code></td>
                            <td>Signals the end of the stream</td>
                        </tr>
                        <tr>
                            <td><code>{"error": "..."}</code></td>
                            <td>An error occurred during generation</td>
                        </tr>
                    </table>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'stream-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'stream-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'stream-curl')">cURL</button>
                    </div>
                    <div id="stream-python" class="code-content active">
                        <pre><code>import requests
import json

API_KEY = "archie_your_api_key_here"

response = requests.post(
    "http://localhost:5001/api/v1/chat/stream",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    json={"message": "Tell me about Arcadia University"},
    stream=True  # Enable streaming
)

# Process the stream
full_response = ""
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = json.loads(line_str[6:])
            
            if 'token' in data:
                # Print each token as it arrives
                print(data['token'], end='', flush=True)
                full_response += data['token']
            elif 'tool_call' in data:
                print(f"\\n[Using tool: {data['tool_call']['tool_name']}]")
            elif 'done' in data:
                print("\\n--- Stream complete ---")
            elif 'error' in data:
                print(f"\\nError: {data['error']}")</code></pre>
                    </div>
                    <div id="stream-typescript" class="code-content">
                        <pre><code>// Using fetch API with ReadableStream
const API_KEY = "archie_your_api_key_here";

const response = await fetch("http://localhost:5001/api/v1/chat/stream", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    body: JSON.stringify({
        message: "Tell me about Arcadia University"
    })
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();
let fullResponse = "";

while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\\n');
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.token) {
                process.stdout.write(data.token);  // Or update UI
                fullResponse += data.token;
            } else if (data.tool_call) {
                console.log(`\\n[Using tool: ${data.tool_call.tool_name}]`);
            } else if (data.done) {
                console.log("\\n--- Stream complete ---");
            } else if (data.error) {
                console.error(`Error: ${data.error}`);
            }
        }
    }
}

// Note: Browser EventSource API does NOT support custom headers.
// For browser streaming with API key auth, use fetch with ReadableStream as shown above.</code></pre>
                    </div>
                    <div id="stream-curl" class="code-content">
                        <pre><code>curl -N -X POST http://localhost:5001/api/v1/chat/stream \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: archie_your_api_key_here" \\
  -d '{"message": "Tell me about Arcadia University"}'</code></pre>
                    </div>
                </div>
            </div>
        </div>

        <div class="card" id="utility-endpoints">
            <div class="card-header">
                <h2>🔧 Utility Endpoints</h2>
            </div>
            <div class="card-body">
                
                <!-- Health Check -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-get">GET</span>
                        <span class="endpoint-path">/api/v1/health</span>
                        <span class="auth-badge none">No Auth Required</span>
                    </h3>
                    <p>Check if the API server is running and healthy. Useful for monitoring and health checks.</p>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'health-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'health-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'health-curl')">cURL</button>
                    </div>
                    <div id="health-python" class="code-content active">
                        <pre><code>import requests

response = requests.get("http://localhost:5001/api/v1/health")
health = response.json()

if health["status"] == "healthy":
    print(f"✅ API is healthy - Version: {health['version']}")</code></pre>
                    </div>
                    <div id="health-typescript" class="code-content">
                        <pre><code>const response = await fetch("http://localhost:5001/api/v1/health");
const health = await response.json();

if (health.status === "healthy") {
    console.log(`✅ API is healthy - Version: ${health.version}`);
}</code></pre>
                    </div>
                    <div id="health-curl" class="code-content">
                        <pre><code>curl http://localhost:5001/api/v1/health</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h4>Response (200 OK)</h4>
                        <pre><code>{
    "status": "healthy",
    "service": "ArchieAI API",
    "version": "1.0.0"
}</code></pre>
                    </div>
                </div>
                
                <!-- Usage Stats -->
                <div class="endpoint">
                    <h3>
                        <span class="method method-get">GET</span>
                        <span class="endpoint-path">/api/v1/usage</span>
                        <span class="auth-badge">Requires API Key</span>
                    </h3>
                    <p>Get usage statistics for the authenticated API key, including total requests made and last usage time.</p>
                    
                    <div class="code-tabs">
                        <button class="code-tab active" onclick="showCode(this, 'usage-python')">Python</button>
                        <button class="code-tab" onclick="showCode(this, 'usage-typescript')">TypeScript</button>
                        <button class="code-tab" onclick="showCode(this, 'usage-curl')">cURL</button>
                    </div>
                    <div id="usage-python" class="code-content active">
                        <pre><code>import requests

API_KEY = "archie_your_api_key_here"

response = requests.get(
    "http://localhost:5001/api/v1/usage",
    headers={"X-API-Key": API_KEY}
)

usage = response.json()
print(f"Key: {usage['name']}")
print(f"Total requests: {usage['usage_count']}")
print(f"Last used: {usage['last_used']}")</code></pre>
                    </div>
                    <div id="usage-typescript" class="code-content">
                        <pre><code>const API_KEY = "archie_your_api_key_here";

const response = await fetch("http://localhost:5001/api/v1/usage", {
    headers: { "X-API-Key": API_KEY }
});

const usage = await response.json();
console.log(`Key: ${usage.name}`);
console.log(`Total requests: ${usage.usage_count}`);
console.log(`Last used: ${usage.last_used}`);</code></pre>
                    </div>
                    <div id="usage-curl" class="code-content">
                        <pre><code>curl http://localhost:5001/api/v1/usage \\
  -H "X-API-Key: archie_your_api_key_here"</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h4>Response (200 OK)</h4>
                        <pre><code>{
    "key_id": "abc123xyz789",
    "name": "My Application",
    "usage_count": 42,
    "last_used": "2024-01-15T14:22:00.000000",
    "created_at": "2024-01-15T10:30:00.000000"
}</code></pre>
                    </div>
                </div>
            </div>
        </div>

        <div class="card" id="error-handling">
            <div class="card-header">
                <h2>⚠️ Error Handling</h2>
            </div>
            <div class="card-body">
                <p>The API uses standard HTTP status codes to indicate the success or failure of requests.</p>
                
                <h3 style="margin: 20px 0 15px;">HTTP Status Codes</h3>
                <table>
                    <tr>
                        <th>Status Code</th>
                        <th>Meaning</th>
                    </tr>
                    <tr>
                        <td><code>200 OK</code></td>
                        <td>Request successful</td>
                    </tr>
                    <tr>
                        <td><code>201 Created</code></td>
                        <td>Resource created successfully (e.g., new API key)</td>
                    </tr>
                    <tr>
                        <td><code>400 Bad Request</code></td>
                        <td>Invalid request body or missing required parameters</td>
                    </tr>
                    <tr>
                        <td><code>401 Unauthorized</code></td>
                        <td>Missing or invalid API key</td>
                    </tr>
                    <tr>
                        <td><code>404 Not Found</code></td>
                        <td>Resource not found (e.g., invalid key_id)</td>
                    </tr>
                    <tr>
                        <td><code>500 Internal Server Error</code></td>
                        <td>Server error - please try again</td>
                    </tr>
                </table>
                
                <h3 style="margin: 20px 0 15px;">Error Response Format</h3>
                <pre><code>{
    "error": "Error type",
    "message": "Detailed description of what went wrong"
}</code></pre>
                
                <h3 style="margin: 20px 0 15px;">Common Errors</h3>
                
                <div class="endpoint">
                    <h4>Missing API Key</h4>
                    <pre><code>// Status: 401 Unauthorized
{
    "error": "API key required",
    "message": "Please provide an API key via X-API-Key header or Authorization: Bearer &lt;key&gt;"
}</code></pre>
                </div>
                
                <div class="endpoint">
                    <h4>Invalid API Key</h4>
                    <pre><code>// Status: 401 Unauthorized
{
    "error": "Invalid API key",
    "message": "The provided API key is invalid or has been revoked"
}</code></pre>
                </div>
                
                <div class="endpoint">
                    <h4>Missing Required Field</h4>
                    <pre><code>// Status: 400 Bad Request
{
    "error": "message is required"
}</code></pre>
                </div>
            </div>
        </div>

        <div class="card" id="rate-limits">
            <div class="card-header">
                <h2>📊 Rate Limits & Best Practices</h2>
            </div>
            <div class="card-body">
                <h3 style="margin-bottom: 15px;">Best Practices</h3>
                <ul style="padding-left: 20px; margin-bottom: 20px;">
                    <li><strong>Store API keys securely:</strong> Use environment variables or secure vaults, never hardcode in source</li>
                    <li><strong>Handle errors gracefully:</strong> Implement proper error handling and retry logic</li>
                    <li><strong>Use streaming for long responses:</strong> The <code>/chat/stream</code> endpoint provides better UX</li>
                    <li><strong>Monitor your usage:</strong> Check the <code>/usage</code> endpoint regularly</li>
                    <li><strong>Rotate keys periodically:</strong> Generate new keys and revoke old ones regularly</li>
                </ul>
                
                <h3 style="margin: 20px 0 15px;">Example: Robust API Client</h3>
                <div class="code-tabs">
                    <button class="code-tab active" onclick="showCode(this, 'client-python')">Python</button>
                    <button class="code-tab" onclick="showCode(this, 'client-typescript')">TypeScript</button>
                </div>
                <div id="client-python" class="code-content active">
                    <pre><code>import requests
import os
from typing import Optional

class ArchieAIClient:
    \"\"\"A robust client for the ArchieAI API.\"\"\"
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:5001/api/v1"):
        self.api_key = api_key or os.getenv("ARCHIE_API_KEY")
        self.base_url = base_url
        
        if not self.api_key:
            raise ValueError("API key required. Set ARCHIE_API_KEY env var or pass to constructor.")
    
    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def chat(self, message: str) -> str:
        \"\"\"Send a message and get a response.\"\"\"
        response = requests.post(
            f"{self.base_url}/chat",
            headers=self._get_headers(),
            json={"message": message}
        )
        response.raise_for_status()
        return response.json()["response"]
    
    def chat_stream(self, message: str):
        \"\"\"Stream a response token by token.\"\"\"
        import json
        
        response = requests.post(
            f"{self.base_url}/chat/stream",
            headers=self._get_headers(),
            json={"message": message},
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if 'token' in data:
                        yield data['token']
                    elif 'done' in data:
                        break
    
    def get_usage(self) -> dict:
        \"\"\"Get usage statistics.\"\"\"
        response = requests.get(
            f"{self.base_url}/usage",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ArchieAIClient()
response = client.chat("What are the library hours?")
print(response)

# Streaming
for token in client.chat_stream("Tell me a story"):
    print(token, end='', flush=True)</code></pre>
                </div>
                <div id="client-typescript" class="code-content">
                    <pre><code>interface ChatResponse {
    response: string;
    generation_time_seconds: number;
}

interface UsageStats {
    key_id: string;
    name: string;
    usage_count: number;
    last_used: string;
    created_at: string;
}

class ArchieAIClient {
    private apiKey: string;
    private baseUrl: string;

    constructor(apiKey?: string, baseUrl: string = "http://localhost:5001/api/v1") {
        this.apiKey = apiKey || process.env.ARCHIE_API_KEY || "";
        this.baseUrl = baseUrl;
        
        if (!this.apiKey) {
            throw new Error("API key required. Set ARCHIE_API_KEY env var or pass to constructor.");
        }
    }

    private getHeaders(): HeadersInit {
        return {
            "Content-Type": "application/json",
            "X-API-Key": this.apiKey
        };
    }

    async chat(message: string): Promise&lt;string&gt; {
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: "POST",
            headers: this.getHeaders(),
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data: ChatResponse = await response.json();
        return data.response;
    }

    async *chatStream(message: string): AsyncGenerator&lt;string&gt; {
        const response = await fetch(`${this.baseUrl}/chat/stream`, {
            method: "POST",
            headers: this.getHeaders(),
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        while (reader) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    if (data.token) {
                        yield data.token;
                    } else if (data.done) {
                        return;
                    }
                }
            }
        }
    }

    async getUsage(): Promise&lt;UsageStats&gt; {
        const response = await fetch(`${this.baseUrl}/usage`, {
            headers: this.getHeaders()
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return response.json();
    }
}

// Usage
const client = new ArchieAIClient("archie_your_key_here");
const response = await client.chat("What are the library hours?");
console.log(response);

// Streaming
for await (const token of client.chatStream("Tell me a story")) {
    process.stdout.write(token);
}</code></pre>
                </div>
            </div>
        </div>

        <footer>
            <p>ArchieAI API Documentation v1.0.0</p>
            <p>Made with ❤️ by Arcadia University Students</p>
        </footer>
    </div>

    <script>
        function showCode(button, contentId) {
            // Get the parent endpoint or card
            const parent = button.closest('.endpoint') || button.closest('.card-body');
            
            // Remove active class from all tabs in this group
            parent.querySelectorAll('.code-tab').forEach(tab => tab.classList.remove('active'));
            
            // Hide all code content in this group
            parent.querySelectorAll('.code-content').forEach(content => content.classList.remove('active'));
            
            // Activate clicked tab and show content
            button.classList.add('active');
            document.getElementById(contentId).classList.add('active');
        }
    </script>
</body>
</html>
"""


@api_bp.route("/", methods=["GET"])
@api_bp.route("/docs", methods=["GET"])
def api_docs():
    """Serve API documentation page."""
    return fk.Response(API_DOCUMENTATION_HTML, mimetype='text/html')


@api_bp.route("/keys", methods=["GET"])
def list_keys():
    """
    List all API keys for a user.
    
    Query parameter:
    - owner_email: The email of the key owner
    """
    owner_email = fk.request.args.get("owner_email")
    
    if not owner_email:
        return fk.jsonify({"error": "owner_email query parameter required"}), 400
    
    keys = api_key_manager.list_keys(owner_email)
    return fk.jsonify({"keys": keys})


@api_bp.route("/keys/<key_id>/revoke", methods=["POST"])
def revoke_key(key_id):
    """
    Revoke an API key.
    
    Request body:
    {
        "owner_email": "user@example.com"
    }
    """
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    owner_email = data.get("owner_email")
    
    if not owner_email:
        return fk.jsonify({"error": "owner_email is required"}), 400
    
    success = api_key_manager.revoke_api_key(key_id, owner_email)
    
    if success:
        return fk.jsonify({"message": "API key revoked successfully"})
    else:
        return fk.jsonify({"error": "Failed to revoke key - key not found or unauthorized"}), 404


# Chat API Endpoints (require API key)

async def collect_streaming_response(message: str) -> str:
    """Collect full response from streaming AI generator."""
    full_response = ""
    async for chunk in gemini.Archie_streaming(message):
        if isinstance(chunk, str):
            full_response += chunk
        elif isinstance(chunk, dict):
            # Skip tool calls and final markers for non-streaming response
            if chunk.get('final'):
                break
    return full_response


@api_bp.route("/chat", methods=["POST"])
@require_api_key
def chat():
    """
    Send a message to ArchieAI and get a response.
    
    Headers:
    - X-API-Key: Your API key
    
    Request body:
    {
        "message": "What are the dining hall hours?"
    }
    """
    start_time = time.time()
    
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    message = data.get("message")
    
    if not message:
        return fk.jsonify({"error": "message is required"}), 400
    
    # Get response from AI using streaming method (Archie method is deprecated)
    response = asyncio.run(collect_streaming_response(message))
    
    generation_time = time.time() - start_time
    
    # Log interaction to API-specific data store
    api_data_collector.log_interaction(
        session_id=f"api_{fk.g.api_key_data['key_id']}",
        user_email=fk.g.api_key_data["owner_email"],
        ip_address=fk.request.remote_addr,
        device_info=fk.request.user_agent.string,
        question=message,
        answer=response,
        generation_time_seconds=generation_time
    )
    
    return fk.jsonify({
        "response": response,
        "generation_time_seconds": round(generation_time, 2)
    })


@api_bp.route("/chat/stream", methods=["POST"])
@require_api_key
def chat_stream():
    """
    Send a message to ArchieAI and get a streaming response.
    
    Headers:
    - X-API-Key: Your API key
    
    Request body:
    {
        "message": "What are the dining hall hours?"
    }
    
    Response:
    Server-Sent Events (SSE) stream with tokens
    """
    start_time = time.time()
    
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    message = data.get("message")
    
    if not message:
        return fk.jsonify({"error": "message is required"}), 400
    
    # Capture request info for data collection
    ip_address = fk.request.remote_addr
    device_info = fk.request.user_agent.string
    key_data = fk.g.api_key_data
    
    def generate():
        full_response = ""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            async_gen = gemini.Archie_streaming(message)
            
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    
                    if isinstance(chunk, str):
                        full_response += chunk
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                    elif isinstance(chunk, dict):
                        if chunk.get('tool_name'):
                            json_safe_payload = {
                                'tool_name': chunk.get('tool_name'),
                                'tool_result_preview': str(chunk.get('tool_result'))[:TOOL_RESULT_PREVIEW_LENGTH]
                            }
                            yield f"data: {json.dumps({'tool_call': json_safe_payload})}\n\n"
                        elif chunk.get('final'):
                            pass
                except StopAsyncIteration:
                    break
            
            generation_time = time.time() - start_time
            
            # Log interaction
            api_data_collector.log_interaction(
                session_id=f"api_{key_data['key_id']}",
                user_email=key_data["owner_email"],
                ip_address=ip_address,
                device_info=device_info,
                question=message,
                answer=full_response,
                generation_time_seconds=generation_time
            )
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if loop is not None and not loop.is_closed():
                loop.close()
    
    return fk.Response(generate(), mimetype='text/event-stream')


@api_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint (no authentication required)."""
    return fk.jsonify({
        "status": "healthy",
        "service": "ArchieAI API",
        "version": "1.0.0"
    })


@api_bp.route("/usage", methods=["GET"])
@require_api_key
def usage():
    """
    Get usage statistics for the authenticated API key.
    
    Headers:
    - X-API-Key: Your API key
    """
    key_data = fk.g.api_key_data
    return fk.jsonify({
        "key_id": key_data["key_id"],
        "name": key_data["name"],
        "usage_count": key_data["usage_count"],
        "last_used": key_data["last_used"],
        "created_at": key_data["created_at"]
    })


# Standalone Flask app for API server
def create_api_app():
    """Create a standalone Flask app for the API server."""
    app = fk.Flask(__name__)
    app.register_blueprint(api_bp)
    return app


if __name__ == "__main__":
    # Run as standalone API server
    app = create_api_app()
    logger.info("Starting ArchieAI API Server...")
    logger.info("API documentation available at http://localhost:5001/api/v1/")
    # Use environment variable to control debug mode (default: False for security)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
