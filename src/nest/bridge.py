"""
A2A Bridge for NASDAQ Stock Agent

This module implements the A2A (Agent-to-Agent) bridge that handles
incoming stock analysis requests from other agents in the NANDA network.
It extends the NEST framework's SimpleAgentBridge to provide stock-specific
message processing capabilities.
"""

import logging
import re
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp
from aiohttp import ClientTimeout, ClientError

from src.services.investment_analysis import ComprehensiveAnalysisService
from src.models.analysis import StockAnalysis
from src.nest.query_parser import (
    extract_ticker_from_query,
    parse_query_intent,
    format_ticker_error
)
from src.nest.message_formatter import (
    format_analysis_response,
    format_error_response,
    parse_a2a_message,
    create_conversation_id
)
from src.nest.registry import RegistryClient
from src.services.logging_service import logging_service

logger = logging.getLogger(__name__)


class StockAgentBridge:
    """
    Custom A2A bridge for stock agent.
    
    This bridge handles incoming A2A messages, extracts ticker symbols,
    performs stock analysis, and formats responses for agent-to-agent
    communication.
    """
    
    def __init__(
        self,
        agent_id: str = "nasdaq-stock-agent",
        analysis_service: Optional[ComprehensiveAnalysisService] = None,
        registry_url: Optional[str] = None,
        telemetry = None,
        message_timeout: int = 30
    ):
        """
        Initialize the A2A bridge.
        
        Args:
            agent_id: Unique identifier for this agent
            analysis_service: Service for performing stock analysis
            registry_url: URL of the NANDA agent registry
            telemetry: Optional telemetry object for monitoring
            message_timeout: Timeout for outgoing messages in seconds (default: 30)
        """
        self.agent_id = agent_id
        self.analysis_service = analysis_service or ComprehensiveAnalysisService()
        self.registry_url = registry_url
        self.telemetry = telemetry
        self.message_timeout = message_timeout
        
        # Initialize registry client if registry URL is provided
        self.registry_client: Optional[RegistryClient] = None
        if registry_url:
            self.registry_client = RegistryClient(
                registry_url=registry_url,
                agent_id=agent_id
            )
        
        # HTTP session for sending messages to other agents
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Initialized StockAgentBridge for agent '{agent_id}'")
    
    async def process_stock_query(
        self,
        query: str,
        conversation_id: str,
        parent_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a stock query and return formatted A2A response.
        
        This is the main entry point for handling incoming A2A messages.
        It extracts the ticker symbol, performs analysis, and formats
        the response. If the query contains @agent-id syntax, it will
        forward the message to the specified agent.
        
        Args:
            query: Natural language query containing stock ticker or @agent-id
            conversation_id: Unique identifier for the conversation
            parent_message_id: Optional ID of the message being responded to
            
        Returns:
            Dict containing the A2A response message
            
        Examples:
            >>> bridge = StockAgentBridge()
            >>> response = await bridge.process_stock_query(
            ...     "analyze AAPL",
            ...     "conv-123",
            ...     "msg-456"
            ... )
            >>> # Or forward to another agent:
            >>> response = await bridge.process_stock_query(
            ...     "@financial-advisor Should I buy AAPL?",
            ...     "conv-123",
            ...     "msg-456"
            ... )
        """
        start_time = datetime.utcnow()
        
        # Log incoming message
        await logging_service.log_nest_message(
            message_type='stock_query',
            direction='incoming',
            agent_id=self.agent_id,
            conversation_id=conversation_id,
            message_content=query,
            status='processing'
        )
        
        # Check if the query contains @agent-id syntax
        target_agent_id, remaining_query = self.parse_agent_mention(query)
        
        if target_agent_id:
            # Forward the message to the specified agent
            logger.info(
                f"Query contains @{target_agent_id} mention, forwarding message"
            )
            
            response = await self.send_to_agent(
                target_agent_id=target_agent_id,
                message=remaining_query,
                conversation_id=conversation_id,
                parent_message_id=parent_message_id
            )
            
            # Check if forwarding failed
            if response and "error" in response:
                # Return error response in A2A format
                return format_error_response(
                    error_message=response["message"],
                    conversation_id=conversation_id,
                    parent_message_id=parent_message_id,
                    agent_id=self.agent_id,
                    error_code="AGENT_COMMUNICATION_ERROR",
                    suggestions=[
                        f"Verify that agent '{target_agent_id}' is registered and available",
                        "Try again later",
                        "Contact the agent administrator"
                    ]
                )
            
            # Return the response from the target agent
            # Add a note that this was forwarded
            if response and "content" in response:
                original_text = response["content"].get("text", "")
                response["content"]["text"] = (
                    f"[{self.agent_id}] Forwarded to @{target_agent_id}:\n\n"
                    f"{original_text}"
                )
            
            return response or format_error_response(
                error_message=f"No response received from agent '{target_agent_id}'",
                conversation_id=conversation_id,
                parent_message_id=parent_message_id,
                agent_id=self.agent_id,
                error_code="NO_RESPONSE"
            )
        
        try:
            logger.info(f"Processing stock query: '{query}' (conversation: {conversation_id})")
            
            # Parse the query to extract ticker and validate
            query_intent = parse_query_intent(query)
            
            if not query_intent['valid']:
                # Query is invalid - return error response
                error_msg = query_intent['error']
                ticker = query_intent.get('ticker')
                
                logger.warning(f"Invalid query: {error_msg}")
                
                return format_error_response(
                    error_message=format_ticker_error(ticker),
                    conversation_id=conversation_id,
                    parent_message_id=parent_message_id,
                    agent_id=self.agent_id,
                    error_code="INVALID_QUERY",
                    suggestions=[
                        "Provide a valid NASDAQ ticker symbol (e.g., AAPL, TSLA, MSFT)",
                        "Use format: 'analyze TICKER' or 'what about TICKER?'"
                    ]
                )
            
            ticker = query_intent['ticker']
            logger.info(f"Extracted ticker: {ticker}")
            
            # Perform comprehensive stock analysis
            try:
                analysis = await self.analysis_service.perform_complete_analysis(
                    ticker=ticker,
                    query_text=query
                )
                
                # Check if analysis was successful
                if not analysis.recommendation:
                    # Analysis failed or incomplete
                    logger.error(f"Analysis failed for {ticker}: No recommendation generated")
                    
                    return format_error_response(
                        error_message=f"Unable to complete analysis for {ticker}. {analysis.summary}",
                        conversation_id=conversation_id,
                        parent_message_id=parent_message_id,
                        agent_id=self.agent_id,
                        error_code="ANALYSIS_FAILED",
                        suggestions=[
                            "Verify the ticker symbol is correct",
                            "Try again in a few moments",
                            "Check if the stock is actively traded"
                        ]
                    )
                
                # Format successful analysis response
                response = format_analysis_response(
                    analysis=analysis,
                    conversation_id=conversation_id,
                    parent_message_id=parent_message_id,
                    agent_id=self.agent_id
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(
                    f"Successfully processed query for {ticker} "
                    f"(recommendation: {analysis.recommendation.recommendation.value}, "
                    f"processing time: {processing_time:.0f}ms)"
                )
                
                # Log successful message processing
                await logging_service.log_nest_message(
                    message_type='analysis_response',
                    direction='outgoing',
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    message_content=f"Analysis for {ticker}: {analysis.recommendation.recommendation.value}",
                    status='success',
                    processing_time_ms=int(processing_time),
                    metadata={
                        'ticker': ticker,
                        'recommendation': analysis.recommendation.recommendation.value,
                        'confidence_score': analysis.recommendation.confidence_score
                    }
                )
                
                return response
                
            except Exception as analysis_error:
                logger.error(f"Analysis error for {ticker}: {analysis_error}", exc_info=True)
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log failed message processing
                await logging_service.log_nest_message(
                    message_type='analysis_response',
                    direction='outgoing',
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    message_content=f"Analysis failed for {ticker}",
                    status='error',
                    error_message=str(analysis_error),
                    processing_time_ms=int(processing_time),
                    metadata={'ticker': ticker}
                )
                
                return format_error_response(
                    error_message=f"Analysis failed for {ticker}: {str(analysis_error)}",
                    conversation_id=conversation_id,
                    parent_message_id=parent_message_id,
                    agent_id=self.agent_id,
                    error_code="ANALYSIS_ERROR",
                    suggestions=[
                        "Verify the ticker symbol is valid",
                        "Try again later",
                        "Contact support if the issue persists"
                    ]
                )
        
        except Exception as e:
            logger.error(f"Unexpected error processing query: {e}", exc_info=True)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log unexpected error
            await logging_service.log_nest_message(
                message_type='stock_query',
                direction='incoming',
                agent_id=self.agent_id,
                conversation_id=conversation_id,
                message_content=query,
                status='error',
                error_message=str(e),
                processing_time_ms=int(processing_time)
            )
            
            return format_error_response(
                error_message=f"Unexpected error: {str(e)}",
                conversation_id=conversation_id,
                parent_message_id=parent_message_id,
                agent_id=self.agent_id,
                error_code="INTERNAL_ERROR",
                suggestions=["Try again later", "Contact support if the issue persists"]
            )
    
    async def handle_a2a_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming A2A message.
        
        This method parses the A2A message format and delegates to
        process_stock_query for actual processing.
        
        Args:
            message: A2A message dictionary
            
        Returns:
            Dict containing the A2A response message
        """
        try:
            # Parse the A2A message
            parsed = parse_a2a_message(message)
            
            query = parsed['query']
            conversation_id = parsed['conversation_id']
            message_id = parsed['message_id']
            from_agent_id = parsed['from_agent_id']
            
            logger.info(
                f"Received A2A message from agent '{from_agent_id}' "
                f"(conversation: {conversation_id})"
            )
            
            # Process the stock query
            response = await self.process_stock_query(
                query=query,
                conversation_id=conversation_id,
                parent_message_id=message_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling A2A message: {e}", exc_info=True)
            
            # Try to extract conversation_id for error response
            conversation_id = message.get('conversation_id', 'unknown')
            
            return format_error_response(
                error_message=f"Failed to process message: {str(e)}",
                conversation_id=conversation_id,
                agent_id=self.agent_id,
                error_code="MESSAGE_PROCESSING_ERROR"
            )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session for sending messages.
        
        Returns:
            aiohttp.ClientSession: Active session for HTTP requests
        """
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self.message_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close HTTP session and registry client."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed bridge HTTP session")
        
        if self.registry_client:
            await self.registry_client.close()
            logger.debug("Closed registry client")
    
    def parse_agent_mention(self, message: str) -> tuple[Optional[str], str]:
        """
        Parse @agent-id syntax from a message.
        
        Extracts the target agent ID from messages like:
        - "@financial-advisor Should I buy AAPL?"
        - "@risk-analyzer What's the risk for TSLA?"
        
        Args:
            message: Message text that may contain @agent-id syntax
            
        Returns:
            Tuple of (target_agent_id, remaining_message)
            If no @agent-id found, returns (None, original_message)
            
        Example:
            >>> bridge = StockAgentBridge()
            >>> agent_id, msg = bridge.parse_agent_mention("@advisor Should I buy?")
            >>> print(agent_id)  # "advisor"
            >>> print(msg)       # "Should I buy?"
        """
        # Pattern to match @agent-id at the start of the message
        pattern = r'^@([\w-]+)\s+(.+)$'
        match = re.match(pattern, message.strip())
        
        if match:
            target_agent_id = match.group(1)
            remaining_message = match.group(2)
            logger.debug(f"Parsed agent mention: @{target_agent_id}")
            return target_agent_id, remaining_message
        
        return None, message
    
    async def send_to_agent(
        self,
        target_agent_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to another agent via A2A protocol.
        
        This method:
        1. Looks up the target agent in the registry
        2. Sends an A2A message to the agent's URL
        3. Waits for and returns the response
        
        Args:
            target_agent_id: ID of the target agent
            message: Message content to send
            conversation_id: Optional conversation identifier (auto-generated if not provided)
            parent_message_id: Optional ID of the message being responded to
            metadata: Optional additional metadata to include
            
        Returns:
            Optional[Dict]: Response from the target agent, or None if failed
            
        Example:
            >>> bridge = StockAgentBridge(registry_url="http://registry:6900")
            >>> response = await bridge.send_to_agent(
            ...     target_agent_id="financial-advisor",
            ...     message="Should I buy AAPL?",
            ...     conversation_id="conv-123"
            ... )
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Sending message to agent '{target_agent_id}'")
            
            # Check if registry client is available
            if not self.registry_client:
                logger.error("Cannot send message: Registry client not initialized")
                return {
                    "error": "Registry not configured",
                    "message": "Cannot send messages to other agents without registry configuration"
                }
            
            # Look up the target agent in the registry
            logger.debug(f"Looking up agent '{target_agent_id}' in registry")
            target_url = await self.registry_client.lookup_agent(target_agent_id)
            
            if not target_url:
                logger.warning(f"Agent '{target_agent_id}' not found in registry")
                return {
                    "error": "Agent not found",
                    "message": f"Agent '{target_agent_id}' is not registered in the NANDA network"
                }
            
            logger.info(f"Found agent '{target_agent_id}' at {target_url}")
            
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = create_conversation_id()
                logger.debug(f"Generated conversation ID: {conversation_id}")
            
            # Build the A2A message
            a2a_message = {
                "role": "user",
                "content": {
                    "text": message,
                    "type": "text"
                },
                "conversation_id": conversation_id,
                "metadata": {
                    "from_agent_id": self.agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            }
            
            # Add parent message ID if provided
            if parent_message_id:
                a2a_message["parent_message_id"] = parent_message_id
            
            # Send the message to the target agent
            logger.debug(f"Sending A2A message to {target_url}")
            
            # Log outgoing message
            await logging_service.log_nest_message(
                message_type='agent_forward',
                direction='outgoing',
                agent_id=self.agent_id,
                conversation_id=conversation_id,
                message_content=message,
                target_agent_id=target_agent_id,
                status='sending'
            )
            
            try:
                session = await self._get_session()
                
                # Construct the A2A endpoint URL
                a2a_endpoint = f"{target_url.rstrip('/')}/a2a"
                
                async with session.post(a2a_endpoint, json=a2a_message) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        elapsed_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        logger.info(
                            f"Successfully received response from agent '{target_agent_id}' "
                            f"(elapsed: {elapsed_time:.0f}ms)"
                        )
                        
                        # Log successful message send
                        await logging_service.log_nest_message(
                            message_type='agent_forward',
                            direction='outgoing',
                            agent_id=self.agent_id,
                            conversation_id=conversation_id,
                            message_content=message,
                            target_agent_id=target_agent_id,
                            status='success',
                            processing_time_ms=int(elapsed_time)
                        )
                        
                        return result
                    else:
                        error_text = await response.text()
                        elapsed_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        
                        logger.error(
                            f"Agent '{target_agent_id}' returned error status {response.status}: "
                            f"{error_text}"
                        )
                        
                        # Log failed message send
                        await logging_service.log_nest_message(
                            message_type='agent_forward',
                            direction='outgoing',
                            agent_id=self.agent_id,
                            conversation_id=conversation_id,
                            message_content=message,
                            target_agent_id=target_agent_id,
                            status='error',
                            error_message=f"HTTP {response.status}: {error_text}",
                            processing_time_ms=int(elapsed_time)
                        )
                        
                        return {
                            "error": f"HTTP {response.status}",
                            "message": f"Agent returned error: {error_text}"
                        }
            
            except asyncio.TimeoutError:
                elapsed_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.error(
                    f"Timeout waiting for response from agent '{target_agent_id}' "
                    f"(timeout: {self.message_timeout}s)"
                )
                
                # Log timeout
                await logging_service.log_nest_message(
                    message_type='agent_forward',
                    direction='outgoing',
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    message_content=message,
                    target_agent_id=target_agent_id,
                    status='timeout',
                    error_message=f"Timeout after {self.message_timeout}s",
                    processing_time_ms=int(elapsed_time)
                )
                
                return {
                    "error": "Timeout",
                    "message": f"Agent '{target_agent_id}' did not respond within {self.message_timeout} seconds"
                }
            
            except ClientError as e:
                elapsed_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.error(
                    f"Connection error sending message to agent '{target_agent_id}': {e}"
                )
                
                # Log connection error
                await logging_service.log_nest_message(
                    message_type='agent_forward',
                    direction='outgoing',
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    message_content=message,
                    target_agent_id=target_agent_id,
                    status='error',
                    error_message=f"Connection error: {str(e)}",
                    processing_time_ms=int(elapsed_time)
                )
                
                return {
                    "error": "Connection error",
                    "message": f"Failed to connect to agent '{target_agent_id}': {str(e)}"
                }
        
        except Exception as e:
            logger.error(
                f"Unexpected error sending message to agent '{target_agent_id}': {e}",
                exc_info=True
            )
            
            return {
                "error": "Internal error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def get_capabilities(self) -> list[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        return [
            "stock_analysis",
            "technical_analysis",
            "fundamental_analysis",
            "investment_recommendations",
            "market_data"
        ]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the bridge and its dependencies.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Check analysis service health
            analysis_health = await self.analysis_service.get_service_health()
            
            is_healthy = analysis_health.get('overall_status') == 'healthy'
            
            health_status = {
                'bridge': 'StockAgentBridge',
                'agent_id': self.agent_id,
                'status': 'healthy' if is_healthy else 'degraded',
                'analysis_service': analysis_health,
                'registry_configured': self.registry_client is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add registry status if available
            if self.registry_client:
                health_status['registry_connected'] = self.registry_client.is_registered()
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'bridge': 'StockAgentBridge',
                'agent_id': self.agent_id,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
