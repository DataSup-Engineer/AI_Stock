# NEST Integration Monitoring and Logging

This document describes the monitoring and logging capabilities added to the NEST integration for the NASDAQ Stock Agent.

## Overview

The NEST integration now includes comprehensive logging and monitoring for all A2A (Agent-to-Agent) communication and registry operations. This enables tracking of message flows, performance metrics, and troubleshooting of integration issues.

## Logging Capabilities

### 1. A2A Message Logging

All A2A messages (incoming and outgoing) are logged with the following information:

- **Message Type**: Type of message (e.g., 'stock_query', 'analysis_response', 'agent_forward')
- **Direction**: 'incoming' or 'outgoing'
- **Agent ID**: ID of the agent sending/receiving the message
- **Conversation ID**: Unique identifier for the conversation
- **Message Content**: Content of the message (truncated if > 500 characters)
- **Target Agent ID**: For outgoing messages, the target agent ID
- **Status**: 'success', 'error', 'timeout', or 'processing'
- **Error Message**: Error details if status is 'error'
- **Processing Time**: Time taken to process the message (in milliseconds)
- **Metadata**: Additional context-specific metadata

#### Example Usage

```python
from src.services.logging_service import logging_service

# Log incoming message
await logging_service.log_nest_message(
    message_type='stock_query',
    direction='incoming',
    agent_id='nasdaq-stock-agent',
    conversation_id='conv-123',
    message_content='analyze AAPL',
    status='processing'
)

# Log successful response
await logging_service.log_nest_message(
    message_type='analysis_response',
    direction='outgoing',
    agent_id='nasdaq-stock-agent',
    conversation_id='conv-123',
    message_content='Analysis for AAPL: BUY',
    status='success',
    processing_time_ms=1250,
    metadata={
        'ticker': 'AAPL',
        'recommendation': 'BUY',
        'confidence_score': 0.85
    }
)
```

### 2. Registry Operation Logging

All NANDA registry operations are logged with the following information:

- **Operation**: Type of operation ('register', 'lookup', 'status_update', 'deregister')
- **Agent ID**: ID of the agent performing the operation
- **Status**: 'success', 'error', or 'retry'
- **Error Message**: Error details if status is 'error'
- **Metadata**: Operation-specific metadata (e.g., target_agent_id for lookup, capabilities for register)

#### Example Usage

```python
from src.services.logging_service import logging_service

# Log successful registration
await logging_service.log_nest_registry_operation(
    operation='register',
    agent_id='nasdaq-stock-agent',
    status='success',
    metadata={
        'agent_url': 'https://stock-agent.example.com:6000',
        'capabilities': ['stock_analysis', 'technical_analysis'],
        'registry_url': 'http://registry:6900'
    }
)

# Log agent lookup
await logging_service.log_nest_registry_operation(
    operation='lookup',
    agent_id='nasdaq-stock-agent',
    status='success',
    metadata={
        'target_agent_id': 'financial-advisor',
        'agent_url': 'https://advisor.example.com:6000'
    }
)
```

## Monitoring Metrics

### NEST Statistics Endpoint

The logging service provides a `get_nest_statistics()` method that returns comprehensive metrics about NEST integration activity over the last 24 hours:

```python
from src.services.logging_service import logging_service

stats = await logging_service.get_nest_statistics()
```

#### Metrics Included

**Message Metrics:**
- Total messages (incoming + outgoing)
- Incoming message count
- Outgoing message count
- Successful message count
- Failed message count
- Success rate percentage

**Registry Metrics:**
- Total registry operations
- Successful operations
- Success rate percentage

**Performance Metrics:**
- Average processing time (ms)
- Maximum processing time (ms)
- Minimum processing time (ms)

#### Example Response

```json
{
  "service": "NEST Integration",
  "period": "24 hours",
  "messages": {
    "total": 150,
    "incoming": 75,
    "outgoing": 75,
    "successful": 145,
    "failed": 5,
    "success_rate": "96.7%"
  },
  "registry": {
    "total_operations": 25,
    "successful_operations": 24,
    "success_rate": "96.0%"
  },
  "performance": {
    "avg_processing_time": 1250.5,
    "max_processing_time": 3500,
    "min_processing_time": 250
  },
  "timestamp": "2024-11-12T10:30:00Z"
}
```

## Health Check Integration

### System Status Endpoint

The `/status` endpoint now includes NEST metrics in the response:

```bash
GET /status
```

