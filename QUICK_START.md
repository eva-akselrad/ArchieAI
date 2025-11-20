# ArchieAI Quick Start Guide

## 🚀 Fastest Setup

### Prerequisites
- [Ollama](https://ollama.ai/) installed on your system
- [Rust](https://rustup.rs/) installed (for building the application)

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/eva-akselrad/ArchieAI.git
cd ArchieAI

# 2. Install and start Ollama (if not already installed)
# Visit https://ollama.ai/ for installation instructions

# 3. Pull the AI model
ollama pull qwen3:4b

# 4. Create environment file
cp .env.example .env

# 5. Create data directory
mkdir -p data/sessions

# 6. Build and run the application
cargo run --release
```

Then open: http://localhost:5000

## 📋 Common Commands

### Development
```bash
cargo run                    # Run in debug mode
cargo run --release         # Run optimized release build
cargo build --release       # Build without running
cargo test                  # Run tests
```

### Ollama Management
```bash
ollama list                 # List installed models
ollama pull qwen3:4b        # Pull default model
ollama pull qwen3:235b      # Pull advanced model (larger)
ollama rm qwen3:4b          # Remove a model
ollama serve                # Start Ollama service (if not running)
```

### Application Management
```bash
# Stop the application: Press Ctrl+C in the terminal where it's running

# Update application
git pull
cargo build --release
cargo run --release
```

## 🔧 Configuration

Edit `.env` file:
```env
MODEL=qwen3:4b                      # Change AI model (default: qwen3:4b, advanced: qwen3:235b)
OLLAMA_HOST=http://localhost        # Ollama host
OLLAMA_PORT=11434                   # Ollama port
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# If another process is using it, stop it or change the port in the Rust application
```

### Ollama Not Running
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Or on macOS/Linux, Ollama runs as a service after installation
```

### Model Not Responding
```bash
# Ensure model is installed
ollama list

# Pull the default model if missing
ollama pull qwen3:4b

# Verify Ollama is accessible
curl http://localhost:11434/api/tags
```

### Build Issues
```bash
# Update Rust toolchain
rustup update

# Clean build
cargo clean
cargo build --release
```

## 📊 System Requirements

- **Minimum (qwen3:4b):** 8GB RAM, 10GB disk space
- **Recommended (qwen3:4b):** 16GB RAM, 15GB disk space
- **Advanced (qwen3:235b):** 32GB+ RAM, 150GB+ disk space
- **CPU:** Multi-core processor recommended
- **OS:** Linux, macOS, or Windows with Rust support

## 🎯 Quick Tips

1. **First time setup:** Follow the commands above to get started
2. **Change models:** Update `MODEL` in `.env`, pull the new model with `ollama pull`, and restart the app
3. **Persistent data:** All chats saved in `./data/` directory
4. **Check Ollama status:** Run `ollama list` to see installed models
5. **Performance:** Use `cargo run --release` for better performance

## 🔗 Useful Links

- Main app: http://localhost:5000
- Ollama API: http://localhost:11434
- Ollama Documentation: https://ollama.ai/
- Rust Documentation: https://doc.rust-lang.org/
- Full Documentation: See README.md

## ⚡ Advanced

### Run Tests
```bash
cargo test
cargo test -- --nocapture  # Show test output
```

### Build Optimized Binary
```bash
cargo build --release
./target/release/archie-ai-rust
```

### Clean Build Artifacts
```bash
cargo clean
```

### Development Mode with Auto-Reload
```bash
# Install cargo-watch
cargo install cargo-watch

# Run with auto-reload
cargo watch -x run
```
