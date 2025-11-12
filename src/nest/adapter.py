"""
NEST Adapter for NASDAQ Stock Agent

This module implements the main NEST adapter that wraps the stock agent's
analysis logic and exposes it via the A2A (Agent-to-Agent) protocol using
the NANDA framework.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from src.nest.config import NESTConfig
from src.nest.bridge import StockAgentBridge
from src.nest.registry import RegistryClient
from src.services.investment_analysis import ComprehensiveAnalysisService

logger = logging.getLogger(__name__)


class StockAgentNEST:
    """
    NEST adapter for NASDAQ Stock Agent.
    
    This adapter wraps the stock agent's analysis logic and integrates it
    with the NEST framework for A2A communication. It manages the agent
    lifecycle, including initialization, registration, and shutdown.
    """
    
    def __init__(
        self,
        agent_id: str = "nasdaq-stock-agent",
        port: int = 6000,
        registry_url: Optional[str] = None,
        public_url: Optional[str] = None,
        enable_telemetry: bool = True,
        config: Optional[NESTConfig] = None
    ):
        """
        Initialize NEST adapter with configuration.
        
        Args:
            agent_id: Unique identifier for this agent
            port: Port number for A2A server
            registry_url: URL of the NANDA agent registry
            public_url: Public URL where this agent can be reached
            enable_telemetry: Enable telemetry and monitoring
            config: Optional NESTConfig object (if not provided, will use parameters)
        """
        # Use provided config or create from parameters
        if config:
            self.config = config
        else:
            self.config = NESTConfig(
                agent_id=agent_id,
                nest_port=port,
                registry_url=registry_url,
                public_url=public_url,
                enable_telemetry=enable_telemetry,
                enable_nest=True
            )
        
        self.agent_id = self.config.agent_id
        self.port = self.config.nest_port
        self.registry_url = self.config.registry_url
        self.public_url = self.config.public_url or f"http://localhost:{self.port}"
        
        # Initialize core components
        self.analysis_service = ComprehensiveAnalysisService()
        self.bridge = StockAgentBridge(
            agent_id=self.agent_id,
            analysis_service=self.analysis_service,
            registry_url=self.registry_url
        )
        
        # Initialize registry client if registry URL is provided
        self.registry_client: Optional[RegistryClient] = None
        if self.registry_url:
            self.registry_client = RegistryClient(
                registry_url=self.registry_url,
                agent_id=self.agent_id
            )
        
        # NANDA adapter (will be initialized when python-a2a is available)
        self._nanda_adapter = None
        self._server_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        logger.info(
            f"Initialized StockAgentNEST adapter for '{self.agent_id}' "
            f"(port: {self.port}, registry: {self.registry_url or 'none'})"
        )
    
    async def agent_logic(self, message: str, conversation_id: str) -> str:
        """
        Process incoming A2A messages and return stock analysis.
        
        This is the main entry point for handling A2A messages. It wraps
        the stock analysis logic and formats responses for A2A communication.
        
        Args:
            message: Incoming message content (natural language query)
            conversation_id: Unique identifier for the conversation
            
        Returns:
            str: Formatted response message
            
        Example:
            >>> adapter = StockAgentNEST()
            >>> response = await adapter.agent_logic(
            ...     "What's the analysis for AAPL?",
            ...     "conv-123"
            ... )
        """
        try:
            logger.info(
                f"Processing A2A message (conversation: {conversation_id}): '{message}'"
            )
            
            # Process the stock query through the bridge
            response_dict = await self.bridge.process_stock_query(
                query=message,
                conversation_id=conversation_id
            )
            
            # Extract the text content from the response
            if isinstance(response_dict, dict):
                content = response_dict.get('content', {})
                if isinstance(content, dict):
                    response_text = content.get('text', str(response_dict))
                else:
                    response_text = str(content)
            else:
                response_text = str(response_dict)
            
            logger.debug(f"Generated response for conversation {conversation_id}")
            return response_text
            
        except Exception as e:
            logger.error(
                f"Error in agent_logic for conversation {conversation_id}: {e}",
                exc_info=True
            )
            return f"[{self.agent_id}] ❌ Error processing request: {str(e)}"
    
    async def _register_with_registry(self) -> bool:
        """
        Register agent with the NANDA registry.
        
        Returns:
            bool: True if registration succeeded, False otherwise
        """
        if not self.registry_client:
            logger.info("No registry client configured - skipping registration")
            return True
        
        try:
            logger.info(f"Registering agent '{self.agent_id}' with registry")
            
            # Get agent metadata from config
            metadata = self.config.get_agent_metadata()
            
            # Register with the registry
            success = await self.registry_client.register_agent(
                agent_url=self.public_url,
                capabilities=self.config.capabilities,
                metadata={
                    'agent_name': metadata['agent_name'],
                    'domain': metadata['domain'],
                    'specialization': metadata['specialization'],
                    'description': metadata['description'],
                    'version': metadata['version']
                }
            )
            
            if success:
                logger.info(
                    f"Successfully registered agent '{self.agent_id}' "
                    f"at {self.public_url}"
                )
            else:
                logger.warning(
                    f"Failed to register agent '{self.agent_id}' - "
                    "continuing without registry integration"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error registering with registry: {e}", exc_info=True)
            return False
    
    async def _start_heartbeat(self):
        """
        Start periodic heartbeat to registry.
        
        Sends health status updates to the registry every 30 seconds.
        """
        if not self.registry_client:
            return
        
        logger.info("Starting registry heartbeat")
        
        while self._is_running:
            try:
                # Get health status from bridge
                health_status = await self.bridge.get_health_status()
                status = health_status.get('status', 'unknown')
                
                # Update registry
                await self.registry_client.update_status(
                    status=status,
                    metadata={
                        'last_heartbeat': datetime.utcnow().isoformat(),
                        'health': health_status
                    }
                )
                
                logger.debug(f"Sent heartbeat to registry (status: {status})")
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
            
            # Wait 30 seconds before next heartbeat
            await asyncio.sleep(30)
    
    def start(self, register: bool = True):
        """
        Start the NEST agent server.
        
        This method initializes the NANDA adapter and starts the A2A server.
        If a registry URL is configured and register=True, it will also
        register the agent with the registry.
        
        Args:
            register: Whether to register with the registry (default: True)
            
        Raises:
            RuntimeError: If the agent is already running
            ImportError: If python-a2a package is not installed
        """
        if self._is_running:
            raise RuntimeError(f"Agent '{self.agent_id}' is already running")
        
        try:
            logger.info(f"Starting NEST agent '{self.agent_id}' on port {self.port}")
            
            # Try to import python-a2a
            try:
                from a2a import SimpleAgentBridge as NANDABridge
                logger.info("Successfully imported python-a2a framework")
            except ImportError as e:
                logger.error(
                    "python-a2a package not installed. "
                    "Install it with: pip install python-a2a"
                )
                raise ImportError(
                    "python-a2a package is required for NEST integration. "
                    "Install it with: pip install python-a2a"
                ) from e
            
            # Initialize NANDA adapter
            # Note: The actual implementation depends on the python-a2a API
            # This is a placeholder that will work once python-a2a is installed
            logger.info("Initializing NANDA adapter")
            
            # Create a simple wrapper that adapts our bridge to NANDA's interface
            class NANDAAdapter(NANDABridge):
                def __init__(self, stock_agent_nest):
                    self.stock_agent = stock_agent_nest
                    super().__init__(
                        agent_id=stock_agent_nest.agent_id,
                        port=stock_agent_nest.port
                    )
                
                async def process_message(self, message: str, conversation_id: str) -> str:
                    return await self.stock_agent.agent_logic(message, conversation_id)
            
            self._nanda_adapter = NANDAAdapter(self)
            
            # Mark as running
            self._is_running = True
            
            # Register with registry if requested
            if register and self.registry_client:
                asyncio.create_task(self._register_with_registry())
                # Start heartbeat
                asyncio.create_task(self._start_heartbeat())
            
            logger.info(
                f"NEST agent '{self.agent_id}' started successfully "
                f"(A2A endpoint: {self.public_url})"
            )
            
        except Exception as e:
            logger.error(f"Failed to start NEST agent: {e}", exc_info=True)
            self._is_running = False
            raise
    
    async def start_async(self, register: bool = True):
        """
        Async version of start() for use in async contexts.
        
        Args:
            register: Whether to register with the registry (default: True)
        """
        if self._is_running:
            raise RuntimeError(f"Agent '{self.agent_id}' is already running")
        
        try:
            logger.info(f"Starting NEST agent '{self.agent_id}' on port {self.port}")
            
            # Try to import python-a2a
            try:
                from a2a import SimpleAgentBridge as NANDABridge
                logger.info("Successfully imported python-a2a framework")
            except ImportError as e:
                logger.error(
                    "python-a2a package not installed. "
                    "Install it with: pip install python-a2a"
                )
                raise ImportError(
                    "python-a2a package is required for NEST integration. "
                    "Install it with: pip install python-a2a"
                ) from e
            
            # Initialize NANDA adapter
            logger.info("Initializing NANDA adapter")
            
            # Create adapter (implementation depends on python-a2a API)
            class NANDAAdapter(NANDABridge):
                def __init__(self, stock_agent_nest):
                    self.stock_agent = stock_agent_nest
                    super().__init__(
                        agent_id=stock_agent_nest.agent_id,
                        port=stock_agent_nest.port
                    )
                
                async def process_message(self, message: str, conversation_id: str) -> str:
                    return await self.stock_agent.agent_logic(message, conversation_id)
            
            self._nanda_adapter = NANDAAdapter(self)
            
            # Mark as running
            self._is_running = True
            
            # Register with registry if requested
            if register and self.registry_client:
                await self._register_with_registry()
                # Start heartbeat in background
                asyncio.create_task(self._start_heartbeat())
            
            logger.info(
                f"NEST agent '{self.agent_id}' started successfully "
                f"(A2A endpoint: {self.public_url})"
            )
            
        except Exception as e:
            logger.error(f"Failed to start NEST agent: {e}", exc_info=True)
            self._is_running = False
            raise
    
    def stop(self):
        """
        Stop the NEST agent and cleanup.
        
        This method performs graceful shutdown, including:
        - Deregistering from the registry
        - Stopping the A2A server
        - Cleaning up resources
        """
        if not self._is_running:
            logger.warning(f"Agent '{self.agent_id}' is not running")
            return
        
        try:
            logger.info(f"Stopping NEST agent '{self.agent_id}'")
            
            # Mark as not running (stops heartbeat)
            self._is_running = False
            
            # Deregister from registry
            if self.registry_client:
                try:
                    # Run deregister in event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.registry_client.deregister())
                    else:
                        loop.run_until_complete(self.registry_client.deregister())
                except Exception as e:
                    logger.error(f"Error deregistering from registry: {e}")
            
            # Stop NANDA adapter
            if self._nanda_adapter:
                try:
                    if hasattr(self._nanda_adapter, 'stop'):
                        self._nanda_adapter.stop()
                except Exception as e:
                    logger.error(f"Error stopping NANDA adapter: {e}")
            
            # Close registry client session
            if self.registry_client:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.registry_client.close())
                    else:
                        loop.run_until_complete(self.registry_client.close())
                except Exception as e:
                    logger.error(f"Error closing registry client: {e}")
            
            logger.info(f"NEST agent '{self.agent_id}' stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping NEST agent: {e}", exc_info=True)
    
    async def stop_async(self):
        """
        Async version of stop() for use in async contexts.
        """
        if not self._is_running:
            logger.warning(f"Agent '{self.agent_id}' is not running")
            return
        
        try:
            logger.info(f"Stopping NEST agent '{self.agent_id}'")
            
            # Mark as not running (stops heartbeat)
            self._is_running = False
            
            # Deregister from registry
            if self.registry_client:
                try:
                    await self.registry_client.deregister()
                except Exception as e:
                    logger.error(f"Error deregistering from registry: {e}")
            
            # Stop NANDA adapter
            if self._nanda_adapter:
                try:
                    if hasattr(self._nanda_adapter, 'stop'):
                        if asyncio.iscoroutinefunction(self._nanda_adapter.stop):
                            await self._nanda_adapter.stop()
                        else:
                            self._nanda_adapter.stop()
                except Exception as e:
                    logger.error(f"Error stopping NANDA adapter: {e}")
            
            # Close registry client session
            if self.registry_client:
                try:
                    await self.registry_client.close()
                except Exception as e:
                    logger.error(f"Error closing registry client: {e}")
            
            logger.info(f"NEST agent '{self.agent_id}' stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping NEST agent: {e}", exc_info=True)
    
    def is_running(self) -> bool:
        """
        Check if the agent is currently running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._is_running
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the NEST agent.
        
        Returns:
            Dict containing status information including full agent configuration
        """
        try:
            # Get bridge health status
            bridge_health = await self.bridge.get_health_status()
            
            # Get registry status
            registry_status = {
                'configured': self.registry_client is not None,
                'registered': self.registry_client.is_registered() if self.registry_client else False,
                'url': self.registry_url
            }
            
            # Get full agent configuration
            agent_config = self.config.get_agent_config_for_communication()
            
            return {
                'agent_id': self.agent_id,
                'status': 'running' if self._is_running else 'stopped',
                'port': self.port,
                'public_url': self.public_url,
                'bridge_health': bridge_health,
                'registry': registry_status,
                'agent_config': agent_config,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                'agent_id': self.agent_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the complete agent configuration for agent-to-agent communication.
        
        Returns:
            Dict containing all agent configuration details
        """
        return self.config.get_agent_metadata()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_async()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_async()