Response includes:

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
      "public_url": "https://stock-agent.example.com:6000",
      "bridge_health": { ... },
      "registry": {
        "configured": true,
        "registered": true,
        "url": "http://registry:6900"
      },
      "metrics": {
        "service": "NEST Integration",
        "messages": { ... },
        "registry": { ... },
        "performance": { ... }
      }
    }
  }
}
```

### NEST-Specific Status Endpoint

The `/nest` endpoint provides detailed NEST integration status including metrics:

```bash
GET /nest
```

Response:

```json
{
  "success": true,
  "nest_status": {
    "agent_id": "nasdaq-stock-agent",
    "status": "running",
    "port": 6000,
    "public_url": "https://stock-agent.example.com:6000",
    "bridge_health": {
      "bridge": "StockAgentBridge",
      "agent_id": "nasdaq-stock-agent",
      "status": "healthy",
      "analysis_service": { ... },
      "registry_configured": true,
      "registry_connected": true
    },
    "registry": {
      "configured": true,
      "registered": true,
      "url": "http://registry:6900"
    },
    "metrics": {
      "service": "NEST Integration",
      "period": "24 hours",
      "messages": {
        "total": 150,
        "incoming": 75,
        "outgoing": 75,
        "successful": 145,
        "failed": 5,
        "success_rate": "96.7%"
      },
      "registry": {
        "total_operations": 25,
        "successful_operations": 24,
        "success_rate": "96.0%"
      },
      "performance": {
        "avg_processing_time": 1250.5,
        "max_processing_time": 3500,
        "min_processing_time": 250
      }
    }
  },
  "timestamp": "2024-11-12T10:30:00Z"
}
```

## Automatic Logging Integration

### Bridge Component

The `StockAgentBridge` automatically logs:

1. **Incoming Messages**: When an A2A message is received
2. **Successful Responses**: When analysis completes successfully
3. **Failed Responses**: When analysis fails or errors occur
4. **Outgoing Messages**: When forwarding messages to other agents
5. **Timeouts**: When agent communication times out
6. **Connection Errors**: When unable to connect to target agents

### Registry Client

The `RegistryClient` automatically logs:

1. **Registration**: When agent registers with the registry
2. **Lookups**: When looking up other agents
3. **Status Updates**: When updating agent status (heartbeats)
4. **Deregistration**: When agent deregisters on shutdown

## Data Storage

All NEST logs are stored in MongoDB in the `errors` collection with special log types:

- **NEST_MESSAGE_LOG**: For A2A message events
- **NEST_REGISTRY_LOG**: For registry operations

Logs are subject to the same 30-day TTL (Time To Live) as other logs in the system.

## Querying Logs

You can query NEST logs using the existing logging service methods:

```python
from src.services.logging_service import logging_service
from datetime import datetime, timedelta

# Get NEST message logs from last 24 hours
yesterday = datetime.utcnow() - timedelta(days=1)
message_logs = await logging_service.get_error_logs(
    start_date=yesterday,
    error_type='NEST_MESSAGE_LOG',
    limit=100
)

# Get registry operation logs
registry_logs = await logging_service.get_error_logs(
    start_date=yesterday,
    error_type='NEST_REGISTRY_LOG',
    limit=100
)
```

## Monitoring Best Practices

1. **Regular Health Checks**: Monitor the `/nest` endpoint regularly to ensure NEST integration is healthy
2. **Track Success Rates**: Watch message and registry success rates - rates below 95% may indicate issues
3. **Monitor Processing Times**: Sudden increases in average processing time may indicate performance problems
4. **Review Failed Messages**: Investigate failed messages to identify patterns or recurring issues
5. **Registry Connectivity**: Ensure registry operations are succeeding - failed lookups prevent agent communication

## Troubleshooting

### High Message Failure Rate

If message success rate is low:
1. Check network connectivity to other agents
2. Verify target agents are registered and healthy
3. Review error messages in logs for specific issues
4. Check timeout settings if seeing many timeout errors

### Registry Operation Failures

If registry operations are failing:
1. Verify registry URL is correct and accessible
2. Check network connectivity to registry service
3. Ensure registry service is running and healthy
4. Review registry logs for authentication or authorization issues

### Performance Issues

If processing times are high:
1. Check analysis service health and performance
2. Review database query performance
3. Monitor system resource usage (CPU, memory)
4. Consider scaling if load is consistently high

## Related Documentation

- [NEST Integration Guide](./NEST_INTEGRATION.md)
- [NEST Launcher Documentation](./NEST_LAUNCHER.md)
- [A2A Outgoing Communication](./A2A_OUTGOING_COMMUNICATION.md)
