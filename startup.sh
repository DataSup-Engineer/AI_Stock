#!/bin/bash

# Startup script for NASDAQ Stock Agent on AWS EC2
# Automatically detects public IP and updates NEST_PUBLIC_URL

set -e

echo "=================================================="
echo "NASDAQ Stock Agent - AWS EC2 Startup"
echo "=================================================="
echo ""

# Function to get public IP
get_public_ip() {
    # Try multiple services to get public IP
    local ip=""
    
    # Try AWS EC2 metadata service first (most reliable on EC2)
    ip=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
    
    if [ -z "$ip" ]; then
        # Fallback to external services
        ip=$(curl -s --connect-timeout 2 https://api.ipify.org 2>/dev/null || echo "")
    fi
    
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 2 https://ifconfig.me 2>/dev/null || echo "")
    fi
    
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 2 https://icanhazip.com 2>/dev/null || echo "")
    fi
    
    echo "$ip"
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file first: cp .env.example .env"
    exit 1
fi

echo "📡 Detecting public IP address..."
PUBLIC_IP=$(get_public_ip)

if [ -z "$PUBLIC_IP" ]; then
    echo "❌ Error: Could not detect public IP address"
    echo "Please set NEST_PUBLIC_URL manually in .env file"
    exit 1
fi

echo "✅ Detected public IP: $PUBLIC_IP"
echo ""

# Update NEST_PUBLIC_URL in .env file
echo "🔧 Updating NEST_PUBLIC_URL in .env..."

# Check if NEST_PUBLIC_URL exists in .env
if grep -q "^NEST_PUBLIC_URL=" .env; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^NEST_PUBLIC_URL=.*|NEST_PUBLIC_URL=http://${PUBLIC_IP}:6000|" .env
    else
        # Linux
        sed -i "s|^NEST_PUBLIC_URL=.*|NEST_PUBLIC_URL=http://${PUBLIC_IP}:6000|" .env
    fi
    echo "✅ Updated NEST_PUBLIC_URL=http://${PUBLIC_IP}:6000"
else
    # Add new line if not exists
    echo "NEST_PUBLIC_URL=http://${PUBLIC_IP}:6000" >> .env
    echo "✅ Added NEST_PUBLIC_URL=http://${PUBLIC_IP}:6000"
fi

echo ""
echo "📋 Current NEST Configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep "^NEST_" .env | while read line; do
    echo "  $line"
done
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask user if they want to start the services
read -p "🚀 Start services now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🐳 Starting Docker services..."
    echo ""
    
    # Check if production or development
    if [ -f "docker-compose.prod.yml" ] && [ "$1" == "prod" ]; then
        echo "Starting in PRODUCTION mode..."
        docker-compose -f docker-compose.prod.yml up -d
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📊 View logs:"
        echo "  docker-compose -f docker-compose.prod.yml logs -f"
    else
        echo "Starting in DEVELOPMENT mode..."
        docker-compose up -d
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📊 View logs:"
        echo "  docker-compose logs -f"
    fi
    
    echo ""
    echo "🔍 Verify NEST registration (wait 30 seconds):"
    echo "  curl http://registry.chat39.com:6900/agents/nasdaq-stock-agent"
    echo ""
    echo "🌐 Access your agent:"
    echo "  API: http://${PUBLIC_IP}:8000"
    echo "  Docs: http://${PUBLIC_IP}:8000/docs"
    echo "  NEST: http://${PUBLIC_IP}:6000"
else
    echo ""
    echo "ℹ️  Configuration updated. Start services manually:"
    echo "  Development: docker-compose up -d"
    echo "  Production:  docker-compose -f docker-compose.prod.yml up -d"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
