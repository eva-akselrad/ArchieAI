<p align="center">
  <img src="src/static/imgs/Mini Knight Laptop.svg" alt="ArchieAI Logo" width="150"/>
</p>

<h1 align="center">ArchieAI</h1>

<p align="center">
  Archie AI is an AI-powered assistant designed to help users and students with a variety of tasks, from answering questions to providing recommendations and generating content. Built on Ollama for local LLM inference, ArchieAI aims to enhance productivity and make your experience at Arcadia University more efficient and enjoyable.
</p>

## Quick Start

Get started with ArchieAI in minutes using Docker:

```bash
# Clone the repository
git clone https://github.com/eva-akselrad/ArchieAI.git
cd ArchieAI

# Configure environment
cp .env.example .env

# Start the application
docker compose up -d

# Pull an Ollama model
docker exec -it archieai-ollama ollama pull qwen3

# Access at http://localhost:5000
```

## Features
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

## Setup

### Docker Deployment (Recommended)

The easiest way to deploy ArchieAI is using Docker and Docker Compose:

1. **Prerequisites:**
   - Install [Docker](https://docs.docker.com/get-docker/)
   - Install [Docker Compose](https://docs.docker.com/compose/install/)

2. **Configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your preferred model (e.g., `MODEL=qwen3`)

3. **Start the application:**
   ```bash
   docker compose up -d
   ```
   This will:
   - Build the ArchieAI application container
   - Start the Ollama service for local LLM inference
   - Set up persistent volumes for data and model storage

4. **Pull your preferred Ollama model:**
   ```bash
   docker exec -it archieai-ollama ollama pull qwen3
   ```
   Note: You can use any Ollama model. For tool calling support (web search), use `qwen3` or another tool-compatible model.

5. **Access the application:**
   - Web interface: `http://localhost:5000`
   - Ollama API: `http://localhost:11434`

6. **Useful Docker commands:**
   ```bash
   # View logs
   docker compose logs -f app
   
   # Stop the application
   docker compose down
   
   # Restart services
   docker compose restart
   
   # Remove all containers and volumes
   docker compose down -v
   ```

### Manual Installation

If you prefer to run ArchieAI without Docker:

1. Install [Ollama](https://ollama.ai/) on your system
2. Pull a model that supports tool calling: `ollama pull qwen3` (recommended for tool calling support)
3. Copy `.env.example` to `.env` and configure your model:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your preferred model (e.g., `MODEL=qwen3`)
5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Initialize data directories:
   ```bash
   mkdir -p data/sessions
   echo '{}' > data/qna.json
   ```
7. Run the application:
   ```bash
   python src/app.py
   ```
8. Access the web interface at `http://localhost:5000`

## Docker Configuration

### GPU Support (Optional)

If you have an NVIDIA GPU and want to use it for faster inference:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment the GPU configuration in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```
3. Restart the services: `docker compose down && docker compose up -d`

### Data Persistence

All application data is stored in volumes:
- `./data` - User sessions, chat history, and scraped data (mapped to host)
- `ollama_data` - Ollama models and configuration (Docker volume)

To backup your data:
```bash
# Backup application data
tar -czf archieai-backup.tar.gz data/

# Backup Ollama models
docker run --rm -v archieai_ollama_data:/data -v $(pwd):/backup alpine tar -czf /backup/ollama-models.tar.gz -C /data .
```

### Environment Variables

Configure the application by editing `.env`:
- `MODEL` - The Ollama model to use for responses (default: llama2)
- `OLLAMA_MODEL` - Model for streaming with tool support (default: qwen3)
- `OLLAMA_API_KEY` - Optional API key for Ollama authentication

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
- **Note:** Requires a model with tool calling support (e.g., qwen3)

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

### Running in Development Mode

**With Docker:**
```bash
# Start services
docker compose up

# View live logs
docker compose logs -f

# Access container shell
docker exec -it archieai-app bash
```

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run application in debug mode
python src/app.py
```

### Web Scraper

To run the web scraper manually:
```bash
# With Docker
docker exec -it archieai-app python src/helpers/scraper.py

# Without Docker
python src/helpers/scraper.py
```

The scraper runs in a loop and updates university data every hour.

### Testing with Different Models

Pull and test different Ollama models:
```bash
# With Docker
docker exec -it archieai-ollama ollama pull llama3
docker exec -it archieai-ollama ollama pull mistral
docker exec -it archieai-ollama ollama pull qwen3

# List available models
docker exec -it archieai-ollama ollama list
```

Then update your `.env` file with the desired model and restart the app.

## Troubleshooting

### Common Issues

**Issue: Application can't connect to Ollama**
- Ensure Ollama service is running: `docker compose ps`
- Check Ollama logs: `docker compose logs ollama`
- Verify Ollama is accessible: `curl http://localhost:11434/api/version`

**Issue: Model not found**
- Pull the model: `docker exec -it archieai-ollama ollama pull <model-name>`
- Check available models: `docker exec -it archieai-ollama ollama list`
- Ensure the MODEL in `.env` matches an installed model

**Issue: Port already in use**
- Change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "5001:5000"  # Use port 5001 on host instead
  ```

**Issue: Permission denied on data directory**
- Fix permissions: `sudo chown -R $USER:$USER data/`

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is developed for Arcadia University.
