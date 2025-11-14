# NASDAQ Stock Agent

> AI-powered stock analysis agent that provides investment recommendations for NASDAQ stocks using Claude AI.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 📖 What is This?

The NASDAQ Stock Agent is an intelligent AI system that analyzes stocks and provides investment recommendations. It uses:

- **Claude AI** (Anthropic) for intelligent analysis
- **Real-time market data** from yfinance
- **Technical analysis** (RSI, MACD, Moving Averages)
- **Fundamental analysis** (P/E ratios, EPS, Revenue)
- **Natural language processing** to understand your questions

### What Can It Do?

- Analyze any NASDAQ stock by ticker symbol (e.g., "AAPL", "TSLA")
- Answer questions in plain English (e.g., "Should I buy Apple stock?")
- Provide BUY/HOLD/SELL recommendations with confidence scores
- Explain the reasoning behind each recommendation
- Track analysis history in a database

### Example

**You ask:** "What do you think about Apple stock?"

**Agent responds:**
```json
{
  "symbol": "AAPL",
  "recommendation": "BUY",
  "confidence": 85,
  "current_price": 178.45,
  "reasoning": "Strong technical indicators with price above key moving averages.",
  "key_factors": [
    "Price above 50-day and 200-day moving averages",
    "Strong revenue growth of 8.5%",
    "Solid balance sheet"
  ],
  "risks": [
    "High valuation at 28.5x P/E ratio",
    "Potential regulatory headwinds"
  ]
}
```

## 🚀 Quick Start - Local Machine

### Prerequisites

- Docker and Docker Compose installed
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- 2GB+ RAM available

### Steps to Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/nasdaq-stock-agent.git
cd nasdaq-stock-agent
```

**2. Configure environment**
```bash
# Copy the template
cp .env.example .env

# Edit and add your API key
nano .env
```

Update this line in `.env`:
```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
```

**3. Start the application**
```bash
docker-compose up -d
```

**4. Test it**
```bash
# Check if it's running
curl http://localhost:8000/

# Analyze a stock
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "AAPL"}'
```

**5. View API documentation**

Open in your browser: http://localhost:8000/docs

**That's it!** Your agent is running on `http://localhost:8000`

### Stop the Application

```bash
docker-compose down
```

### Using the Startup Script

The `startup.sh` script automatically detects your public IP and configures NEST:

```bash
# For development
./startup.sh

# For production (AWS EC2)
./startup.sh prod
```

**What it does:**
- Detects public IP from AWS EC2 metadata or external services
- Updates `NEST_PUBLIC_URL` in `.env` automatically
- Optionally starts Docker services
- Shows configuration summary

## ☁️ Deploy to AWS EC2

### Prerequisites

- AWS account with EC2 access
- SSH key pair for EC2
- Anthropic API key

### Steps to Deploy on AWS EC2

**1. Launch EC2 Instance**

In AWS Console:
- Go to EC2 Dashboard → Launch Instance
- **Name**: nasdaq-stock-agent
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t3.medium (2 vCPU, 4GB RAM)
- **Key Pair**: Select or create new
- **Storage**: 20GB gp3
- **Security Group**: Create with these rules:
  - SSH (22) - Your IP
  - HTTP (80) - 0.0.0.0/0
  - Custom TCP (8000) - 0.0.0.0/0
  - Custom TCP (6000) - 0.0.0.0/0

**2. Connect to EC2**
```bash
# Set key permissions
chmod 400 your-key.pem

# SSH into instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

**3. Install Docker**
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

**4. Deploy Application**
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/nasdaq-stock-agent.git
cd nasdaq-stock-agent

# Configure environment
cp .env.example .env
nano .env
```

Update these values in `.env`:
```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
MONGO_ROOT_PASSWORD=your_secure_password_here
MONGO_PASSWORD=your_secure_password_here
# Note: NEST_PUBLIC_URL will be auto-detected by startup script
```

**5. Start Services (Automatic IP Detection)**

**Option A: Quick Deploy (Easiest)**
```bash
# One command deployment - handles everything
./quick-deploy.sh

# This will:
# 1. Create .env from template (if needed)
# 2. Detect your EC2 public IP automatically
# 3. Update NEST_PUBLIC_URL in .env
# 4. Start services in production mode
```

**Option B: Using Startup Script**
```bash
# If you already have .env configured
./startup.sh prod

# This will:
# 1. Detect your EC2 public IP
# 2. Update NEST_PUBLIC_URL in .env
# 3. Start services in production mode
```

