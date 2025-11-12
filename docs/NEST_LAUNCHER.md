# NEST Launcher Usage Guide

The NEST launcher provides a unified way to run the NASDAQ Stock Agent in different deployment modes.

## Modes

### 1. Standalone Mode (FastAPI Only)

Runs only the FastAPI server without NEST integration. This is the default mode and maintains backward compatibility.

```bash
# Using the launcher
python -m src.nest.launcher

# Or using the original main.py
python main.py
```

**Configuration:**
- No NEST environment variables required
- Uses existing FastAPI configuration from config files

### 2. NEST Mode (A2A Only)

Runs only the NEST A2A server for pure agent-to-agent communication.

```bash
# Set required environment variables
export NEST_ENABLED=true
export NEST_AGENT_ID=nasdaq-stock-agent
export NEST_PORT=6000
export NEST_REGISTRY_URL=http://registry.example.com:6900
export NEST_PUBLIC_URL=https://your-domain.com:6000

# Start in NEST mode
python -m src.nest.launcher
```

**Configuration:**
- `NEST_ENABLED=true` - Required to enable NEST
- `NEST_AGENT_ID` - Unique agent identifier (default: nasdaq-stock-agent)
- `NEST_PORT` - A2A server port (default: 6000)
- `NEST_REGISTRY_URL` - Optional registry URL for agent discovery
- `NEST_PUBLIC_URL` - Optional public URL for registration

### 3. Dual Mode (FastAPI + A2A)

Runs both the FastAPI server and NEST A2A server concurrently.

```bash
# Set required environment variables
export NEST_ENABLED=true
export NEST_DUAL_MODE=true
export NEST_AGENT_ID=nasdaq-stock-agent
export NEST_PORT=6000
export NEST_REGISTRY_URL=http://registry.example.com:6900
export NEST_PUBLIC_URL=https://your-domain.com:6000

# Start in dual mode
python -m src.nest.launcher
```

**Configuration:**
- All NEST mode variables plus:
- `NEST_DUAL_MODE=true` - Required to enable dual mode

## Environment Variables

### Required for NEST/Dual Mode

- `NEST_ENABLED` - Enable NEST integration (true/false)
- `NEST_AGENT_ID` - Unique agent identifier

### Optional

- `NEST_AGENT_NAME` - Display name (default: "NASDAQ Stock Agent")
- `NEST_PORT` - A2A server port (default: 6000)
- `NEST_PUBLIC_URL` - Public URL for external access
- `NEST_REGISTRY_URL` - NANDA registry URL for agent discovery
- `NEST_TELEMETRY` - Enable telemetry (default: true)
- `NEST_DUAL_MODE` - Run both servers (default: false)
- `NEST_DOMAIN` - Agent domain (default: "financial analysis")
- `NEST_SPECIALIZATION` - Agent specialization description
- `NEST_CAPABILITIES` - Comma-separated list of capabilities
- `NEST_VERSION` - Agent version (default: "1.0.0")

## Graceful Shutdown

The launcher handles graceful shutdown for all modes:

- Responds to SIGINT (Ctrl+C) and SIGTERM signals
- Deregisters from registry (if registered)
- Stops all running servers
- Cleans up resources

## Examples

### Local Development (Standalone)

```bash
# Just run the FastAPI server
python -m src.nest.launcher
```

### Local Development (Dual Mode)

```bash
# Run both servers locally
export NEST_ENABLED=true
export NEST_DUAL_MODE=true
export NEST_AGENT_ID=nasdaq-stock-agent-dev
export NEST_PORT=6000

python -m src.nest.launcher
```

### Production Deployment (Dual Mode)

```bash
# Set all production variables
export NEST_ENABLED=true
export NEST_DUAL_MODE=true
export NEST_AGENT_ID=nasdaq-stock-agent-prod
export NEST_PORT=6000
export NEST_PUBLIC_URL=https://stock-agent.example.com:6000
export NEST_REGISTRY_URL=https://registry.example.com:6900

# Start the launcher
python -m src.nest.launcher
```

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose both ports
EXPOSE 8000 6000

# Set environment variables
ENV NEST_ENABLED=true
ENV NEST_DUAL_MODE=true
ENV NEST_PORT=6000

# Start in dual mode
CMD ["python", "-m", "src.nest.launcher"]
```

## Programmatic Usage

```python
import asyncio
from src.nest.launcher import AgentLauncher
from src.nest.config import NESTConfig

async def main():
    # Create configuration
    config = NESTConfig.from_env()
    
    # Create launcher
    launcher = AgentLauncher(config=config)
    
    # Start in desired mode
    if config.enable_dual_mode:
        await launcher.start_dual()
    elif config.should_enable_nest():
        await launcher.start_nest()
    else:
        await launcher.start_standalone()

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### NEST Mode Fails to Start

**Issue:** "NEST is not enabled or configuration is invalid"

**Solution:** Ensure `NEST_ENABLED=true` is set and configuration is valid:
```bash
export NEST_ENABLED=true
export NEST_AGENT_ID=nasdaq-stock-agent
```

### Port Already in Use

**Issue:** "Address already in use"

**Solution:** Change the port or stop the conflicting service:
```bash
# For FastAPI (default 8000)
export PORT=8001

# For NEST (default 6000)
export NEST_PORT=6001
```

### Registry Connection Failed

**Issue:** "Failed to register with registry"

**Solution:** This is a warning, not an error. The agent will continue without registry integration. Verify:
- Registry URL is correct
- Registry is accessible from your network
- Network connectivity is working

### Import Errors

**Issue:** "ModuleNotFoundError: No module named 'python-a2a'"

**Solution:** Install NEST dependencies:
```bash
pip install python-a2a
```

## Monitoring

### Check Agent Status

The launcher logs important events:
- Server startup/shutdown
- Registry registration status
- Error conditions

### Health Checks

In dual mode, both endpoints are available:
- FastAPI: `http://localhost:8000/health`
- NEST: Check via registry or A2A protocol

## Migration from main.py

The launcher is backward compatible. To migrate:

1. **No changes needed for standalone mode:**
   ```bash
   # Old way (still works)
   python main.py
   
   # New way (equivalent)
   python -m src.nest.launcher
   ```

2. **Enable NEST integration:**
   ```bash
   # Set environment variables
   export NEST_ENABLED=true
   export NEST_DUAL_MODE=true
   
   # Use launcher
   python -m src.nest.launcher
   ```

3. **Update deployment scripts:**
   Replace `python main.py` with `python -m src.nest.launcher` in your deployment scripts.
