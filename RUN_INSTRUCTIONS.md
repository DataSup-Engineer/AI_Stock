# NASDAQ Stock Agent - Complete Run Instructions

This guide provides step-by-step instructions for setting up and running the NASDAQ Stock Agent AI system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Agent](#running-the-agent)
5. [Testing the Agent](#testing-the-agent)
6. [NEST Integration (Optional)](#nest-integration-optional)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)
9. [Stopping the Agent](#stopping-the-agent)

---

## Prerequisites

Before running the NASDAQ Stock Agent, ensure you have the following installed:

### Required Software

1. **Python 3.9 or higher**
   ```bash
   python --version  # Should show 3.9.x or higher
   ```

2. **MongoDB 4.4 or higher**
   ```bash
   mongod --version  # Should show 4.4.x or higher
   ```

3. **Anthropic API Key**
   - Sign up at https://console.anthropic.com/
   - Create an API key from the dashboard
   - Keep this key secure - you'll need it for configuration

### System Requirements

- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: At least 2GB free space
- **Network**: Internet connection for API calls and market data
- **OS**: macOS, Linux, or Windows (WSL recommended for Windows)

---

## Installation

### Step 1: Clone or Download the Repository

```bash
# If using git
git clone <repository-url>
cd nasdaq-stock-agent

# Or if you have the files already, navigate to the directory
cd /path/to/nasdaq-stock-agent
```

### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
which python  # Should point to venv/bin/python
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|langchain|anthropic|pymongo"
```

**Expected packages:**
- fastapi (0.104.0+)
- langchain (0.1.0+)
- langchain-anthropic (0.1.0+)
- anthropic (0.7.0+)
- pymongo (4.6.0+)
- motor (3.3.0+)

### Step 4: Install MongoDB

#### macOS (using Homebrew)
```bash
# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify MongoDB is running
brew services list | grep mongodb
```

#### Linux (Ubuntu/Debian)
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify MongoDB is running
sudo systemctl status mongod
```

#### Using Docker (All Platforms)
```bash
# Pull MongoDB image
docker pull mongo:latest

# Run MongoDB container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:latest

# Verify container is running
docker ps | grep mongodb
```

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Open the file for editing
nano .env  # or use your preferred editor (vim, code, etc.)
```

### Step 2: Configure Required Settings

Edit `.env` and set the following **required** values:

```bash
# REQUIRED: Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# REQUIRED: MongoDB connection (default is usually fine)
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DATABASE=nasdaq_stock_agent

# REQUIRED: Application settings (defaults are usually fine)
APP_NAME=NASDAQ Stock Agent
APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### Step 3: Optional Configuration

You can also configure these optional settings:

```bash
# Cache settings (how long to cache market data)
CACHE_TTL_SECONDS=300  # 5 minutes

# Logging settings
LOG_RETENTION_DAYS=30  # Keep logs for 30 days

# Rate limiting
RATE_LIMIT_REQUESTS=100
MAX_CONCURRENT_REQUESTS=50

# YFinance timeout
YFINANCE_TIMEOUT=30
```

### Step 4: Verify Configuration

```bash
# Check that .env file exists and has your API key
cat .env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-api03-...
# (not the example placeholder)
```

---

## Running the Agent

### Step 1: Verify Prerequisites

Before starting, ensure:

```bash
# 1. Virtual environment is activated
which python  # Should show venv/bin/python

# 2. MongoDB is running
# For Homebrew:
brew services list | grep mongodb

# For systemd:
sudo systemctl status mongod

# For Docker:
docker ps | grep mongodb

# 3. Environment is configured
cat .env | grep ANTHROPIC_API_KEY
```

### Step 2: Start the Application

```bash
# Start the NASDAQ Stock Agent
python main.py
```

**Expected Output:**
```
2024-11-12 10:30:00 - root - INFO - Starting NASDAQ Stock Agent v1.0.0
2024-11-12 10:30:00 - root - INFO - Loading configuration...
2024-11-12 10:30:01 - src.services.database - INFO - MongoDB connected successfully
2024-11-12 10:30:01 - src.services.database - INFO - Database initialized successfully
2024-11-12 10:30:01 - src.core.dependencies - INFO - MCP server initialized successfully
2024-11-12 10:30:01 - src.a2a.handler - INFO - A2A handler initialized successfully
2024-11-12 10:30:01 - root - INFO - NEST integration is disabled - running in standalone mode
2024-11-12 10:30:01 - root - INFO - All services initialized successfully
2024-11-12 10:30:01 - root - INFO - Starting server on 0.0.0.0:8000 (debug=False)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 3: Verify the Agent is Running

Open a new terminal and run:

```bash
# Basic health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"NASDAQ Stock Agent","version":"1.0.0","timestamp":"2024-11-12T10:30:00Z"}
```

---

## Testing the Agent

### 1. Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check with service status
curl http://localhost:8000/health/detailed

# System status with metrics
curl http://localhost:8000/status

# MCP server status
curl http://localhost:8000/mcp
```

### 2. Interactive API Documentation

Open your web browser and visit:

```
http://localhost:8000/docs
```

This provides an interactive Swagger UI where you can:
- View all available endpoints
- Test API calls directly from the browser
- See request/response schemas
- Try different stock analysis queries

### 3. Stock Analysis Examples

#### Example 1: Basic Stock Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I buy Apple stock?"
  }'
```

#### Example 2: Specific Ticker Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze TSLA stock performance"
  }'
```

#### Example 3: Comparative Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare AAPL and MSFT for investment"
  }'
```

### 4. A2A Protocol Testing

```bash
# Get A2A manifest
curl http://localhost:8000/a2a/manifest

# Send A2A message
curl -X POST http://localhost:8000/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": {
      "text": "What is the outlook for NVDA?",
      "type": "text"
    },
    "conversation_id": "test-conv-123"
  }'
