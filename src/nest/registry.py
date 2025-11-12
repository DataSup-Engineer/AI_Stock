"""
NANDA Registry Client

This module implements the client for communicating with the NANDA agent registry.
It handles agent registration, status updates, agent lookup, and deregistration.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp
from aiohttp import ClientTimeout, ClientError
from src.services.logging_service import logging_service

logger = logging.getLogger(__name__)


class RegistryClient:
    """
    Client for NANDA agent registry.
    
    This client manages all communication with the NANDA registry service,
    including agent registration, status updates, and agent discovery.
    """
    
    def __init__(
        self,
        registry_url: str,
        agent_id: str,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize registry client.
        
        Args:
            registry_url: Base URL of the NANDA registry service
            agent_id: Unique identifier for this agent
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        """
        self.registry_url = registry_url.rstrip('/')
        self.agent_id = agent_id
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
        self._registered = False
        
        logger.info(
            f"Initialized RegistryClient for agent '{agent_id}' "
            f"(registry: {registry_url})"
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session.
        
        Returns:
            aiohttp.ClientSession: Active session for HTTP requests
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed registry client session")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to registry with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Optional request body data
            retry_count: Current retry attempt number
            
        Returns:
            Optional[Dict]: Response data or None if failed
        """
        url = f"{self.registry_url}{endpoint}"
        
        try:
            session = await self._get_session()
            
            async with session.request(method, url, json=data) as response:
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    logger.debug(f"{method} {endpoint} succeeded (status: {response.status})")
                    return result
                else:
                    error_text = await response.text()
                    logger.warning(
                        f"{method} {endpoint} failed with status {response.status}: {error_text}"
                    )
                    
                    # Retry on server errors (5xx)
                    if response.status >= 500 and retry_count < self.max_retries:
                        return await self._retry_request(method, endpoint, data, retry_count)
                    
                    return None
        
        except ClientError as e:
            logger.error(f"Client error during {method} {endpoint}: {e}")
            
            # Retry on connection errors
            if retry_count < self.max_retries:
                return await self._retry_request(method, endpoint, data, retry_count)
            
            return None
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout during {method} {endpoint}")
            
            # Retry on timeout
            if retry_count < self.max_retries:
                return await self._retry_request(method, endpoint, data, retry_count)
            
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error during {method} {endpoint}: {e}", exc_info=True)
            return None
    
    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]],
        retry_count: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retry a failed request with exponential backoff.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            data: Optional request body data
            retry_count: Current retry attempt number
            
        Returns:
            Optional[Dict]: Response data or None if failed
        """
        retry_count += 1
        delay = self.retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
        
        logger.info(
            f"Retrying {method} {endpoint} (attempt {retry_count}/{self.max_retries}) "
            f"after {delay:.1f}s delay"
        )
        
        await asyncio.sleep(delay)
        
        return await self._make_request(method, endpoint, data, retry_count)
    
    async def register_agent(
        self,
        agent_url: str,
        capabilities: List[str],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Register agent with the NANDA registry.
        
        This method registers the agent with the registry, providing all
        necessary metadata for agent discovery and communication.
        
        Args:
            agent_url: Public URL where this agent can be reached
            capabilities: List of agent capabilities
            metadata: Additional agent metadata (name, domain, description, etc.)
            
        Returns:
            bool: True if registration succeeded, False otherwise
            
        Example:
            >>> client = RegistryClient("http://registry:6900", "stock-agent")
            >>> success = await client.register_agent(
            ...     agent_url="https://stock-agent.example.com:6000",
            ...     capabilities=["stock_analysis", "technical_analysis"],
            ...     metadata={
            ...         "agent_name": "NASDAQ Stock Agent",
            ...         "domain": "financial analysis",
            ...         "description": "AI-powered stock analysis"
            ...     }
            ... )
        """
        try:
            logger.info(f"Registering agent '{self.agent_id}' with registry")
            
            # Prepare registration payload
            registration_data = {
                "agent_id": self.agent_id,
                "agent_url": agent_url,
                "capabilities": capabilities,
                "status": "healthy",
                "registered_at": datetime.utcnow().isoformat(),
                **metadata
            }
            
            # Make registration request
            response = await self._make_request(
                method="POST",
                endpoint="/agents/register",
                data=registration_data
            )
            
            if response:
                self._registered = True
                logger.info(
                    f"Successfully registered agent '{self.agent_id}' "
                    f"at {agent_url} with capabilities: {', '.join(capabilities)}"
                )
                
                # Log successful registration
                await logging_service.log_nest_registry_operation(
                    operation='register',
                    agent_id=self.agent_id,
                    status='success',
                    metadata={
                        'agent_url': agent_url,
                        'capabilities': capabilities,
                        'registry_url': self.registry_url
                    }
                )
                
                return True
            else:
                logger.error(f"Failed to register agent '{self.agent_id}'")
                
                # Log failed registration
                await logging_service.log_nest_registry_operation(
                    operation='register',
                    agent_id=self.agent_id,
                    status='error',
                    error_message='Registration request failed',
                    metadata={
                        'agent_url': agent_url,
                        'registry_url': self.registry_url
                    }
                )
                
                return False
        
        except Exception as e:
            logger.error(f"Error registering agent '{self.agent_id}': {e}", exc_info=True)
            
            # Log registration error
            await logging_service.log_nest_registry_operation(
                operation='register',
                agent_id=self.agent_id,
                status='error',
                error_message=str(e),
                metadata={'registry_url': self.registry_url}
            )
            
            return False
    
    async def update_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update agent status in the registry.
        
        This method is used for health check updates and status changes.
        Should be called periodically to indicate the agent is still alive.
        
        Args:
            status: Agent status (e.g., "healthy", "degraded", "unhealthy")
            metadata: Optional additional metadata to update
            
        Returns:
            bool: True if update succeeded, False otherwise
            
        Example:
            >>> client = RegistryClient("http://registry:6900", "stock-agent")
            >>> success = await client.update_status(
            ...     status="healthy",
            ...     metadata={"requests_processed": 1500}
            ... )
        """
        try:
            logger.debug(f"Updating status for agent '{self.agent_id}' to '{status}'")
            
            # Prepare status update payload
            update_data = {
                "agent_id": self.agent_id,
                "status": status,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Add optional metadata
            if metadata:
                update_data.update(metadata)
            
            # Make status update request
            response = await self._make_request(
                method="PUT",
                endpoint=f"/agents/{self.agent_id}/status",
                data=update_data
            )
            
            if response:
                logger.debug(f"Successfully updated status for agent '{self.agent_id}'")
                return True
            else:
                logger.warning(f"Failed to update status for agent '{self.agent_id}'")
                return False
        
        except Exception as e:
            logger.error(
                f"Error updating status for agent '{self.agent_id}': {e}",
                exc_info=True
            )
            return False
    
    async def lookup_agent(self, agent_id: str) -> Optional[str]:
        """
        Look up another agent's URL in the registry.
        
        This method is used for agent discovery when sending messages
        to other agents in the NANDA network.
        
        Args:
            agent_id: ID of the agent to look up
            
        Returns:
            Optional[str]: Agent's URL if found, None otherwise
            
        Example:
            >>> client = RegistryClient("http://registry:6900", "stock-agent")
            >>> url = await client.lookup_agent("financial-advisor")
            >>> if url:
            ...     print(f"Found agent at: {url}")
        """
        try:
            logger.debug(f"Looking up agent '{agent_id}' in registry")
            
            # Make lookup request
            response = await self._make_request(
                method="GET",
                endpoint=f"/agents/{agent_id}"
            )
            
            if response and "agent_url" in response:
                agent_url = response["agent_url"]
                logger.info(f"Found agent '{agent_id}' at {agent_url}")
                
                # Log successful lookup
                await logging_service.log_nest_registry_operation(
                    operation='lookup',
                    agent_id=self.agent_id,
                    status='success',
                    metadata={
                        'target_agent_id': agent_id,
                        'agent_url': agent_url,
                        'registry_url': self.registry_url
                    }
                )
                
                return agent_url
            else:
                logger.warning(f"Agent '{agent_id}' not found in registry")
                
                # Log failed lookup
                await logging_service.log_nest_registry_operation(
                    operation='lookup',
                    agent_id=self.agent_id,
                    status='error',
                    error_message=f"Agent '{agent_id}' not found",
                    metadata={
                        'target_agent_id': agent_id,
                        'registry_url': self.registry_url
                    }
                )
                
                return None
        
        except Exception as e:
            logger.error(f"Error looking up agent '{agent_id}': {e}", exc_info=True)
            
            # Log lookup error
            await logging_service.log_nest_registry_operation(
                operation='lookup',
                agent_id=self.agent_id,
                status='error',
                error_message=str(e),
                metadata={
                    'target_agent_id': agent_id,
                    'registry_url': self.registry_url
                }
            )
            
            return None
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about another agent.
        
        Args:
            agent_id: ID of the agent to query
            
        Returns:
            Optional[Dict]: Agent information including capabilities, metadata, etc.
        """
        try:
            logger.debug(f"Getting info for agent '{agent_id}'")
            
            response = await self._make_request(
                method="GET",
                endpoint=f"/agents/{agent_id}"
            )
            
            if response:
                logger.debug(f"Retrieved info for agent '{agent_id}'")
                return response
            else:
                logger.warning(f"Could not retrieve info for agent '{agent_id}'")
                return None
        
        except Exception as e:
            logger.error(f"Error getting info for agent '{agent_id}': {e}", exc_info=True)
            return None
    
    async def list_agents(
        self,
        capability: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all agents in the registry, optionally filtered by capability or domain.
        
        Args:
            capability: Optional capability to filter by
            domain: Optional domain to filter by
            
        Returns:
            List[Dict]: List of agent information dictionaries
        """
        try:
            logger.debug("Listing agents from registry")
            
            # Build query parameters
            params = {}
            if capability:
                params["capability"] = capability
            if domain:
                params["domain"] = domain
            
            # Build endpoint with query params
            endpoint = "/agents"
            if params:
                query_string = "&".join(f"{k}={v}" for k, v in params.items())
                endpoint = f"{endpoint}?{query_string}"
            
            response = await self._make_request(
                method="GET",
                endpoint=endpoint
            )
            
            if response and isinstance(response, list):
                logger.info(f"Retrieved {len(response)} agents from registry")
                return response
            elif response and "agents" in response:
                agents = response["agents"]
                logger.info(f"Retrieved {len(agents)} agents from registry")
                return agents
            else:
                logger.warning("No agents found in registry")
                return []
        
        except Exception as e:
            logger.error(f"Error listing agents: {e}", exc_info=True)
            return []
    
    async def deregister(self) -> bool:
        """
        Remove agent from the registry.
        
        This should be called during graceful shutdown to clean up
        the registry and prevent stale agent entries.
        
        Returns:
            bool: True if deregistration succeeded, False otherwise
        """
        try:
            if not self._registered:
                logger.debug(f"Agent '{self.agent_id}' was not registered, skipping deregistration")
                return True
            
            logger.info(f"Deregistering agent '{self.agent_id}' from registry")
            
            response = await self._make_request(
                method="DELETE",
                endpoint=f"/agents/{self.agent_id}"
            )
            
            if response or response is None:  # Some registries may return empty response
                self._registered = False
                logger.info(f"Successfully deregistered agent '{self.agent_id}'")
                
                # Log successful deregistration
                await logging_service.log_nest_registry_operation(
                    operation='deregister',
                    agent_id=self.agent_id,
                    status='success',
                    metadata={'registry_url': self.registry_url}
                )
                
                return True
            else:
                logger.warning(f"Failed to deregister agent '{self.agent_id}'")
                
                # Log failed deregistration
                await logging_service.log_nest_registry_operation(
                    operation='deregister',
                    agent_id=self.agent_id,
                    status='error',
                    error_message='Deregistration request failed',
                    metadata={'registry_url': self.registry_url}
                )
                
                return False
        
        except Exception as e:
            logger.error(f"Error deregistering agent '{self.agent_id}': {e}", exc_info=True)
            
            # Log deregistration error
            await logging_service.log_nest_registry_operation(
                operation='deregister',
                agent_id=self.agent_id,
                status='error',
                error_message=str(e),
                metadata={'registry_url': self.registry_url}
            )
            
            return False
    
    async def heartbeat(self) -> bool:
        """
        Send a heartbeat to the registry to indicate the agent is alive.
        
        This is a convenience method that calls update_status with "healthy".
        
        Returns:
            bool: True if heartbeat succeeded, False otherwise
        """
        return await self.update_status("healthy")
    
    def is_registered(self) -> bool:
        """
        Check if the agent is currently registered.
        
        Returns:
            bool: True if registered, False otherwise
        """
        return self._registered
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
