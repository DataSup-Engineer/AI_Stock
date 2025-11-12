"""
NASDAQ Stock Agent - Main Application Entry Point
"""
import asyncio
import logging
import uvicorn
from typing import Optional
from src.api.app import create_app
from src.core.config_manager import config_manager
from src.core.dependencies import service_container
from src.nest.config import NESTConfig
from src.nest.adapter import StockAgentNEST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global NEST adapter instance
_nest_adapter: Optional[StockAgentNEST] = None


def main():
    """Main application entry point"""
    try:
        # Load configuration
        config = config_manager.load_configuration()
        app_config = config.get("application", {})
        
        # Create FastAPI application
        app = create_app()
        
        logger.info(f"Starting {app_config.get('name', 'NASDAQ Stock Agent')} v{app_config.get('version', '1.0.0')}")
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


async def startup_check():
    """Perform startup health check"""
    try:
        logger.info("Performing startup health check...")
        
        # Initialize services
        await service_container.initialize()
        
        # Get system status
        status = await service_container.get_system_status()
        
        if status.get('status') in ['healthy', 'degraded']:
            logger.info("Startup health check passed")
            return True
        else:
            logger.error(f"Startup health check failed: {status}")
            return False
            
    except Exception as e:
        logger.error(f"Startup health check error: {e}")
        return False


async def initialize_nest():
    """
    Initialize NEST integration if enabled.
    
    Returns:
        Optional[StockAgentNEST]: NEST adapter instance if enabled, None otherwise
    """
    global _nest_adapter
    
    try:
        # Load NEST configuration
        nest_config = NESTConfig.from_env()
        
        # Check if NEST should be enabled
        if not nest_config.should_enable_nest():
            logger.info("NEST integration is disabled - running in standalone mode")
            return None
        
        logger.info("NEST integration is enabled - initializing NEST adapter")
        
        # Validate configuration
        is_valid, errors = nest_config.validate()
        if not is_valid:
            logger.error(f"NEST configuration validation failed: {', '.join(errors)}")
            logger.warning("Falling back to standalone mode")
            return None
        
        # Create NEST adapter
        _nest_adapter = StockAgentNEST(config=nest_config)
        
        # Start NEST adapter
        await _nest_adapter.start_async(register=True)
        
        logger.info(
            f"NEST adapter started successfully "
            f"(agent_id: {nest_config.agent_id}, port: {nest_config.nest_port})"
        )
        
        return _nest_adapter
        
    except ImportError as e:
        logger.warning(
            f"NEST integration requires python-a2a package: {e}. "
            "Running in standalone mode. Install with: pip install python-a2a"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize NEST integration: {e}", exc_info=True)
        logger.warning("Continuing in standalone mode")
        return None


async def shutdown_nest():
    """Shutdown NEST integration if running."""
    global _nest_adapter
    
    if _nest_adapter and _nest_adapter.is_running():
        try:
            logger.info("Shutting down NEST adapter...")
            await _nest_adapter.stop_async()
            logger.info("NEST adapter stopped successfully")
        except Exception as e:
            logger.error(f"Error shutting down NEST adapter: {e}", exc_info=True)
        finally:
            _nest_adapter = None


def get_nest_adapter() -> Optional[StockAgentNEST]:
    """
    Get the global NEST adapter instance.
    
    Returns:
        Optional[StockAgentNEST]: NEST adapter if initialized, None otherwise
    """
    return _nest_adapter


if __name__ == "__main__":
    try:
        # Load configuration
        config = config_manager.load_configuration()
        app_config = config.get("application", {})
        
        # Get server configuration
        host = app_config.get("host", "0.0.0.0")
        port = app_config.get("port", 8000)
        debug = app_config.get("debug", False)
        
        logger.info(f"Starting server on {host}:{port} (debug={debug})")
        
        # Run server
        uvicorn.run(
            "main:main",
            host=host,
            port=port,
            reload=debug,
            factory=True,
            log_level="info" if not debug else "debug"
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        exit(1)