```

### 5. Verify Logging

```bash
# Check recent analyses
curl http://localhost:8000/api/v1/logs/analyses?limit=10

# Check error logs
curl http://localhost:8000/api/v1/logs/errors?limit=10

# Get logging statistics
curl http://localhost:8000/api/v1/logs/stats
```

---

## NEST Integration (Optional)

NEST (NANDA Sandbox and Testbed) enables agent-to-agent communication. This is optional and only needed if you want your agent to communicate with other agents in a NANDA network.

### Prerequisites for NEST

1. **python-a2a package** (optional dependency)
   ```bash
   pip install python-a2a
   ```

2. **NANDA Registry** (if using agent discovery)
   - You need access to a NANDA registry service
   - Get the registry URL from your network administrator

### Enabling NEST Integration

Edit your `.env` file and add:

```bash
# Enable NEST integration
NEST_ENABLED=true

# Agent identification
NEST_AGENT_ID=nasdaq-stock-agent
NEST_AGENT_NAME=NASDAQ Stock Agent

# Network configuration
NEST_PORT=6000
NEST_PUBLIC_URL=https://your-domain.com:6000

# Registry configuration (optional)
NEST_REGISTRY_URL=http://registry.example.com:6900

# Agent capabilities
NEST_DOMAIN=financial analysis
NEST_SPECIALIZATION=NASDAQ stock analysis and investment recommendations
NEST_CAPABILITIES=stock_analysis,technical_analysis,fundamental_analysis,investment_recommendations,market_data

# Optional settings
NEST_TELEMETRY=true
NEST_DUAL_MODE=false
```

### Starting with NEST

```bash
# Start the agent (NEST will auto-initialize if enabled)
python main.py
```

**Expected Output with NEST:**
```
2024-11-12 10:30:01 - root - INFO - NEST integration is enabled - initializing NEST adapter
2024-11-12 10:30:01 - src.nest.adapter - INFO - Initialized StockAgentNEST adapter for 'nasdaq-stock-agent'
2024-11-12 10:30:02 - src.nest.registry - INFO - Registering agent 'nasdaq-stock-agent' with registry
2024-11-12 10:30:02 - src.nest.registry - INFO - Successfully registered agent 'nasdaq-stock-agent'
2024-11-12 10:30:02 - src.nest.adapter - INFO - NEST agent 'nasdaq-stock-agent' started successfully
```

### Testing NEST Integration

```bash
# Check NEST status
curl http://localhost:8000/nest