**Option B: Manual Start**
```bash
# Manually update NEST_PUBLIC_URL with your EC2 IP
# Get your public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Update .env file
nano .env
# Set: NEST_PUBLIC_URL=http://YOUR_EC2_IP:6000

# Start with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

**6. Test Deployment**
```bash
# From your local machine
curl http://YOUR_EC2_PUBLIC_IP:8000/

# Analyze a stock
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "AAPL"}'
```

**7. Access API Documentation**

Open in browser: `http://YOUR_EC2_PUBLIC_IP:8000/docs`

### Manage EC2 Deployment

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update application
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📊 Usage Examples

### Using curl

```bash
# Analyze by ticker
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "AAPL"}'

# Natural language
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I buy Tesla stock?"}'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={"query": "AAPL"}
)

result = response.json()
print(f"Recommendation: {result['recommendation']}")
print(f"Confidence: {result['confidence']}%")
```

### Using JavaScript

```javascript
fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'AAPL' })
})
.then(res => res.json())
.then(data => console.log(data));
```

## 🔧 Configuration

### Docker Compose Files

This project includes two Docker Compose configurations:

#### `docker-compose.yml` (Development/Local)
- **Use for**: Local development and testing
- **MongoDB**: No authentication (simpler setup)
- **Nginx**: Not included (direct access to port 8000)
- **Command**: `docker-compose up -d`
- **Best for**: Quick local testing and development

#### `docker-compose.prod.yml` (Production/AWS EC2)
- **Use for**: Production deployments on AWS EC2 or other servers
- **MongoDB**: Authentication required (secure)
- **Nginx**: Included as reverse proxy (ports 80/443)
- **Resource Limits**: CPU and memory limits configured
- **Command**: `docker-compose -f docker-compose.prod.yml up -d`
- **Best for**: Production environments requiring security and scalability

**Key Differences:**

| Feature | docker-compose.yml | docker-compose.prod.yml |
|---------|-------------------|------------------------|
| MongoDB Auth | ❌ No | ✅ Yes (secure) |
| Nginx Proxy | ❌ No | ✅ Yes |
| Resource Limits | ❌ No | ✅ Yes |
| SSL Support | ❌ No | ✅ Yes |
| Restart Policy | unless-stopped | always |
| Use Case | Local Dev | Production |

### Required Environment Variables

```bash
# Anthropic API (Required)
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307

# MongoDB (Required)
MONGODB_URL=mongodb://mongodb:27017/
MONGODB_DATABASE=nasdaq_stock_agent
```

### Production Variables (AWS EC2)

```bash
# MongoDB Authentication (Required for docker-compose.prod.yml)
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_PASSWORD=your_secure_password

# NEST Integration (Optional)
NEST_ENABLED=true
NEST_PUBLIC_URL=http://YOUR_EC2_PUBLIC_IP:6000
```

See `.env.example` for all available configuration options.

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │ (Browser, curl, API calls)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Nginx     │ Port 80/443 (Production only)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FastAPI   │ Port 8000 (Main API)
│   Agent     │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │MongoDB │ │Claude  │ │yfinance│ │ NEST   │
   │Database│ │  AI    │ │ Market │ │ (A2A)  │
   └────────┘ └────────┘ └────────┘ └────────┘
```

## 🆘 Troubleshooting

### Agent Won't Start

```bash
# Check logs
docker-compose logs nasdaq-agent

# Verify API key is set
docker exec nasdaq-stock-agent env | grep ANTHROPIC

# Restart
docker-compose restart nasdaq-agent
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Stop the process or change PORT in .env
```

### Out of Memory (EC2)

```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📝 API Endpoints

- `GET /` - Health check
- `GET /docs` - Interactive API documentation
- `POST /api/v1/analyze` - Analyze stock
- `GET /api/v1/status` - System status
- `GET /health` - Health check

## 🔐 Security Notes

- Never commit `.env` file to Git (already in `.gitignore`)
- Use strong passwords for MongoDB in production
- Restrict EC2 security group to your IP for SSH
- Consider enabling SSL/TLS for production (update `nginx.conf`)
- Rotate API keys regularly

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **Issues**: Open a GitHub issue
- **Logs**: `docker-compose logs -f nasdaq-agent`

## 📄 License

This project is licensed under the MIT License.

---

**Made with ❤️ using Claude AI, FastAPI, and Docker**
