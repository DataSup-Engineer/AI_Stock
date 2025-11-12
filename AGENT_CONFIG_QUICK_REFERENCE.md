# Agent Configuration Quick Reference

This is a quick reference guide for configuring the NASDAQ Stock Agent for agent-to-agent communication.

## Essential Configuration

Add these to your `.env` file to enable full agent-to-agent communication:

```bash
# Enable NEST Integration
NEST_ENABLED=true

# Agent Identity (Required for @agent_name syntax)
NEST_AGENT_ID=nasdaq-stock-agent
NEST_AGENT_NAME=NASDAQ Stock Agent

# Network Configuration (Required for external access)
NEST_PORT=6000
NEST_PUBLIC_URL=https://your-domain.com:6000

# Registry Configuration (Required for agent discovery)
NEST_REGISTRY_URL=http://registry.example.com:6900

# AI Model Configuration (Required)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

## Complete Configuration Template

Copy this template to your `.env` file and customize:

```bash
# ============================================
# NEST Agent Configuration
# ============================================

# Enable NEST Integration
NEST_ENABLED=true

# Agent Identity
NEST_AGENT_ID=nasdaq-stock-agent
NEST_AGENT_NAME=NASDAQ Stock Agent
NEST_DOMAIN=financial analysis
NEST_SPECIALIZATION=NASDAQ stock analysis and investment recommendations
NEST_VERSION=1.0.0

# Agent Description
NEST_DESCRIPTION=AI-powered stock analysis agent providing comprehensive investment analysis for NASDAQ stocks

# Agent Expertise (comma-separated)
NEST_EXPERTISE=NASDAQ stock analysis,Technical indicators (RSI MACD Moving Averages),Fundamental analysis (P/E EPS Revenue),Market sentiment analysis,Investment recommendations (BUY SELL HOLD),Risk assessment,Portfolio optimization

# Agent Capabilities (comma-separated)
NEST_CAPABILITIES=stock_analysis,technical_analysis,fundamental_analysis,investment_recommendations,market_data

# Network Configuration
NEST_PORT=6000
NEST_PUBLIC_URL=https://nasdaq-agent.yourcompany.com:6000
NEST_REGISTRY_URL=https://registry.yourcompany.com:6900
NEST_MCP_REGISTRY_URL=https://mcp-registry.yourcompany.com:6901

# AI Model Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# System Prompt (optional - uses default if not set)
NEST_SYSTEM_PROMPT=You are an expert NASDAQ stock analysis agent. Your role is to provide comprehensive, data-driven investment analysis and recommendations for NASDAQ-listed stocks. You analyze technical indicators, fundamental metrics, market trends, and sentiment to deliver actionable insights. Always provide clear reasoning for your recommendations and consider both opportunities and risks. When communicating with other agents, be concise and focus on key insights relevant to their queries.

# Feature Flags
NEST_TELEMETRY=true
NEST_DUAL_MODE=false
```

## Accessing Agent Configuration

### Via API

```bash
# Get agent configuration
curl http://localhost:8000/nest/config

# Get agent status (includes configuration)
curl http://localhost:8000/nest
```

### Via Python

```python
from main import get_nest_adapter

nest_adapter = get_nest_adapter()
if nest_adapter:
    # Get full configuration
    config = nest_adapter.get_agent_config()
    print(f"Agent: {config['agent_name']}")
    print(f"Capabilities: {config['capabilities']}")
```

## Agent Communication Examples

### Example 1: Another Agent Mentions This Agent

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

### Example 2: This Agent Forwards to Another Agent

```json
{
  "role": "user",
  "content": {
    "text": "@financial-advisor Based on my analysis, AAPL shows strong fundamentals. What's your recommendation?",
    "type": "text"
  },
  "conversation_id": "conv-123"
}
```

### Example 3: Agent Discovery

```bash
# Find this agent by capability
curl "http://registry.example.com:6900/agents?capability=stock_analysis"

# Get this agent's details
curl "http://registry.example.com:6900/agents/nasdaq-stock-agent"
```

## Configuration Fields Reference

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `agent_id` | Yes | nasdaq-stock-agent | Unique identifier |
| `agent_name` | Yes | NASDAQ Stock Agent | Display name for @mentions |
| `domain` | Yes | financial analysis | Primary domain |
| `specialization` | Yes | NASDAQ stock analysis... | Specific expertise |
| `description` | Yes | AI-powered stock... | Full description |
| `expertise` | Yes | [7 items] | List of expertise areas |
| `capabilities` | Yes | [5 items] | Functional capabilities |
| `public_url` | Yes* | http://localhost:6000 | Public endpoint URL |
| `registry_url` | No | null | NANDA registry URL |
| `mcp_registry_url` | No | null | MCP registry URL |
| `anthropic_api_key` | Yes | null | Anthropic API key |
| `model` | Yes | claude-3-sonnet-20240229 | AI model |
| `system_prompt` | Yes | [default prompt] | Agent behavior prompt |
| `port` | Yes | 6000 | A2A server port |
| `version` | Yes | 1.0.0 | Agent version |

\* Required for external access

## Quick Start

1. **Copy configuration template** to `.env`
2. **Set your API key**: `ANTHROPIC_API_KEY=sk-ant-...`
3. **Enable NEST**: `NEST_ENABLED=true`
4. **Set public URL**: `NEST_PUBLIC_URL=https://your-domain.com:6000`
5. **Set registry URL**: `NEST_REGISTRY_URL=http://registry:6900`
6. **Start the agent**: `python main.py`
7. **Verify configuration**: `curl http://localhost:8000/nest/config`

## Verification Checklist

- [ ] NEST_ENABLED=true
- [ ] ANTHROPIC_API_KEY is set (not the placeholder)
- [ ] NEST_AGENT_NAME is descriptive
- [ ] NEST_PUBLIC_URL is accessible from other agents
- [ ] NEST_REGISTRY_URL points to a valid registry
- [ ] Agent starts without errors
- [ ] `/nest/config` endpoint returns configuration
- [ ] Agent is registered in registry (if registry URL is set)

## Common Issues

### Issue: Agent not discoverable
**Solution**: Verify `NEST_REGISTRY_URL` is set and registry is accessible

### Issue: @agent_name not working
**Solution**: Ensure `NEST_AGENT_NAME` matches exactly (case-sensitive)

### Issue: Configuration not loading
**Solution**: Check `.env` file exists and variables are set correctly

### Issue: API key error
**Solution**: Verify `ANTHROPIC_API_KEY` is set and valid

## Documentation Links

- **Full Configuration Guide**: [docs/AGENT_CONFIGURATION.md](docs/AGENT_CONFIGURATION.md)
- **NEST Integration**: [docs/NEST_INTEGRATION.md](docs/NEST_INTEGRATION.md)
- **Run Instructions**: [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md)
- **NEST Monitoring**: [docs/NEST_MONITORING.md](docs/NEST_MONITORING.md)

## Support

For issues or questions:
1. Check the [Troubleshooting](#common-issues) section
2. Review the [full documentation](docs/AGENT_CONFIGURATION.md)
3. Verify configuration with `/nest/config` endpoint
4. Check logs for error messages
