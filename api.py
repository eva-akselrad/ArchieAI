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


@api_bp.route("/", methods=["GET"])
def api_index():
    """API index endpoint."""
    return fk.jsonify({
        "message": "Welcome to the ArchieAI API",
        "documentation_url": "/api/v1/health"
    })
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
    
    # Get response from AI
    response = asyncio.run(gemini.Archie(message))
    
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
    logger.info("API documentation available at /api/v1/health")
    # Use environment variable to control debug mode (default: False for security)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
