#!/bin/bash
set -e

echo "🚀 ArchieAI Setup Script"
echo "========================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed (try both old and new syntax)
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. You can edit it to customize your configuration."
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data/sessions
echo "✅ Data directory created"
echo ""

# Pull Ollama image
echo "🐳 Pulling Ollama Docker image..."
docker pull ollama/ollama:latest
echo "✅ Ollama image pulled"
echo ""

# Build the application
echo "🔨 Building ArchieAI application..."
$COMPOSE_CMD build
echo "✅ Application built"
echo ""

# Start services
echo "🚀 Starting services..."
$COMPOSE_CMD up -d
echo "✅ Services started"
echo ""

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if we should pull a model
read -p "📥 Do you want to pull the qwen3:4b model now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Pulling qwen3:4b model (this may take a while)..."
    docker exec archie-ollama ollama pull qwen3:4b
    echo "✅ Model pulled successfully"
    echo ""
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "🌐 ArchieAI is now running at: http://localhost:5000"
echo ""
echo "📋 Useful commands:"
echo "  - View logs:          $COMPOSE_CMD logs -f"
echo "  - Stop services:      $COMPOSE_CMD stop"
echo "  - Start services:     $COMPOSE_CMD start"
echo "  - Restart services:   $COMPOSE_CMD restart"
echo "  - Stop and remove:    $COMPOSE_CMD down"
echo "  - Pull a model:       docker exec archie-ollama ollama pull <model-name>"
echo "  - List models:        docker exec archie-ollama ollama list"
echo ""
echo "🎉 Happy chatting with ArchieAI!"
