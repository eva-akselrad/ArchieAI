<p align="center">
  <img src="/static/imgs/Mini Knight Laptop.svg" alt="ArchieAI Logo" width="150"/>
</p>

<h1 align="center">ArchieAI</h1>

<p align="center">
  Archie AI is an AI-powered assistant designed to help users and students with a variety of tasks, from answering questions to providing recommendations and generating content. Built on Ollama for local LLM inference, ArchieAI aims to enhance productivity and make your experience at Arcadia University more efficient and enjoyable.
</p>

---

**📖 [Quick Start Guide](QUICK_START.md)** | **🐳 Docker Setup Below** | **💬 [Report Issues](https://github.com/eva-akselrad/ArchieAI/issues)**

---

## Features
- **🐳 Docker Support:** One-command setup with Docker and Docker Compose
- **Natural Language Understanding:** Communicates in a human-like manner.  
- **Contextual Awareness:** Remembers previous interactions for better responses.  
- **Streaming Responses:** See the AI "thinking" in real-time with token-by-token streaming.
- **Local LLM Inference:** Uses Ollama for privacy-focused, local AI processing.
- **Multi-Tasking:** Handles a wide range of tasks including writing, research, and data analysis.  
- **Customizable:** Tailor responses and functionalities to suit individual needs.  
- **Integration:** Easily integrates with various platforms and applications.
- **Tool-Based Web Search:** Uses Ollama's tool calling to intelligently search the web when needed.
- **Session Management:** Persistent chat history with support for multiple sessions per user.
- **Account System:** User authentication with password hashing for secure login.
- **Chat History:** View, load, and delete previous conversations.
- **Web Scraping:** Automated scraping of Arcadia University resources for up-to-date information.  

## Quick Start with Docker 🐳

The fastest way to get ArchieAI running is with Docker. This method automatically sets up everything including Ollama.

### Prerequisites
- [Docker Desktop](https://docs.docker.com/get-docker/) installed and **running**
  - **Windows users:** Make sure Docker Desktop is started before running commands
  - **Linux users:** Ensure Docker service is running: `sudo systemctl start docker`

### Docker Setup (No Scripts Required)

**Step 1: Clone and Configure**
```bash
# Clone the repository
git clone https://github.com/eva-akselrad/ArchieAI.git
cd ArchieAI

# Create environment file (copy and customize if needed)
cp .env.example .env
```

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

**Step 2: Create Data Directory**
```bash
mkdir -p data/sessions
```

**Windows PowerShell:**
```powershell
New-Item -ItemType Directory -Force -Path data/sessions
```

**Step 3: Start Services**
```bash
docker compose up -d
```

**Windows PowerShell:**
```powershell
docker compose up -d
```

**Step 4: Pull AI Model**

Wait for services to start (about 30 seconds), then pull a model:

```bash
# Default model (recommended)
docker exec archie-ollama ollama pull qwen3:4b

# OR advanced model (requires 32GB+ RAM)
docker exec archie-ollama ollama pull qwen3:235b
```

**Step 5: Access the Application**

Open your browser to: **http://localhost:5000**

### Troubleshooting Docker Desktop on Windows

If you get "cannot find the file specified" or similar errors:

1. **Ensure Docker Desktop is running** - Check the system tray for the Docker icon
2. **Restart Docker Desktop** - Right-click the icon and select "Restart"
3. **Wait for Docker to fully start** - The icon should show "Docker Desktop is running"
4. **Try again** - Run `docker compose up -d`

If issues persist:
```powershell
# Clean and rebuild
docker compose down
docker compose up -d --build
```

### Docker Management Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose stop

# Start services
docker compose start

# Restart services
docker compose restart

# Stop and remove containers
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Pull a different model
docker exec archie-ollama ollama pull <model-name>

# List available models
docker exec archie-ollama ollama list
```

**Note:** If you have an older Docker installation, replace `docker compose` with `docker-compose` in all commands.

### Optional: Automated Setup Script

For Linux/Mac users, there's an optional setup script that automates all the steps:

```bash
./setup.sh
```

This script is **not required** - the manual Docker steps above work on all platforms including Windows.

### Configuration

Edit `.env` file to customize:
- `MODEL`: Change AI model (default: `qwen3:4b`, advanced: `qwen3:235b`)
- `OLLAMA_HOST`: Ollama server URL
- `OLLAMA_PORT`: Ollama port (default: `11434`)

## Setup

### Running the Rust Version

1. Install [Ollama](https://ollama.ai/) on your system
2. Pull the AI model: `ollama pull qwen3:4b` (or `qwen3:235b` for advanced quality)
3. Copy `.env.example` to `.env` and configure your model:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your preferred model (default is `MODEL=qwen3:4b`)
5. Build and run with Cargo:
   ```bash
   cargo run --release
   ```
6. Access the web interface at `http://localhost:5000`

## Usage

### Getting Started
1. Visit `http://localhost:5000` in your web browser
2. Choose to login with an account or continue as a guest
3. Start chatting with ArchieAI!

### Features Guide

#### Chat History
- Click the history icon (clock) in the chat interface to view previous conversations
- Click "Load" to switch to a previous chat session
- Click "Delete" to remove a chat session permanently
- Click "+ New Chat" to start a fresh conversation

#### Account Management
- First-time users: Enter email and password to create an account automatically
- Returning users: Login with your credentials to access your chat history
- Guest users: Continue without an account (history not saved across sessions)

#### Web Search
ArchieAI uses Ollama's tool calling feature to intelligently search the web when:
- The scraped university data doesn't contain the answer
- The query requires current/real-time information
- The AI determines additional information is needed
- **Note:** qwen3 models have excellent tool calling support

#### Session Context
- Each conversation maintains context within the session
- Recent messages (last 5) are used to provide context for responses
- Context is preserved when loading previous sessions

## API Endpoints

### Chat Endpoints
- `POST /api/archie` - Send a question (non-streaming)
- `POST /api/archie/stream` - Send a question (streaming response)

### Session Management
- `GET /api/sessions/history` - Get current session history
- `GET /api/sessions/list` - List all user sessions (requires login)
- `GET /api/sessions/<id>` - Get specific session details
- `DELETE /api/sessions/<id>` - Delete a session
- `POST /api/sessions/new` - Create new session
- `POST /api/sessions/switch/<id>` - Switch to different session

## Data Storage

All data is stored locally in JSON files:
- `data/users.json` - User accounts with hashed passwords
- `data/sessions/*.json` - Individual chat sessions
- `data/qna.json` - Question-answer pairs (legacy storage)

## Development

### Running Tests

The Rust implementation includes comprehensive test coverage with 44 tests:
- **main.rs**: 9 tests covering route handlers, cookies, request/response types
- **session_manager.rs**: 14 tests covering user authentication, session management, password hashing
- **data_collector.rs**: 8 tests covering analytics logging and data persistence
- **gem_interface.rs**: 13 tests covering AI interface and message handling

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name
```

### Building for Production

```bash
# Build optimized release binary
cargo build --release

# Binary will be in target/release/archie-ai-rust
./target/release/archie-ai-rust
```

## Troubleshooting

### Docker Issues

**Services won't start:**
```bash
# Check if ports are available
sudo lsof -i :5000
sudo lsof -i :11434

# Restart Docker
sudo systemctl restart docker  # Linux
# OR restart Docker Desktop on Mac/Windows
```

**Ollama model not found:**
```bash
# Pull the default model
docker exec archie-ollama ollama pull qwen3:4b

# OR pull the advanced model (requires more RAM)
docker exec archie-ollama ollama pull qwen3:235b

# Verify model is installed
docker exec archie-ollama ollama list
```

**Permission denied errors:**
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

**Container keeps restarting:**
```bash
# Check logs
docker-compose logs archie-ai
docker-compose logs ollama

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Application Issues

**"Failed to load home page" error:**
- Ensure templates exist in `src/templates/`
- Check file permissions
- Verify Docker volume mounts

**AI not responding:**
- Ensure Ollama is running: `docker ps`
- Check model is pulled: `docker exec archie-ollama ollama list`
- Verify `.env` has correct `MODEL` name

**Session not persisting:**
- Check `data/` directory exists and is writable
- Verify Docker volume mount in `docker-compose.yml`

## System Requirements

- **RAM:** Minimum 8GB (16GB recommended for larger models)
- **Storage:** 10GB+ free space (models can be large)
- **CPU:** Multi-core processor recommended
- **OS:** Linux, macOS, or Windows with Docker support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational purposes at Arcadia University.
