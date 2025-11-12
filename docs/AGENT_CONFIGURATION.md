# Agent Configuration for Agent-to-Agent Communication

This document describes the complete agent configuration that enables other agents to discover and communicate with the NASDAQ Stock Agent using the `@agent_name` syntax.

## Overview

The NASDAQ Stock Agent exposes a comprehensive configuration that includes all necessary information for agent-to-agent (A2A) communication. This configuration is accessible via the `/nest/config` endpoint and is automatically registered with the NANDA registry when NEST integration is enabled.

## Complete Agent Configuration

The agent configuration includes the following fields:

```json
{
  "agent_id": "nasdaq-stock-agent",
  "agent_name": "NASDAQ Stock Agent",
  "domain": "financial analysis",
  "specialization": "NASDAQ stock analysis and investment recommendations",
  "description": "AI-powered stock analysis agent providing comprehensive investment analysis for NASDAQ stocks",
  "expertise": [
    "NASDAQ stock analysis",
    "Technical indicators (RSI, MACD, Moving Averages)",
    "Fundamental analysis (P/E, EPS, Revenue)",
    "Market sentiment analysis",
    "Investment recommendations (BUY, SELL, HOLD)",
    "Risk assessment",
    "Portfolio optimization"
  ],
  "registry_url": "http://registry.example.com:6900",
  "mcp_registry_url": "http://mcp-registry.example.com:6901",
  "public_url": "https://stock-agent.example.com:6000",
  "system_prompt": "You are an expert NASDAQ stock analysis agent...",
  "anthropic_api_key": "sk-ant-api03-...",
  "model": "claude-3-sonnet-20240229",
  "capabilities": [
    "stock_analysis",
    "technical_analysis",
    "fundamental_analysis",
    "investment_recommendations",
    "market_data"
  ],
  "version": "1.0.0",
  "status": "healthy",
  "port": 6000
}
```

## Configuration Fields

### Core Identity

#### `agent_id` (string, required)
- **Description**: Unique identifier for the agent
- **Default**: `"nasdaq-stock-agent"`
- **Environment Variable**: `NEST_AGENT_ID`
- **Usage**: Used for agent discovery and routing messages

#### `agent_name` (string, required)
- **Description**: Human-readable display name for the agent
- **Default**: `"NASDAQ Stock Agent"`
- **Environment Variable**: `NEST_AGENT_NAME`
- **Usage**: Used in `@agent_name` syntax for agent mentions

#### `domain` (string, required)
- **Description**: Primary domain of expertise
- **Default**: `"financial analysis"`
- **Environment Variable**: `NEST_DOMAIN`
- **Usage**: Helps other agents understand the agent's area of expertise

#### `specialization` (string, required)
- **Description**: Specific area of specialization within the domain
- **Default**: `"NASDAQ stock analysis and investment recommendations"`
- **Environment Variable**: `NEST_SPECIALIZATION`
- **Usage**: Provides detailed information about what the agent does

#### `description` (string, required)
- **Description**: Comprehensive description of the agent's purpose and capabilities
- **Default**: `"AI-powered stock analysis agent providing comprehensive investment analysis for NASDAQ stocks"`
- **Environment Variable**: `NEST_DESCRIPTION`
- **Usage**: Displayed in agent directories and discovery interfaces

### Expertise

#### `expertise` (array of strings, required)
- **Description**: List of specific areas of expertise
- **Default**: 
  ```json
  [
    "NASDAQ stock analysis",
    "Technical indicators (RSI, MACD, Moving Averages)",
    "Fundamental analysis (P/E, EPS, Revenue)",
    "Market sentiment analysis",
    "Investment recommendations (BUY, SELL, HOLD)",
    "Risk assessment",
    "Portfolio optimization"
  ]
  ```
- **Environment Variable**: `NEST_EXPERTISE` (comma-separated)
- **Usage**: Helps other agents understand specific capabilities

