"""
NEST Dual-Mode Launcher

This module provides a unified launcher that can run the NASDAQ Stock Agent in:
- Standalone mode: FastAPI server only (existing functionality)
- NEST mode: A2A server only (NEST integration)
- Dual mode: Both FastAPI and A2A servers concurrently

The launcher handles graceful shutdown and ensures proper cleanup of resources.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import uvicorn

from src.nest.config import NESTConfig
from src.nest.adapter import StockAgentNEST
from src.api.app import create_app
from src.core.config_manager import config_manager

logger = logging.getLogger(__name__)


class AgentLauncher:
    """
    Unified launcher for standalone and NEST modes.
    
    This launcher provides a flexible way to run the stock agent in different
    deployment modes, with proper lifecycle management and graceful shutdown.
    """
    
    def __init__(self, config: Optional[NESTConfig] = None):
        """
        Initialize launcher with configuration.
        
        Args:
            config: Optional NESTConfig object. If not provided, will load from environment.
        """
        self.config = config or NESTConfig.from_env()
        self.nest_adapter: Optional[StockAgentNEST] = None
        self.fastapi_server: Optional[uvicorn.Server] = None
        self._shutdown_event = asyncio.Event()
        self._running = False
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info(f"Initialized AgentLauncher with config: {self.config}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
        
        # Register handlers for common termination signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_standalone(self):
        """
        Start in standalone mode (FastAPI only).
        
        This mode runs only the FastAPI server without NEST integration,
        maintaining backward compatibility with existing deployments.
        
        Raises:
            RuntimeError: If launcher is already running
        """
        if self._running:
            raise RuntimeError("Launcher is already running")
        
        try:
            logger.info("Starting in STANDALONE mode (FastAPI only)")
            self._running = True
            
            # Load application configuration
            app_config_dict = config_manager.load_configuration()
            app_config = app_config_dict.get("application", {})
            
            # Get server configuration
            host = app_config.get("host", "0.0.0.0")
            port = app_config.get("port", 8000)
            
            # Create FastAPI application
            app = create_app()
            
            # Configure uvicorn server
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            self.fastapi_server = uvicorn.Server(config)
            
            logger.info(f"FastAPI server starting on {host}:{port}")
            
            # Run server until shutdown signal
            await self.fastapi_server.serve()
            
            logger.info("FastAPI server stopped")
            
        except Exception as e:
            logger.error(f"Error in standalone mode: {e}", exc_info=True)
            raise
        finally:
            self._running = False
    
    async def start_nest(self):
        """
        Start in NEST mode (A2A only).
        
        This mode runs only the NEST A2A server without the FastAPI endpoints.
        Useful for pure agent-to-agent communication scenarios.
        
        Raises:
            RuntimeError: If launcher is already running or NEST is not enabled
        """
        if self._running:
            raise RuntimeError("Launcher is already running")
        
        if not self.config.should_enable_nest():
            raise RuntimeError(
                "NEST is not enabled or configuration is invalid. "
                "Set NEST_ENABLED=true and provide valid configuration."
            )
        
        try:
            logger.info("Starting in NEST mode (A2A only)")
            self._running = True
            
            # Create NEST adapter
            self.nest_adapter = StockAgentNEST(config=self.config)
            
            # Start NEST agent
            await self.nest_adapter.start_async(register=True)
            
            logger.info(
                f"NEST agent started on port {self.config.nest_port} "
                f"(agent_id: {self.config.agent_id})"
            )
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            logger.info("Shutdown signal received, stopping NEST agent...")
            
            # Stop NEST agent
            await self.nest_adapter.stop_async()
            
            logger.info("NEST agent stopped")
            
        except Exception as e:
            logger.error(f"Error in NEST mode: {e}", exc_info=True)
            raise
        finally:
            self._running = False
    
    async def start_dual(self):
        """
        Start in dual mode (both FastAPI and A2A servers).
        
        This mode runs both the FastAPI server and the NEST A2A server
        concurrently, allowing the agent to serve both traditional HTTP
        requests and A2A messages simultaneously.
        
        Raises:
            RuntimeError: If launcher is already running or NEST is not enabled
        """
        if self._running:
            raise RuntimeError("Launcher is already running")
        
        if not self.config.should_enable_nest():
            raise RuntimeError(
                "NEST is not enabled or configuration is invalid. "
                "Set NEST_ENABLED=true and provide valid configuration."
            )
        
        try:
            logger.info("Starting in DUAL mode (FastAPI + A2A)")
            self._running = True
            
            # Load application configuration
            app_config_dict = config_manager.load_configuration()
            app_config = app_config_dict.get("application", {})
            
            # Get FastAPI server configuration
            fastapi_host = app_config.get("host", "0.0.0.0")
            fastapi_port = app_config.get("port", 8000)
            
            # Create FastAPI application
            app = create_app()
            
            # Configure uvicorn server
            uvicorn_config = uvicorn.Config(
                app=app,
                host=fastapi_host,
                port=fastapi_port,
                log_level="info",
                access_log=True
            )
            
            self.fastapi_server = uvicorn.Server(uvicorn_config)
            
            # Create NEST adapter
            self.nest_adapter = StockAgentNEST(config=self.config)
            
            # Start NEST agent
            await self.nest_adapter.start_async(register=True)
            
            logger.info(
                f"NEST agent started on port {self.config.nest_port} "
                f"(agent_id: {self.config.agent_id})"
            )
            
            # Create task for FastAPI server
            fastapi_task = asyncio.create_task(
                self.fastapi_server.serve(),
                name="fastapi-server"
            )
            
            logger.info(f"FastAPI server started on {fastapi_host}:{fastapi_port}")
            logger.info("Both servers running in dual mode")
            
            # Wait for shutdown signal or server completion
            done, pending = await asyncio.wait(
                [fastapi_task, asyncio.create_task(self._shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            logger.info("Shutdown initiated, stopping servers...")
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Stop NEST agent
            if self.nest_adapter:
                await self.nest_adapter.stop_async()
                logger.info("NEST agent stopped")
            
            # Stop FastAPI server
            if self.fastapi_server:
                self.fastapi_server.should_exit = True
                logger.info("FastAPI server stopped")
            
            logger.info("Dual mode shutdown complete")
            
        except Exception as e:
            logger.error(f"Error in dual mode: {e}", exc_info=True)
            raise
        finally:
            self._running = False
    
    async def shutdown(self):
        """
        Initiate graceful shutdown.
        
        This method signals all running servers to stop and waits for
        them to complete their shutdown procedures.
        """
        logger.info("Initiating graceful shutdown...")
        self._shutdown_event.set()
        
        # Give servers time to shutdown gracefully
        await asyncio.sleep(1)
        
        # Force stop if still running
        if self.nest_adapter and self.nest_adapter.is_running():
            logger.warning("Force stopping NEST adapter")
            await self.nest_adapter.stop_async()
        
        if self.fastapi_server:
            logger.warning("Force stopping FastAPI server")
            self.fastapi_server.should_exit = True
        
        self._running = False
        logger.info("Shutdown complete")
    
    def is_running(self) -> bool:
        """
        Check if launcher is currently running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._running


async def main():
    """
    Main entry point for the launcher.
    
    Determines the appropriate mode based on configuration and starts
    the agent accordingly.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load configuration
        config = NESTConfig.from_env()
        
        # Create launcher
        launcher = AgentLauncher(config=config)
        
        # Determine mode and start
        if config.enable_dual_mode:
            logger.info("Dual mode enabled - starting both FastAPI and A2A servers")
            await launcher.start_dual()
        elif config.should_enable_nest():
            logger.info("NEST mode enabled - starting A2A server only")
            await launcher.start_nest()
        else:
            logger.info("Standalone mode - starting FastAPI server only")
            await launcher.start_standalone()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Launcher failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    """
    Run the launcher when executed as a script.
    
    Usage:
        # Standalone mode (default)
        python -m src.nest.launcher
        
        # NEST mode
        NEST_ENABLED=true python -m src.nest.launcher
        
        # Dual mode
        NEST_ENABLED=true NEST_DUAL_MODE=true python -m src.nest.launcher
    """
    asyncio.run(main())
