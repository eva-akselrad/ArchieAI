# ArchieAI Quick Start Guide (May not work correctly docker is being strange)

## 🚀 Fastest Setup (Docker)

```bash
# Clone the repository
git clone https://github.com/eva-akselrad/ArchieAI.git
cd ArchieAI

# Create environment file
cp .env.example .env

# Create data directory
mkdir -p data/sessions

# Start services with Docker Compose
docker compose up -d

# Pull the AI model
docker exec archie-ollama ollama pull qwen3:4b
```
# WARNING THIS TAKES LIKE 30 YEARS TO DO SO BE PREPARED
Then open: http://localhost:5000

## 📋 Common Commands

### Start/Stop
```bash
docker compose up -d        # Start in background
docker compose stop         # Stop services
docker compose restart      # Restart services
docker compose down         # Stop and remove containers
```

### View Logs
```bash
docker compose logs -f              # All services
docker compose logs -f archie-ai    # Just ArchieAI
docker compose logs -f ollama       # Just Ollama
```

### Manage Models
```bash
    docker exec archie-ollama ollama list                    # List installed models
docker exec archie-ollama ollama pull qwen3:4b           # Pull default model
docker exec archie-ollama ollama pull qwen3:235b         # Pull advanced model (larger)
docker exec archie-ollama ollama rm qwen3:4b             # Remove a model
```

### Update Application
```bash
git pull
docker compose up -d --build
```

## 🔧 Configuration

Edit `.env` file:
```env
MODEL=qwen3:4b                      # Change AI model (default: qwen3:4b, advanced: qwen3:235b)
OLLAMA_HOST=http://ollama           # Ollama host (leave as-is for Docker)
OLLAMA_PORT=11434                   # Ollama port
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Or change port in docker-compose.yml:
# ports:
#   - "8080:5000"  # Use port 8080 instead
```

### Container Won't Start
```bash
docker compose logs archie-ai   # Check logs
docker compose down             # Clean up
docker compose up -d --build    # Rebuild and start
```

### Model Not Responding
```bash
# Ensure model is installed
docker exec archie-ollama ollama list

# Pull the default model
docker exec archie-ollama ollama pull qwen3:4b

# Restart services
docker compose restart
```

## 📊 System Requirements

- **Minimum (qwen3:4b):** 8GB RAM, 15GB disk space
- **Recommended (qwen3:4b):** 16GB RAM, 20GB disk space
- **Advanced (qwen3:235b):** 32GB+ RAM, 150GB+ disk space
- **CPU:** Multi-core processor

## 🎯 Quick Tips

1. **First time setup:** Follow the commands above - no script needed!
2. **Change models:** Update `MODEL` in `.env` and pull the new model
3. **Persistent data:** All chats saved in `./data/` directory
4. **View all commands:** `docker compose --help`
5. **Check status:** `docker compose ps`

## 🔗 Useful Links

- Main app: http://localhost:5000
- Ollama API: http://localhost:11434
- Documentation: See README.md

## ⚡ Advanced

### Build Only
```bash
docker compose build
```

### Run in Foreground (see logs immediately)
```bash
docker compose up
```

### Clean Everything (⚠️ deletes data)
```bash
docker compose down -v
rm -rf data/
```

### Check Resource Usage
```bash
docker stats
```