import os
import sys
import uuid
import threading
import asyncio
import time
import flask as fk
import json
import secrets
import hashlib
import re
import logging
import datetime as dt_module
from functools import wraps
from typing import Optional, Dict, List
proj_root = os.path.dirname(__file__)         
src_dir = os.path.join(proj_root, "src")
sys.path.insert(0, src_dir)
from lib import GemInterface
from lib import qrCodeGen
from lib.SessionManager import SessionManager
from lib.DataCollector import DataCollector
from werkzeug.security import generate_password_hash

# Configure logging for API
logging.basicConfig(level=logging.INFO)
api_logger = logging.getLogger("api")

gemini = GemInterface.AiInterface()

session_manager = SessionManager(data_dir="data")
data_collector = DataCollector(data_dir="data")

# API-specific data collector (separate from main app)
api_data_collector = DataCollector(data_dir="data/api")

# Constants for API
TOOL_RESULT_PREVIEW_LENGTH = 500


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
        """Generate a new API key."""
        keys = self._load_keys()
        
        key_id = secrets.token_urlsafe(16)
        api_key = f"archie_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(api_key)
        
        keys[key_id] = {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": name,
            "owner_email": owner_email,
            "description": description,
            "created_at": dt_module.datetime.now().isoformat(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0
        }
        
        self._save_keys(keys)
        
        return {
            "key_id": key_id,
            "api_key": api_key,
            "name": name,
            "owner_email": owner_email,
            "created_at": keys[key_id]["created_at"],
            "message": "Save this API key - it will not be shown again!"
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return its metadata if valid."""
        if not api_key:
            return None
            
        key_hash = self._hash_key(api_key)
        
        with self._lock:
            keys = self._load_keys()
            
            for key_id, key_data in keys.items():
                if key_data["key_hash"] == key_hash and key_data["is_active"]:
                    key_data["last_used"] = dt_module.datetime.now().isoformat()
                    key_data["usage_count"] += 1
                    self._save_keys(keys)
                    return key_data.copy()
        
        return None
    
    def revoke_api_key(self, key_id: str, owner_email: str) -> bool:
        """Revoke an API key."""
        keys = self._load_keys()
        
        if key_id not in keys:
            return False
            
        if keys[key_id]["owner_email"] != owner_email:
            return False
        
        keys[key_id]["is_active"] = False
        self._save_keys(keys)
        return True
    
    def list_keys(self, owner_email: str) -> List[Dict]:
        """List all API keys for a user."""
        keys = self._load_keys()
        user_keys = []
        
        for key_id, key_data in keys.items():
            if key_data["owner_email"] == owner_email:
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

app = fk.Flask(__name__)

def Archie(query: str, conversation_history: list = None) -> str:
    """
    Synchronous wrapper to run the async gemini.Archie in a new event loop.
    """
    return asyncio.run(gemini.Archie(query, conversation_history=conversation_history))





@app.route("/", methods=["GET"])
def home():
    # Check if user has a session
    session_id = fk.request.cookies.get("session_id")
    if session_id:
        # User has session, redirect to chat
        return fk.redirect(fk.url_for("index"))
    # No session, show login page
    return fk.render_template("home.html")

@app.route("/index", methods=["GET"])
def index():
    # Main chat interface
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        # No session, redirect to login
        return fk.redirect(fk.url_for("home"))
    return fk.render_template("index.html")

@app.route("/api/archie", methods=["POST"])
def api_archie():
    start_time = time.time()
    
    data = fk.request.get_json()
    question = data.get("question", "")
    session_id = fk.request.cookies.get("session_id")
    user_email = fk.request.cookies.get("user_email")
    
    # Get conversation history if session exists
    conversation_history = []
    if session_id:
        conversation_history = session_manager.get_conversation_history(session_id)
    
    answer = Archie(question, conversation_history=conversation_history)
    
    # Calculate generation time
    generation_time = time.time() - start_time
    
    # Save to session if session_id exists
    if session_id:
        session_manager.add_message(session_id, "user", question)
        session_manager.add_message(session_id, "assistant", answer)
    
    # Collect analytics data
    data_collector.log_interaction(
        session_id=session_id if session_id else "no_session",
        user_email=user_email,
        ip_address=fk.request.remote_addr,
        device_info=fk.request.user_agent.string,
        question=question,
        answer=answer,
        generation_time_seconds=generation_time
    )
    
    print(f"Question: {question}\nAnswer: {answer}\n")
    return fk.jsonify({"answer": answer})
import datetime
@app.route("/api/archie/stream", methods=["POST"])
def api_archie_stream():
    """
    Streaming endpoint that returns AI responses token by token.
    This provides a better user experience by showing the AI "thinking" in real-time.
    """
    start_time = time.time()
    
    data = fk.request.get_json()
    question = data.get("question", "")
    session_id = fk.request.cookies.get("session_id")
    user_email = fk.request.cookies.get("user_email")
    
    # Capture request info for data collection
    ip_address = fk.request.remote_addr
    device_info = fk.request.user_agent.string
    
    def generate():
        full_response = ""
        loop = None
        try:
            # Get conversation history if session exists
            conversation_history = []
            if session_id:
                conversation_history = session_manager.get_conversation_history(session_id)
            
            # Create a new event loop for this request 
            loop = asyncio.new_event_loop()
            
            async_gen = gemini.Archie_streaming(question, conversation_history=conversation_history)
            while True:
                try:
                    # Get the next item from the async generator
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    
                    
                    if isinstance(chunk, str):
                        # Append it to the full response and stream it.
                        full_response += chunk
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                    
                    elif isinstance(chunk, dict):
                        # Make it JSON-safe before streaming. because trial and error is the only way to figure this out apparently
                        
                        if chunk.get('tool_name'):
                            # Create a NEW, safe dictionary for the client
                            json_safe_payload = {
                                'tool_name': chunk.get('tool_name'),
                                'tool_result_preview': str(chunk.get('tool_result'))[:500]
                            }
                            yield f"data: {json.dumps({'tool_call': json_safe_payload})}\n\n"
                            
                        elif chunk.get('final'):
                            # This is just a signal, ignore it.
                            pass
                        
                    
                    else:
                        # Safely log it and send a debug message.
                        
                        chunk_type = type(chunk).__name__
                        print(f"Warning: Received unexpected chunk type: {chunk_type}")
                        
                        # Optionally send a safe representation to the client
                        yield f"data: {json.dumps({'debug_info': f'Received object: {chunk_type}'})}\n\n"
                except StopAsyncIteration:
                    # The generator is done.
                    break
            
            # Calculate generation time 
            generation_time = time.time() - start_time
            
            # Save to session if session_id exists
            if session_id:

                session_manager.add_message(session_id, "user", question)
                session_manager.add_message(session_id, "assistant", full_response)
            
            # Collect analytics data I LOVE DATA COLLECTION
            data_collector.log_interaction(
                session_id=session_id if session_id else "no_session",
                user_email=user_email,
                ip_address=ip_address,
                device_info=device_info,
                question=question,
                answer=full_response,
                generation_time_seconds=generation_time
            )
            
            
            print(f"Question: {question}\nAnswer: {full_response}\n")
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            #print the traceback for debugging I may remove this but for now its useful
            print(f"Error during streaming generation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            
            # Clean up the event loop
            if loop is not None and not loop.is_closed():
                loop.close()
    
    return fk.Response(generate(), mimetype='text/event-stream')

#Gets conversation history for current session
@app.route("/api/sessions/history", methods=["GET"])
def get_session_history():
    """Get conversation history for current session."""
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        return fk.jsonify({"error": "No session found"}), 401
    
    history = session_manager.get_conversation_history(session_id)
    return fk.jsonify({"history": history})

#List all sessions for current user
@app.route("/api/sessions/list", methods=["GET"])
def list_user_sessions():
    """List all sessions for logged-in user."""
    user_email = fk.request.cookies.get("user_email")
    if not user_email:
        return fk.jsonify({"error": "Not logged in"}), 401
    
    sessions = session_manager.get_all_user_sessions_with_preview(user_email)
    return fk.jsonify({"sessions": sessions})

#get details for a specific session
@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_details(session_id):
    """Get details of a specific session."""
    user_email = fk.request.cookies.get("user_email")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session (or it's their current session)
    current_session_id = fk.request.cookies.get("session_id")
    if session_data.get("user_email") != user_email and session_id != current_session_id:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    return fk.jsonify(session_data)

#Delete a specific session
@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a specific session."""
    user_email = fk.request.cookies.get("user_email")
    current_session_id = fk.request.cookies.get("session_id")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session
    if session_data.get("user_email") != user_email and session_id != current_session_id:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    success = session_manager.delete_session(session_id, user_email)
    if success:
        return fk.jsonify({"message": "Session deleted"})
    else:
        return fk.jsonify({"error": "Failed to delete session"}), 500

#Create a new session
@app.route("/api/sessions/new", methods=["POST"])
def create_new_session():
    """Create a new chat session for the current user."""
    user_email = fk.request.cookies.get("user_email")
    
    session_id = session_manager.create_session(user_email=user_email)
    
    resp = fk.make_response(fk.jsonify({"session_id": session_id}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
    return resp

#Switch to a different session
@app.route("/api/sessions/switch/<session_id>", methods=["POST"])
def switch_session(session_id):
    """Switch to a different session."""
    user_email = fk.request.cookies.get("user_email")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session
    if session_data.get("user_email") != user_email:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    resp = fk.make_response(fk.jsonify({"message": "Session switched"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp

#This is not used and guests are no longer supported. I am keeping it for potential future use.
@app.route("/gchats", methods=["GET", "POST"])
def gchats():
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        # Create new guest session
        session_id = session_manager.create_session(user_email=None)

    # render template and attach session cookie
    resp = fk.make_response(fk.redirect(fk.url_for("index")))
    print(f"New guest session started: {session_id}")
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
    return resp
@app.route("/chats", methods=["GET", "POST"])
def chats():
    if fk.request.method == "POST":
        email = fk.request.form.get("email", "").strip()
        password = fk.request.form.get("password", "")
        
        # Basic email validation
        if not email or "@" not in email or len(email) > 255:
            return fk.render_template("home.html", error="Please provide a valid email address")
        
        if not password:
            return fk.render_template("home.html", error="Password is required")

        if email and password:
            # Try to authenticate user
            if session_manager.authenticate_user(email, password):
                # Create new session for logged-in user
                session_id = session_manager.create_session(user_email=email)
                
                resp = fk.make_response(fk.redirect(fk.url_for("index")))
                print(f"User {email} logged in with session: {session_id}")

                resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
                resp.set_cookie("user_email", email, httponly=True, samesite="Strict")
                return resp
            else:
                # User doesn't exist, create new account
                if session_manager.create_user(email, password, ip_address=fk.request.remote_addr, device_info=fk.request.user_agent.string):
                    session_id = session_manager.create_session(user_email=email)

                    resp = fk.make_response(fk.redirect(fk.url_for("index")))
                    print(f"New user {email} created with session: {session_id}")
                    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
                    resp.set_cookie("user_email", email, httponly=True, samesite="Strict")
                    return resp
                else:
                    return fk.render_template("home.html", error="Failed to create account")
        else:
            return fk.render_template("home.html", error="Please provide email and password")
    return fk.render_template("home.html")


def background_checker():
    urls = {
        "website": "https://www.arcadia.edu/",
        "events": "https://www.arcadia.edu/events/?mode=month",
        "about": "https://www.arcadia.edu/about-arcadia/",
        "weather": "https://weather.com/weather/today/l/b0f4fc1167769407f55347d55f492a46e194ccaed63281d2fa3db2e515020994",
        "diningHours": "https://www.arcadia.edu/life-arcadia/living-commuting/dining/",
        "ITresources": "https://www.arcadia.edu/life-arcadia/campus-life-resources/information-technology/",
        "Academic Calendar": "https://www.arcadia.edu/academics/resources/academic-calendars/2025-26/",
        }
    

    dictionary = {}
    for name, url in urls.items():
        result = gemini.scrape_website(url)
        dictionary[name] = result

    # ensure the data directory exists, then write the collected dictionary as JSON
    os.makedirs(os.path.dirname("data/scrape_results.json"), exist_ok=True)
    with open("data/scrape_results.json", "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=4)


# ============================================================================
# EXTERNAL API (API Key Authentication)
# ============================================================================

# Create Flask Blueprint for external API routes
api_bp = fk.Blueprint("external_api", __name__, url_prefix="/api/v1")


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = fk.request.headers.get("X-API-Key")
        
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
        
        fk.g.api_key_data = key_data
        return f(*args, **kwargs)
    
    return decorated_function


async def collect_streaming_response_api(message: str) -> str:
    """Collect full response from streaming AI generator for API."""
    full_response = ""
    async for chunk in gemini.Archie_streaming(message):
        if isinstance(chunk, str):
            full_response += chunk
        elif isinstance(chunk, dict):
            if chunk.get('final'):
                break
    return full_response


# API Key Management Endpoints

@api_bp.route("/keys/generate", methods=["POST"])
def api_generate_key():
    """Generate a new API key."""
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
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, owner_email) or len(owner_email) > 255:
        return fk.jsonify({"error": "Invalid email address"}), 400
    
    result = api_key_manager.generate_api_key(name, owner_email, description)
    return fk.jsonify(result), 201


@api_bp.route("/keys", methods=["GET"])
def api_list_keys():
    """List all API keys for a user."""
    owner_email = fk.request.args.get("owner_email")
    
    if not owner_email:
        return fk.jsonify({"error": "owner_email query parameter required"}), 400
    
    keys = api_key_manager.list_keys(owner_email)
    return fk.jsonify({"keys": keys})


@api_bp.route("/keys/<key_id>/revoke", methods=["POST"])
def api_revoke_key(key_id):
    """Revoke an API key."""
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
def api_chat():
    """Send a message to ArchieAI and get a response."""
    start_time = time.time()
    
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    message = data.get("message")
    
    if not message:
        return fk.jsonify({"error": "message is required"}), 400
    
    response = asyncio.run(collect_streaming_response_api(message))
    
    generation_time = time.time() - start_time
    
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
def api_chat_stream():
    """Send a message to ArchieAI and get a streaming response."""
    start_time = time.time()
    
    data = fk.request.get_json()
    
    if not data:
        return fk.jsonify({"error": "Request body required"}), 400
    
    message = data.get("message")
    
    if not message:
        return fk.jsonify({"error": "message is required"}), 400
    
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
            api_logger.error(f"Error during streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if loop is not None and not loop.is_closed():
                loop.close()
    
    return fk.Response(generate(), mimetype='text/event-stream')


@api_bp.route("/health", methods=["GET"])
def api_health():
    """Health check endpoint (no authentication required)."""
    return fk.jsonify({
        "status": "healthy",
        "service": "ArchieAI API",
        "version": "1.0.0"
    })


@api_bp.route("/usage", methods=["GET"])
@require_api_key
def api_usage():
    """Get usage statistics for the authenticated API key."""
    key_data = fk.g.api_key_data
    return fk.jsonify({
        "key_id": key_data["key_id"],
        "name": key_data["name"],
        "usage_count": key_data["usage_count"],
        "last_used": key_data["last_used"],
        "created_at": key_data["created_at"]
    })


# API Documentation
@api_bp.route("/", methods=["GET"])
@api_bp.route("/docs", methods=["GET"])
def api_docs():
    """Serve API documentation page."""
    # Import the documentation HTML from the api.py module
    try:
        from api import API_DOCUMENTATION_HTML
        return fk.Response(API_DOCUMENTATION_HTML, mimetype='text/html')
    except ImportError:
        return fk.jsonify({
            "message": "Welcome to the ArchieAI API",
            "version": "1.0.0",
            "endpoints": {
                "docs": "/api/v1/docs",
                "health": "/api/v1/health",
                "keys/generate": "/api/v1/keys/generate",
                "keys": "/api/v1/keys",
                "chat": "/api/v1/chat",
                "chat/stream": "/api/v1/chat/stream",
                "usage": "/api/v1/usage"
            }
        })


# Register the API blueprint with the main app
app.register_blueprint(api_bp)

    
if __name__ == "__main__":


    qrCodeGen.make_qr("https://118ce87f29d4.ngrok-free.app", show=True, save_path="websiteqr.png")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)