#!/bin/bash

# Quick deployment script for AWS EC2
# One command to deploy everything

set -e

echo "🚀 NASDAQ Stock Agent - Quick Deploy"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Run startup script
echo ""
echo "🔧 Running startup script..."
./startup.sh prod

echo ""
echo "✅ Deployment complete!"
