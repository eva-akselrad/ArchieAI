<p align="center">
  <img src="src/static/imgs/Mini Knight Laptop.svg" alt="ArchieAI Logo" width="150"/>
</p>

<h1 align="center">ArchieAI</h1>

<p align="center">
  ArchieAI is an AI-powered assistant that's *totally* going to revolutionize your life (or at least pretend to). It helps with various tasks, from answering questions you could've Googled to generating content you'll definitely take full credit for. Built on Ollama because apparently running AI locally is the hip thing to do now. It'll make your Arcadia University experience more "efficient and enjoyable" - and yes, we used air quotes there.
</p>

## Quick Start

Oh look, you want to get started *quickly*? How modern of you. Here's your paint-by-numbers deployment (because apparently reading the full docs is too mainstream):

```bash
# Clone the repository (yes, you need to type this yourself)
git clone https://github.com/eva-akselrad/ArchieAI.git
cd ArchieAI

# Configure environment (fancy way of saying "copy a file")
cp .env.example .env

# Start the application (and pray to the Docker gods)
docker compose up -d

# Pull an Ollama model (because the AI doesn't just magically exist)
docker exec -it archieai-ollama ollama pull qwen3

# Access at http://localhost:5000 (if your computer didn't catch fire)
```

## Features
- **Natural Language Understanding:** It talks like a human. Scary, right? Don't worry, it's still dumber than you (probably).
- **Contextual Awareness:** It remembers your previous chat messages. Just like that friend who never lets you forget that embarrassing thing you said.
- **Streaming Responses:** Watch the AI "think" in real-time, one token at a time. It's like watching paint dry, but with more blinking cursors.
- **Local LLM Inference:** Your data stays on your computer. How... quaint. Privacy is so 2020s.
- **Multi-Tasking:** Handles writing, research, and data analysis. *Technically* does all three, *technically*.
- **Customizable:** Tailor it to your needs. Translation: you'll spend hours configuring it instead of using it.
- **Integration:** "Easily" integrates with platforms. Spoiler: "easily" is doing some heavy lifting here.
- **Tool-Based Web Search:** It can search the web when it doesn't know something. Revolutionary. Truly groundbreaking. Nobody's ever thought of that before.
- **Session Management:** Your chat history persists. Because what you really needed was a permanent record of your 3 AM existential questions.
- **Account System:** We hash your passwords because we're not *completely* irresponsible.
- **Chat History:** Load, view, delete conversations. Delete is there for when you realize how dumb your questions were.
- **Web Scraping:** Auto-scrapes Arcadia University resources. It's not stalking, it's "information gathering."  

## Setup

### Docker Deployment (Recommended)