### Network Configuration

#### `registry_url` (string, optional)
- **Description**: URL of the NANDA agent registry
- **Default**: `null`
- **Environment Variable**: `NEST_REGISTRY_URL`
- **Usage**: Used for agent registration and discovery

#### `mcp_registry_url` (string, optional)
- **Description**: URL of the MCP (Model Context Protocol) registry
- **Default**: `null`
- **Environment Variable**: `NEST_MCP_REGISTRY_URL`
- **Usage**: Used for MCP-based agent discovery

#### `public_url` (string, required for external access)
- **Description**: Public URL where the agent can be reached
- **Default**: `"http://localhost:6000"`
- **Environment Variable**: `NEST_PUBLIC_URL`
- **Usage**: Used by other agents to send A2A messages

#### `port` (integer, required)
- **Description**: Port number for A2A communication
- **Default**: `6000`
- **Environment Variable**: `NEST_PORT`
- **Usage**: Network port for the A2A server

### AI Model Configuration

#### `anthropic_api_key` (string, required)
- **Description**: Anthropic API key for Claude AI model
- **Default**: `null`
- **Environment Variable**: `ANTHROPIC_API_KEY`
- **Usage**: Authentication for AI model access
- **Security**: Excluded from public agent configuration endpoint

#### `model` (string, required)
- **Description**: AI model identifier
- **Default**: `"claude-3-sonnet-20240229"`
- **Environment Variable**: `ANTHROPIC_MODEL`
- **Usage**: Specifies which AI model the agent uses

#### `system_prompt` (string, required)
- **Description**: System prompt that defines the agent's behavior
- **Default**: 
  ```
  You are an expert NASDAQ stock analysis agent. Your role is to provide 
  comprehensive, data-driven investment analysis and recommendations for 
  NASDAQ-listed stocks. You analyze technical indicators, fundamental metrics, 
  market trends, and sentiment to deliver actionable insights. Always provide 
  clear reasoning for your recommendations and consider both opportunities and 
  risks. When communicating with other agents, be concise and focus on key 
  insights relevant to their queries.
  ```
- **Environment Variable**: `NEST_SYSTEM_PROMPT`
- **Usage**: Defines how the agent responds to queries

### Capabilities

#### `capabilities` (array of strings, required)
- **Description**: List of functional capabilities
- **Default**: 
  ```json
  [
    "stock_analysis",
    "technical_analysis",
    "fundamental_analysis",
    "investment_recommendations",
    "market_data"
  ]
  ```
- **Environment Variable**: `NEST_CAPABILITIES` (comma-separated)
- **Usage**: Used for capability-based agent discovery

### Metadata

#### `version` (string, required)
- **Description**: Agent version number
- **Default**: `"1.0.0"`
- **Environment Variable**: `NEST_VERSION`
- **Usage**: Version tracking and compatibility checking

#### `status` (string, read-only)
- **Description**: Current operational status
- **Values**: `"healthy"`, `"degraded"`, `"unhealthy"`, `"stopped"`
- **Usage**: Health monitoring and availability checking

## Accessing Agent Configuration

### Via API Endpoint

```bash
# Get full agent configuration
curl http://localhost:8000/nest/config

# Response:
{
  "success": true,
  "agent_config": {
    "agent_id": "nasdaq-stock-agent",
    "agent_name": "NASDAQ Stock Agent",
    "domain": "financial analysis",
    "specialization": "NASDAQ stock analysis and investment recommendations",
    "description": "AI-powered stock analysis agent...",
    "expertise": [...],
    "public_url": "https://stock-agent.example.com:6000",
    "capabilities": [...],
    "model": "claude-3-sonnet-20240229",
    "version": "1.0.0"
  },
  "timestamp": "2024-11-12T10:30:00Z"
}
```

### Via Python Code