# Expected response includes:
# - agent_id
# - status (running/stopped)
# - registry information
# - metrics (messages, registry operations, performance)
```

### NEST Monitoring

```bash
# Get NEST metrics
curl http://localhost:8000/nest | jq '.nest_status.metrics'

# View NEST message logs
curl http://localhost:8000/api/v1/logs/errors?error_type=NEST_MESSAGE_LOG

# View registry operation logs
curl http://localhost:8000/api/v1/logs/errors?error_type=NEST_REGISTRY_LOG
```

For more details, see:
- [NEST Integration Guide](docs/NEST_INTEGRATION.md)
- [NEST Monitoring Documentation](docs/NEST_MONITORING.md)
- [NEST Launcher Documentation](docs/NEST_LAUNCHER.md)

---

## Monitoring and Logging

### Real-Time Monitoring

#### 1. Application Logs

The agent logs to stdout by default. To save logs to a file:

```bash
# Run with log file
python main.py 2>&1 | tee nasdaq-agent.log

# Or redirect to file only
python main.py > nasdaq-agent.log 2>&1
```

#### 2. System Metrics

```bash
# Get comprehensive system status
curl http://localhost:8000/status | jq

# Get performance metrics
curl http://localhost:8000/metrics | jq

# Get logging statistics
curl http://localhost:8000/api/v1/logs/stats | jq
```

#### 3. Database Monitoring

```bash
# Connect to MongoDB
mongosh nasdaq_stock_agent

# Check collections
show collections

# Count analyses
db.analyses.countDocuments()

# View recent analyses
db.analyses.find().sort({timestamp: -1}).limit(5)

# Check errors
db.errors.find().sort({timestamp: -1}).limit(5)
```

### Log Retention

Logs are automatically cleaned up after 30 days (configurable via `LOG_RETENTION_DAYS` in `.env`).

### Monitoring Dashboard

For production deployments, consider setting up:
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **ELK Stack** for log aggregation
- **MongoDB Compass** for database monitoring

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Anthropic API key not configured"

**Symptoms:**
```
ERROR - Anthropic API key not configured
```

**Solution:**
```bash
# 1. Check .env file exists
ls -la .env

# 2. Verify API key is set
cat .env | grep ANTHROPIC_API_KEY

# 3. Ensure it's not the placeholder
# Should be: ANTHROPIC_API_KEY=sk-ant-api03-...
# Not: ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 4. Restart the application
python main.py
```

#### Issue 2: "MongoDB connection failed"

**Symptoms:**
```
ERROR - Failed to connect to MongoDB
```

**Solution:**
```bash
# Check if MongoDB is running
# For Homebrew:
brew services list | grep mongodb
brew services start mongodb-community

# For systemd:
sudo systemctl status mongod
sudo systemctl start mongod

# For Docker:
docker ps | grep mongodb
docker start mongodb