*The* easiest way to deploy ArchieAI. We promise. Would we lie to you? (Don't answer that.)

1. **Prerequisites:**
   - Install [Docker](https://docs.docker.com/get-docker/) (Because installing software to run software is peak efficiency)
   - Install [Docker Compose](https://docs.docker.com/compose/install/) (Yes, they're separate. Welcome to modern development!)

2. **Configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your preferred model (e.g., `MODEL=qwen3`). Or don't. Live dangerously with the defaults.

3. **Start the application:**
   ```bash
   docker compose up -d
   ```
   This will magically:
   - Build the ArchieAI application container (hope you have decent internet)
   - Start the Ollama service for local LLM inference (local = your computer does all the work)
   - Set up persistent volumes (because losing your data would be *tragic*)

4. **Pull your preferred Ollama model:**
   ```bash
   docker exec -it archieai-ollama ollama pull qwen3
   ```
   Note: You can use *any* Ollama model. Go wild. Live your truth. For tool calling support (fancy speak for "web search"), use `qwen3` or another tool-compatible model. Choose wisely, or don't - the AI won't judge you. We might, but the AI won't.

5. **Access the application:**
   - Web interface: `http://localhost:5000` (assuming you didn't break anything)
   - Ollama API: `http://localhost:11434` (for the brave souls who want raw API access)

6. **Useful Docker commands:**
   ```bash
   # View logs (because something WILL go wrong)
   docker compose logs -f app
   
   # Stop the application (when you inevitably give up)
   docker compose down
   
   # Restart services (the classic "have you tried turning it off and on again")
   docker compose restart
   
   # Remove all containers and volumes (the nuclear option)
   docker compose down -v
   ```

### Manual Installation

Oh, you're one of *those* people who doesn't trust containers? Fine. Here's the hard way:

1. Install [Ollama](https://ollama.ai/) on your system (manually, like it's 2005)
2. Pull a model that supports tool calling: `ollama pull qwen3` (recommended, but feel free to ignore our recommendation)
3. Copy `.env.example` to `.env` and configure your model:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your preferred model (e.g., `MODEL=qwen3`). Yes, we're asking you to edit a text file. Welcome to the cutting edge.
5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Initialize data directories (because folders don't create themselves, shockingly):
   ```bash
   mkdir -p data/sessions
   echo '{}' > data/qna.json
   ```
7. Run the application:
   ```bash
   python src/app.py
   ```
8. Access the web interface at `http://localhost:5000` (fingers crossed!)

## Docker Configuration

### GPU Support (Optional)

Got a fancy NVIDIA GPU collecting dust? Put it to work (finally):

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (more installation! Yay!)
2. Uncomment the GPU configuration in `docker-compose.yml` (we left it commented because we *assume* you don't have a GPU):
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```
3. Restart the services: `docker compose down && docker compose up -d` (the ritual is complete)

### Data Persistence

Your precious data lives in these exciting locations:
- `./data` - User sessions, chat history, and scraped data (on YOUR computer - novel concept, right?)
- `ollama_data` - Ollama models and configuration (in a Docker volume, because why make things simple?)

To backup your data (for when, not if, disaster strikes):
```bash
# Backup application data (tar.gz, because we're vintage like that)
tar -czf archieai-backup.tar.gz data/

# Backup Ollama models (hope you understand what this command does, because explaining it would take forever)
docker run --rm -v archieai_ollama_data:/data -v $(pwd):/backup alpine tar -czf /backup/ollama-models.tar.gz -C /data .
```

### Environment Variables

Configure the application by editing `.env` (it's just a file, don't be scared):
- `MODEL` - The Ollama model to use for responses (default: llama2, because llama2 is *so* last season)
- `OLLAMA_MODEL` - Model for streaming with tool support (default: qwen3, which we keep recommending like a broken record)
- `OLLAMA_API_KEY` - Optional API key for Ollama authentication (optional = you probably don't need it, but who knows?)

## Usage

### Getting Started
1. Visit `http://localhost:5000` in your web browser (any browser, we're not picky... much)
2. Choose to login with an account or continue as a guest (commitment issues? We get it)
3. Start chatting with ArchieAI! (It's almost like talking to a real person, if that person was a large language model)

### Features Guide

#### Chat History
- Click the history icon (clock) in the chat interface to view previous conversations (nostalgia included)
- Click "Load" to switch to a previous chat session (time travel, kind of)
- Click "Delete" to remove a chat session permanently (the "oh god why did I say that" button)
- Click "+ New Chat" to start a fresh conversation (because fresh starts are *totally* a real thing)

#### Account Management
- First-time users: Enter email and password to create an account automatically (we're lazy, so we made it automatic)
- Returning users: Login with your credentials to access your chat history (assuming you remember your password)
- Guest users: Continue without an account (commitment-free since 2024!)

#### Web Search
ArchieAI uses Ollama's tool calling feature to "intelligently" search the web when:
- The scraped university data doesn't contain the answer (shocking, our scraper isn't omniscient)
- The query requires current/real-time information (because the AI can't predict the future... yet)
- The AI determines additional information is needed (it's basically admitting it doesn't know)
- **Note:** Requires a model with tool calling support (e.g., qwen3). We'll keep mentioning qwen3 until you download it.

#### Session Context
- Each conversation maintains context within the session (it remembers what you said, creepy right?)
- Recent messages (last 5) are used to provide context for responses (because memory is expensive, apparently)
- Context is preserved when loading previous sessions (your embarrassing questions persist across time)

## API Endpoints

For those who prefer talking to APIs instead of humans (we don't judge... much):

### Chat Endpoints
- `POST /api/archie` - Send a question (non-streaming, because who needs real-time responses?)
- `POST /api/archie/stream` - Send a question (streaming response, for the impatient folks)

### Session Management
- `GET /api/sessions/history` - Get current session history (your digital diary)
- `GET /api/sessions/list` - List all user sessions (requires login, sorry lurkers)
- `GET /api/sessions/<id>` - Get specific session details (stalk your own conversations)
- `DELETE /api/sessions/<id>` - Delete a session (the digital shredder)
- `POST /api/sessions/new` - Create new session (another fresh start, because the last one went so well)
- `POST /api/sessions/switch/<id>` - Switch to different session (session hopping, it's a lifestyle)

## Data Storage

All data is stored locally in JSON files (because databases are *so* mainstream):
- `data/users.json` - User accounts with hashed passwords (we're not *complete* monsters)
- `data/sessions/*.json` - Individual chat sessions (one file per session, efficient? Debatable.)
- `data/qna.json` - Question-answer pairs (legacy storage, AKA "we're too lazy to remove it")

## Development

### Running in Development Mode

Because production is for cowards:

**With Docker:**
```bash
# Start services (watch the magic happen)
docker compose up

# View live logs (become one with the terminal)
docker compose logs -f

# Access container shell (for when you need to feel like a hacker)
docker exec -it archieai-app bash
```

**Without Docker:**
```bash
# Install dependencies (again, because apparently once wasn't enough)
pip install -r requirements.txt

# Run application in debug mode (where all the fun error messages live)
python src/app.py
```

### Web Scraper

To run the web scraper manually (because automation is *so* automated):
```bash
# With Docker (the easy way)
docker exec -it archieai-app python src/helpers/scraper.py

# Without Docker (the "I like pain" way)
python src/helpers/scraper.py
```

The scraper runs in a loop and updates university data every hour. Riveting stuff. Really. We're on the edge of our seats.

### Testing with Different Models

Pull and test different Ollama models (gotta catch 'em all):
```bash
# With Docker (because typing docker exec is *such* a joy)
docker exec -it archieai-ollama ollama pull llama3
docker exec -it archieai-ollama ollama pull mistral
docker exec -it archieai-ollama ollama pull qwen3

# List available models (spoiler: it's the ones you just downloaded)
docker exec -it archieai-ollama ollama list
```

Then update your `.env` file with the desired model and restart the app. Rinse. Repeat. Welcome to development!

## Troubleshooting

Welcome to the inevitable "things broke" section. We knew you'd end up here.

### Common Issues

**Issue: Application can't connect to Ollama**
- Ensure Ollama service is running: `docker compose ps` (it's not running, is it?)
- Check Ollama logs: `docker compose logs ollama` (brace yourself for error messages)
- Verify Ollama is accessible: `curl http://localhost:11434/api/version` (if this works, you're luckier than most)

**Issue: Model not found**
- Pull the model: `docker exec -it archieai-ollama ollama pull <model-name>` (yes, you need to actually download it)
- Check available models: `docker exec -it archieai-ollama ollama list` (spoiler: empty list)
- Ensure the MODEL in `.env` matches an installed model (reading is fundamental)

**Issue: Port already in use**
- Change ports in `docker-compose.yml`: (because port 5000 is SO popular)
  ```yaml
  ports:
    - "5001:5000"  # Use port 5001 on host instead
  ```
- Or just stop whatever else is using port 5000. Your call.

**Issue: Permission denied on data directory**
- Fix permissions: `sudo chown -R $USER:$USER data/` (ah yes, the classic Linux permissions dance)
- Or run as root like a rebel (we don't recommend this, but we can't stop you)

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests. We promise to read them... eventually. Maybe. Probably.

## License

This project is developed for Arcadia University. All rights reserved. Or not. We're not lawyers. Don't sue us.