```python
from main import get_nest_adapter

# Get NEST adapter
nest_adapter = get_nest_adapter()

if nest_adapter:
    # Get full configuration (includes API key)
    full_config = nest_adapter.get_agent_config()
    
    # Get public configuration (excludes API key)
    public_config = nest_adapter.config.get_agent_config_for_communication()
```

### Via Registry

When NEST integration is enabled and a registry URL is configured, the agent automatically registers its configuration with the NANDA registry. Other agents can then discover this agent by:

1. **Agent ID lookup**: `GET /agents/nasdaq-stock-agent`
2. **Capability search**: `GET /agents?capability=stock_analysis`
3. **Domain search**: `GET /agents?domain=financial%20analysis`

## Using @agent_name Syntax

Other agents can communicate with this agent using the `@agent_name` syntax:

### Example 1: Direct Mention

```json
{
  "role": "user",
  "content": {
    "text": "@NASDAQ Stock Agent What's your analysis of AAPL?",
    "type": "text"
  },
  "conversation_id": "conv-123"
}
```

The message will be automatically routed to the NASDAQ Stock Agent based on the `agent_name` field in the configuration.

### Example 2: Agent Discovery

```python
# Other agent discovers NASDAQ Stock Agent
from src.nest.registry import RegistryClient

registry = RegistryClient(
    registry_url="http://registry.example.com:6900",
    agent_id="requesting-agent"
)

# Look up by agent_id
agent_url = await registry.lookup_agent("nasdaq-stock-agent")

# Get full agent info
agent_info = await registry.get_agent_info("nasdaq-stock-agent")
print(agent_info["agent_name"])  # "NASDAQ Stock Agent"
print(agent_info["capabilities"])  # ["stock_analysis", ...]
```

### Example 3: Capability-Based Discovery

```python
# Find agents with stock_analysis capability
agents = await registry.list_agents(capability="stock_analysis")

for agent in agents:
    if agent["agent_id"] == "nasdaq-stock-agent":
        print(f"Found: {agent['agent_name']}")
        print(f"Specialization: {agent['specialization']}")
        print(f"URL: {agent['public_url']}")
```

## Configuration Best Practices

### 1. Use Descriptive Names

Choose clear, descriptive values for `agent_name` and `specialization` that help other agents understand what your agent does:

```bash
NEST_AGENT_NAME="NASDAQ Stock Analysis Expert"
NEST_SPECIALIZATION="Real-time NASDAQ stock analysis with AI-powered recommendations"
```

### 2. Define Comprehensive Expertise

List all specific areas of expertise to help other agents understand when to consult your agent:

```bash
NEST_EXPERTISE="NASDAQ stock analysis,Technical indicators (RSI MACD Moving Averages),Fundamental analysis (P/E EPS Revenue),Market sentiment analysis,Investment recommendations (BUY SELL HOLD),Risk assessment,Portfolio optimization"
```

### 3. Set Accurate Capabilities

Ensure capabilities accurately reflect what your agent can do:

```bash
NEST_CAPABILITIES="stock_analysis,technical_analysis,fundamental_analysis,investment_recommendations,market_data,risk_assessment"
```

### 4. Provide a Clear System Prompt

Write a system prompt that clearly defines your agent's behavior and communication style:

```bash
NEST_SYSTEM_PROMPT="You are an expert NASDAQ stock analysis agent. Provide data-driven analysis with clear reasoning. When communicating with other agents, be concise and focus on actionable insights."
```

### 5. Use Production URLs

For production deployments, always use HTTPS and proper domain names:

```bash
NEST_PUBLIC_URL="https://nasdaq-agent.yourcompany.com:6000"
NEST_REGISTRY_URL="https://registry.yourcompany.com:6900"
```

### 6. Secure API Keys

Never expose API keys in public endpoints. The `/nest/config` endpoint automatically excludes sensitive information:

