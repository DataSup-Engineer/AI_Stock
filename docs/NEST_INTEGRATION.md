# NEST Integration Guide

## Overview

The NASDAQ Stock Agent now supports integration with the NEST (NANDA Sandbox and Testbed) framework, enabling agent-to-agent (A2A) communication while maintaining full backward compatibility with the existing FastAPI endpoints.

## Features

- **Dual-Mode Operation**: Run both FastAPI and A2A servers simultaneously
- **Automatic Initialization**: NEST integration starts automatically when enabled
- **Graceful Fallback**: Falls back to standalone mode if NEST is disabled or configuration is invalid
- **Health Monitoring**: NEST status included in health check endpoints
- **Registry Integration**: Automatic registration with NANDA agent registry

## Configuration

### Environment Variables

Configure NEST integration using the following environment variables:

```bash
# Enable NEST integration (default: false)
NEST_ENABLED=true

# Agent identity
NEST_AGENT_ID=nasdaq-stock-agent
NEST_AGENT_NAME="NASDAQ Stock Agent"

# Network configuration
NEST_PORT=6000
NEST_PUBLIC_URL=https://your-domain.com:6000
NEST_REGISTRY_URL=http://registry.example.com:6900

# Optional settings
NEST_TELEMETRY=true
NEST_DUAL_MODE=true
```

### Running Modes

#### 1. Standalone Mode (Default)

Run only the FastAPI server without NEST integration:

```bash
python main.py
```

The agent will run on port 8000 (or configured port) with all existing functionality.

#### 2. NEST Mode with FastAPI

Enable NEST integration alongside FastAPI:

```bash
export NEST_ENABLED=true
export NEST_PORT=6000
python main.py
```

This starts:
- FastAPI server on port 8000
- A2A server on port 6000

#### 3. Using the Launcher

For more control, use the dedicated launcher:

```bash
# Standalone mode
python -m src.nest.launcher

# NEST mode only
NEST_ENABLED=true python -m src.nest.launcher

# Dual mode (both servers)
NEST_ENABLED=true NEST_DUAL_MODE=true python -m src.nest.launcher
```

## Health Check Endpoints

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Returns basic health status.

### System Status (includes NEST)

```bash
curl http://localhost:8000/status
```

Returns comprehensive system status including NEST integration status:

```json
{
  "service": "NASDAQ Stock Agent",
  "version": "1.0.0",
  "status": "operational",
  "service_health": {
    "nest_integration": {
      "agent_id": "nasdaq-stock-agent",
      "status": "running",
      "port": 6000,
      "public_url": "http://localhost:6000",
      "registry": {
        "configured": true,
        "registered": true,
        "url": "http://registry.example.com:6900"
      }
    }
  }
}
```

### NEST-Specific Status

```bash
curl http://localhost:8000/nest
```

Returns detailed NEST integration status:

```json
{
  "success": true,
  "nest_status": {
    "agent_id": "nasdaq-stock-agent",
    "status": "running",
    "port": 6000,
    "public_url": "http://localhost:6000",
    "bridge_health": {
      "status": "healthy",
      "analysis_service": "operational"
    },
    "registry": {
      "configured": true,
      "registered": true,
      "url": "http://registry.example.com:6900"
    }
  }
}
```

## A2A Communication

### Sending Messages to the Stock Agent

Other agents can send A2A messages to request stock analysis:

```json
{
  "role": "user",
  "content": {
    "text": "What's the analysis for AAPL?",
    "type": "text"
  },
  "conversation_id": "conv-123"
}
```

### Response Format

The agent responds with formatted stock analysis:

```json
{
  "role": "agent",
  "content": {
    "text": "[nasdaq-stock-agent] Apple Inc. (AAPL) Analysis:\n\nCurrent Price: $175.50 (+2.3%)\nTechnical: Price above 20-day MA (bullish)\nValuation: Fairly Valued\nAI Recommendation: BUY (Confidence: 75%)",
    "type": "text"
  },
  "conversation_id": "conv-123"
}
```

## Troubleshooting

### NEST Integration Not Starting

If NEST integration fails to start, check:

1. **Environment Variable**: Ensure `NEST_ENABLED=true` is set
2. **Dependencies**: Install python-a2a package: `pip install python-a2a`
3. **Configuration**: Verify all required environment variables are set
4. **Logs**: Check application logs for error messages

The agent will automatically fall back to standalone mode if NEST initialization fails.

### NEST Status Shows "disabled"

This is normal if:
- `NEST_ENABLED` is not set or set to `false`
- Configuration validation failed
- python-a2a package is not installed

The agent will continue to work in standalone mode.

### Registry Registration Failed

If registry registration fails:
- Verify `NEST_REGISTRY_URL` is correct and accessible
- Check network connectivity to the registry
- Review registry logs for errors

The agent will continue to operate without registry integration.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   NASDAQ Stock Agent                         │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │  FastAPI App   │         │  NEST Adapter    │           │
│  │  (Port 8000)   │         │  (Port 6000)     │           │
│  │                │         │                  │           │
│  │  /analyze      │         │  A2A Bridge      │           │
│  │  /health       │         │  Registry Client │           │
│  │  /status       │         │                  │           │
│  └────────────────┘         └──────────────────┘           │
│         │                            │                      │
│         └────────────┬───────────────┘                      │
│                      │                                      │
│         ┌────────────▼────────────┐                        │
│         │  Analysis Service       │                        │
│         │  (Shared Core Logic)    │                        │
│         └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Lifecycle Management

1. **Startup**:
   - Load NEST configuration from environment
   - Validate configuration
   - Initialize NEST adapter if enabled
   - Register with NANDA registry
   - Start A2A server

2. **Runtime**:
   - Process A2A messages
   - Send periodic heartbeats to registry
   - Handle both HTTP and A2A requests

3. **Shutdown**:
   - Deregister from registry
   - Stop A2A server
   - Clean up resources
   - Shutdown FastAPI server

## Best Practices

1. **Always set NEST_PUBLIC_URL** in production to ensure the agent is accessible
2. **Monitor health endpoints** to verify NEST integration status
3. **Use dual mode** for maximum flexibility in production
4. **Configure registry URL** for agent discovery
5. **Enable telemetry** for monitoring and debugging

## Example Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  nasdaq-stock-agent:
    build: .
    ports:
      - "8000:8000"  # FastAPI
      - "6000:6000"  # A2A
    environment:
      - NEST_ENABLED=true
      - NEST_AGENT_ID=nasdaq-stock-agent
      - NEST_PORT=6000
      - NEST_PUBLIC_URL=https://stock-agent.example.com:6000
      - NEST_REGISTRY_URL=http://registry:6900
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MONGODB_URI=${MONGODB_URI}
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nasdaq-stock-agent
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: agent
        image: nasdaq-stock-agent:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 6000
          name: a2a
        env:
        - name: NEST_ENABLED
          value: "true"
        - name: NEST_PORT
          value: "6000"
        - name: NEST_REGISTRY_URL
          value: "http://registry-service:6900"
```

## See Also

- [NEST Launcher Documentation](./NEST_LAUNCHER.md)
- [A2A Protocol Documentation](./A2A_PROTOCOL.md)
- [Agent Protocols Overview](./AGENT_PROTOCOLS.md)
