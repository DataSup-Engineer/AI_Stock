# Outgoing A2A Communication

This document describes how to use the outgoing A2A (Agent-to-Agent) communication features in the NASDAQ Stock Agent.

## Overview

The Stock Agent can now send messages to other agents in the NANDA network using the `send_to_agent()` method. This enables:

- Requesting information from specialized agents
- Delegating tasks to other agents
- Building multi-agent workflows
- Agent collaboration and coordination

## Features

### 1. Direct Agent Messaging

Send messages directly to other agents by their agent ID:

```python
from src.nest.bridge import StockAgentBridge

# Initialize bridge with registry
bridge = StockAgentBridge(
    agent_id="nasdaq-stock-agent",
    registry_url="http://registry.example.com:6900"
)

# Send message to another agent
response = await bridge.send_to_agent(
    target_agent_id="financial-advisor",
    message="Should I buy AAPL based on current market conditions?",
    conversation_id="conv-123"
)

# Process response
if response and "error" not in response:
    print(response["content"]["text"])
else:
    print(f"Error: {response['message']}")
```

### 2. @agent-id Syntax

Use the `@agent-id` syntax in queries to automatically route messages:

```python
# Query with @agent-id mention
query = "@financial-advisor Should I buy AAPL?"

# Process query - automatically forwards to financial-advisor
response = await bridge.process_stock_query(
    query=query,
    conversation_id="conv-123"
)
```

The bridge will:
1. Parse the `@agent-id` from the query
2. Look up the agent in the registry
3. Forward the remaining message to that agent
4. Return the response

### 3. Agent Discovery

Look up agents in the registry:

```python
# Get agent URL
agent_url = await bridge.registry_client.lookup_agent("financial-advisor")

# Get detailed agent information
agent_info = await bridge.registry_client.get_agent_info("financial-advisor")
print(f"Agent: {agent_info['agent_name']}")
print(f"Capabilities: {agent_info['capabilities']}")

# List all agents with specific capability
agents = await bridge.registry_client.list_agents(capability="risk_analysis")
```

## Message Format

### Outgoing Message Structure

```json
{
  "role": "user",
  "content": {
    "text": "Your message here",
    "type": "text"
  },
  "conversation_id": "conv-20241112-103045-abc123",
  "metadata": {
    "from_agent_id": "nasdaq-stock-agent",
    "timestamp": "2024-11-12T10:30:45.123456Z"
  }
}
```

### Response Structure

```json
{
  "role": "agent",
  "content": {
    "text": "[target-agent] Response text here",
    "type": "text"
  },
  "conversation_id": "conv-20241112-103045-abc123",
  "parent_message_id": "msg-456"
}
```

## Error Handling

The implementation includes comprehensive error handling:

### Registry Not Configured

```python
bridge = StockAgentBridge()  # No registry URL

response = await bridge.send_to_agent("test-agent", "Hello")
# Returns: {"error": "Registry not configured", "message": "..."}
```

### Agent Not Found

```python
response = await bridge.send_to_agent("nonexistent-agent", "Hello")
# Returns: {"error": "Agent not found", "message": "..."}
```

### Connection Timeout

```python
# Configure timeout (default: 30 seconds)
bridge = StockAgentBridge(
    registry_url="http://registry:6900",
    message_timeout=10  # 10 seconds
)

response = await bridge.send_to_agent("slow-agent", "Complex query")
# Returns: {"error": "Timeout", "message": "..."} if agent doesn't respond
```

### Connection Error

```python
response = await bridge.send_to_agent("offline-agent", "Hello")
# Returns: {"error": "Connection error", "message": "..."}
```

## Usage Examples

### Example 1: Risk Assessment Delegation

```python
async def analyze_with_risk_assessment(ticker: str):
    """Analyze a stock and get risk assessment from risk agent."""
    
    bridge = StockAgentBridge(registry_url="http://registry:6900")
    
    # Perform stock analysis
    analysis = await bridge.analysis_service.perform_complete_analysis(ticker)
    
    # Get risk assessment from specialized agent
    risk_response = await bridge.send_to_agent(
        target_agent_id="risk-analyzer",
        message=f"Assess risk for {ticker} with current price ${analysis.market_data.current_price}",
        conversation_id="risk-analysis-001"
    )
    
    # Combine results
    if risk_response and "error" not in risk_response:
        print(f"Stock Analysis: {analysis.summary}")
        print(f"Risk Assessment: {risk_response['content']['text']}")
    
    await bridge.close()
```

### Example 2: Multi-Agent Consultation

