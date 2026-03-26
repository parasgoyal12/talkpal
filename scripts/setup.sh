#!/bin/bash

# Setup script for Study Companion Bot

set -e

echo "🚀 Study Companion Bot - Setup Script"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your credentials:"
    echo "   - AZURE_OPENAI_API_KEY"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo ""
    echo "   Run this script again after configuring .env"
    exit 0
else
    echo "✅ .env file exists"
fi

# Check if required variables are set
source .env

if [ -z "$AZURE_OPENAI_API_KEY" ] || [ "$AZURE_OPENAI_API_KEY" = "your_azure_openai_key_here" ]; then
    echo "❌ AZURE_OPENAI_API_KEY is not configured in .env"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN is not configured in .env"
    exit 1
fi

echo "✅ Environment variables are configured"
echo ""

# Pull Docker images
echo "📦 Pulling Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building application images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure n8n workflows:"
echo "      - Open http://localhost:5678"
echo "      - Login with admin/changeme"
echo "      - Import workflows from n8n_workflows/"
echo ""
echo "   2. Test your bot:"
echo "      - Open Telegram"
echo "      - Search for your bot"
echo "      - Send /start"
echo ""
echo "   3. View logs:"
echo "      docker-compose logs -f telegram-bot"
echo ""
echo "🎉 Happy studying!"