# Test connection manually
mongosh --eval "db.adminCommand('ping')"
```

#### Issue 3: "Port 8000 already in use"

**Symptoms:**
```
ERROR - [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
echo "PORT=8001" >> .env

# Restart application
python main.py
```

#### Issue 4: "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

#### Issue 5: "No running event loop"

**Symptoms:**
```
RuntimeError: no running event loop
```

**Solution:**
This has been fixed in the code. If you still see this:
```bash
# Pull latest code
git pull

# Or ensure you have the latest version of logging_service.py
```

#### Issue 6: NEST Integration Fails

**Symptoms:**
```
WARNING - NEST integration requires python-a2a package
```

**Solution:**
```bash
# Install python-a2a
pip install python-a2a

# Or disable NEST in .env
echo "NEST_ENABLED=false" >> .env

# Restart application
python main.py
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look for ERROR or WARNING messages
2. **Review documentation**: See `docs/` directory for detailed guides
3. **Check system status**: `curl http://localhost:8000/status`
4. **Verify configuration**: Ensure `.env` is properly configured
5. **Check dependencies**: `pip list` to verify all packages are installed

---

## Stopping the Agent

### Graceful Shutdown

To stop the agent gracefully:

```bash
# In the terminal where the agent is running, press:
CTRL+C

# Expected output:
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [12345]
```

### Force Stop

If the agent doesn't stop gracefully:

```bash
# Find the process
ps aux | grep "python main.py"

# Kill the process
kill -9 <PID>
```

### Cleanup

After stopping:

```bash
# Deactivate virtual environment
deactivate

# Optional: Stop MongoDB if not needed
brew services stop mongodb-community  # macOS
sudo systemctl stop mongod            # Linux
docker stop mongodb                   # Docker
```

---

## Production Deployment

For production deployments, consider:

### 1. Use a Process Manager

```bash
# Install supervisor or systemd service
# Example systemd service file:
sudo nano /etc/systemd/system/nasdaq-agent.service
```

```ini
[Unit]
Description=NASDAQ Stock Agent
After=network.target mongodb.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/nasdaq-stock-agent
Environment="PATH=/path/to/nasdaq-stock-agent/venv/bin"
ExecStart=/path/to/nasdaq-stock-agent/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable nasdaq-agent
sudo systemctl start nasdaq-agent
sudo systemctl status nasdaq-agent
```

### 2. Use a Reverse Proxy

```bash
# Install nginx
sudo apt-get install nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/nasdaq-agent
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Enable HTTPS

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 4. Set Up Monitoring

- Configure log aggregation (ELK, Splunk, etc.)
- Set up metrics collection (Prometheus, Datadog, etc.)
- Configure alerting for errors and downtime
- Monitor database performance

### 5. Security Hardening

- Use environment-specific API keys
- Enable rate limiting
- Set up firewall rules
- Use MongoDB authentication
- Keep dependencies updated
- Regular security audits

---

## Quick Reference

### Essential Commands

```bash
# Start agent
python main.py

# Health check
curl http://localhost:8000/health

# Analyze stock
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I buy AAPL?"}'

# View API docs
open http://localhost:8000/docs

# Check logs
tail -f nasdaq-agent.log

# Stop agent
CTRL+C
```

### Important URLs

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/status
- **NEST Status**: http://localhost:8000/nest
- **A2A Manifest**: http://localhost:8000/a2a/manifest

### Configuration Files

- **Environment**: `.env`
- **Requirements**: `requirements.txt`
- **Main Entry**: `main.py`
- **API Routes**: `src/api/routers/`
- **Services**: `src/services/`
- **NEST Config**: `src/nest/config.py`

### Documentation

- **Quick Start**: `QUICKSTART.md`
- **NEST Integration**: `docs/NEST_INTEGRATION.md`
- **NEST Monitoring**: `docs/NEST_MONITORING.md`
- **A2A Protocol**: `docs/A2A_OUTGOING_COMMUNICATION.md`
- **Installation**: `docs/MACOS_INSTALLATION.md`

---

## Summary Checklist

Before running the agent, ensure:

- [ ] Python 3.9+ installed
- [ ] MongoDB installed and running
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with valid `ANTHROPIC_API_KEY`
- [ ] MongoDB connection configured in `.env`
- [ ] Port 8000 is available (or configured differently)

To start:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start MongoDB (if not running)
brew services start mongodb-community

# 3. Run the agent
python main.py

# 4. Test in another terminal
curl http://localhost:8000/health
```

**You're ready to analyze stocks with AI!** 🚀📈

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or check the documentation in the `docs/` directory.