```python
async def get_investment_advice(ticker: str):
    """Get advice from multiple specialized agents."""
    
    bridge = StockAgentBridge(registry_url="http://registry:6900")
    
    # Consult multiple agents
    agents = [
        ("technical-analyst", f"Technical analysis for {ticker}"),
        ("fundamental-analyst", f"Fundamental analysis for {ticker}"),
        ("sentiment-analyzer", f"Market sentiment for {ticker}")
    ]
    
    responses = []
    for agent_id, message in agents:
        response = await bridge.send_to_agent(
            target_agent_id=agent_id,
            message=message,
            conversation_id=f"consultation-{ticker}"
        )
        responses.append((agent_id, response))
    
    # Aggregate responses
    for agent_id, response in responses:
        if response and "error" not in response:
            print(f"\n{agent_id}:")
            print(response["content"]["text"])
    
    await bridge.close()
```

### Example 3: Using @agent-id Syntax

```python
async def handle_user_query(query: str):
    """Handle user queries with automatic agent routing."""
    
    bridge = StockAgentBridge(registry_url="http://registry:6900")
    
    # User can specify target agent with @agent-id
    # Examples:
    # - "analyze AAPL" -> handled by stock agent
    # - "@financial-advisor Should I buy AAPL?" -> forwarded to advisor
    # - "@risk-analyzer What's the risk for TSLA?" -> forwarded to risk analyzer
    
    response = await bridge.process_stock_query(
        query=query,
        conversation_id="user-session-123"
    )
    
    print(response["content"]["text"])
    
    await bridge.close()
```

## Best Practices

### 1. Use Context Manager

Always use the async context manager for automatic cleanup:

```python
async with StockAgentBridge(registry_url="http://registry:6900") as bridge:
    response = await bridge.send_to_agent("target-agent", "message")
    # Session automatically closed
```

### 2. Handle Errors Gracefully

Always check for errors in responses:

```python
response = await bridge.send_to_agent("target-agent", "message")

if response and "error" in response:
    logger.error(f"Agent communication failed: {response['message']}")
    # Implement fallback logic
else:
    # Process successful response
    process_response(response)
```

### 3. Set Appropriate Timeouts

Configure timeouts based on expected response times:

```python
# For quick queries
bridge = StockAgentBridge(registry_url="...", message_timeout=10)

# For complex analysis
bridge = StockAgentBridge(registry_url="...", message_timeout=60)
```

### 4. Reuse Conversation IDs

Use consistent conversation IDs for related messages:

```python
from src.nest.message_formatter import create_conversation_id

conv_id = create_conversation_id()

# First message
response1 = await bridge.send_to_agent("agent1", "message1", conv_id)

# Follow-up message in same conversation
response2 = await bridge.send_to_agent("agent1", "message2", conv_id)
```

### 5. Monitor Health Status

Check bridge health before sending messages:

```python
health = await bridge.get_health_status()

if health["status"] == "healthy" and health["registry_configured"]:
    # Safe to send messages
    response = await bridge.send_to_agent("target-agent", "message")
else:
    logger.warning("Bridge not healthy, skipping agent communication")
```

## Configuration

### Environment Variables

```bash
# Enable NEST integration
export NEST_ENABLED=true

# Registry URL for agent discovery
export NEST_REGISTRY_URL=http://registry.example.com:6900

# Agent identification
export NEST_AGENT_ID=nasdaq-stock-agent

# Message timeout (optional, default: 30)
export NEST_MESSAGE_TIMEOUT=30
```

### Programmatic Configuration

```python
from src.nest.config import NESTConfig

config = NESTConfig.from_env()

bridge = StockAgentBridge(
    agent_id=config.agent_id,
    registry_url=config.registry_url,
    message_timeout=30
)
```

## Testing

### Unit Tests

Test @agent-id parsing:

```python
def test_parse_agent_mention():
    bridge = StockAgentBridge()
    
    agent_id, msg = bridge.parse_agent_mention("@advisor Buy AAPL?")
    assert agent_id == "advisor"
    assert msg == "Buy AAPL?"
```

### Integration Tests

Test with mock registry:

```python
async def test_send_to_agent():
    # Use test registry
    bridge = StockAgentBridge(registry_url="http://test-registry:6900")
    
    response = await bridge.send_to_agent(
        target_agent_id="test-agent",
        message="test message",
        conversation_id="test-conv"
    )
    
    assert response is not None
    await bridge.close()
```

## Troubleshooting

### Agent Not Found

**Problem**: `{"error": "Agent not found"}`

**Solutions**:
- Verify the agent ID is correct
- Check if the target agent is registered in the registry
- Use `list_agents()` to see available agents

### Connection Timeout

**Problem**: `{"error": "Timeout"}`

**Solutions**:
- Increase the `message_timeout` value
- Check if the target agent is responsive
- Verify network connectivity

### Registry Not Configured

**Problem**: `{"error": "Registry not configured"}`

**Solutions**:
- Provide `registry_url` when initializing the bridge
- Set `NEST_REGISTRY_URL` environment variable
- Verify the registry URL is accessible

## See Also

- [NEST Integration Design](../specs/nest-integration/design.md)
- [NEST Requirements](../specs/nest-integration/requirements.md)
- [A2A Protocol Documentation](A2A_PROTOCOL.md)