```python
# Full config (internal use only)
full_config = nest_adapter.get_agent_config()
# Includes: anthropic_api_key

# Public config (safe for sharing)
public_config = nest_adapter.config.get_agent_config_for_communication()
# Excludes: anthropic_api_key
```

## Environment Variable Reference

Complete list of environment variables for agent configuration:

```bash
# Core Identity
NEST_AGENT_ID=nasdaq-stock-agent
NEST_AGENT_NAME=NASDAQ Stock Agent
NEST_DOMAIN=financial analysis
NEST_SPECIALIZATION=NASDAQ stock analysis and investment recommendations
NEST_DESCRIPTION=AI-powered stock analysis agent providing comprehensive investment analysis

# Expertise (comma-separated)
NEST_EXPERTISE=NASDAQ stock analysis,Technical indicators,Fundamental analysis,Market sentiment,Investment recommendations,Risk assessment,Portfolio optimization

# Network Configuration
NEST_PORT=6000
NEST_PUBLIC_URL=https://stock-agent.example.com:6000
NEST_REGISTRY_URL=http://registry.example.com:6900
NEST_MCP_REGISTRY_URL=http://mcp-registry.example.com:6901

# Capabilities (comma-separated)
NEST_CAPABILITIES=stock_analysis,technical_analysis,fundamental_analysis,investment_recommendations,market_data

# AI Model Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
NEST_SYSTEM_PROMPT=You are an expert NASDAQ stock analysis agent...

# Metadata
NEST_VERSION=1.0.0

# Feature Flags
NEST_ENABLED=true
NEST_TELEMETRY=true
NEST_DUAL_MODE=false
```

## Testing Agent Configuration

### 1. Verify Configuration Loading

```bash
# Start the agent
python main.py

# Check configuration
curl http://localhost:8000/nest/config | jq
```

### 2. Test Agent Discovery

```bash
# Register with registry (automatic on startup if NEST_REGISTRY_URL is set)
# Then query registry
curl http://registry.example.com:6900/agents/nasdaq-stock-agent | jq
```

### 3. Test @agent_name Communication

```bash
# Send message with @agent_name mention
curl -X POST http://localhost:8000/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": {
      "text": "@NASDAQ Stock Agent analyze AAPL",
      "type": "text"
    },
    "conversation_id": "test-123"
  }'
```

## Troubleshooting

### Configuration Not Loading

**Problem**: Agent configuration is not being loaded from environment variables.

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Check environment variables are set
env | grep NEST_

# Restart the application
python main.py
```

### Agent Not Discoverable

**Problem**: Other agents cannot find this agent in the registry.

**Solution**:
```bash
# Verify NEST is enabled
cat .env | grep NEST_ENABLED

# Check registry URL is set
cat .env | grep NEST_REGISTRY_URL

# Verify agent is registered
curl http://registry.example.com:6900/agents/nasdaq-stock-agent
```

### @agent_name Not Working

**Problem**: Messages with `@agent_name` are not being routed correctly.

**Solution**:
```bash
# Verify agent_name is set correctly
curl http://localhost:8000/nest/config | jq '.agent_config.agent_name'

# Check registry has correct agent_name
curl http://registry.example.com:6900/agents/nasdaq-stock-agent | jq '.agent_name'

# Ensure name matches exactly (case-sensitive)
```

## Related Documentation

- [NEST Integration Guide](./NEST_INTEGRATION.md)
- [NEST Monitoring](./NEST_MONITORING.md)
- [A2A Communication](./A2A_OUTGOING_COMMUNICATION.md)
- [Run Instructions](../RUN_INSTRUCTIONS.md)

## Summary

The NASDAQ Stock Agent provides a comprehensive configuration that enables seamless agent-to-agent communication. By properly configuring the agent identity, expertise, capabilities, and network settings, other agents can easily discover and communicate with this agent using the `@agent_name` syntax. The configuration is accessible via the `/nest/config` endpoint and is automatically registered with the NANDA registry when NEST integration is enabled.
