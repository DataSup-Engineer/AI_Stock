"""
Integration tests for NEST framework integration.

This test suite validates:
- A2A message processing with sample queries
- Registry registration and lookup
- Agent-to-agent communication
- Standalone mode compatibility
- Error handling for various failure scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import aiohttp

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from src.nest.adapter import StockAgentNEST
from src.nest.bridge import StockAgentBridge
from src.nest.registry import RegistryClient
from src.nest.config import NESTConfig
from src.nest.query_parser import extract_ticker_from_query, parse_query_intent
from src.nest.message_formatter import format_analysis_response, format_error_response
from src.models.analysis import StockAnalysis, InvestmentRecommendation, RecommendationType


class TestA2AMessageProcessing:
    """Test A2A message processing with sample queries."""
    
    @pytest.mark.asyncio
    async def test_process_simple_stock_query(self):
        """Test processing a simple stock query via A2A."""
        # Create bridge with mocked analysis service
        mock_analysis_service = AsyncMock()
        
        # Create mock analysis result
        mock_recommendation = InvestmentRecommendation(
            recommendation=RecommendationType.BUY,
            confidence_score=85.0,
            reasoning="Strong technical and fundamental indicators",
            key_factors=["Strong momentum", "Positive technicals"],
            risk_assessment="Low risk"
        )
        
        mock_analysis = StockAnalysis(
            ticker="AAPL",
            company_name="Apple Inc.",
            recommendation=mock_recommendation,
            summary="Positive outlook with strong momentum"
        )
        
        mock_analysis_service.perform_complete_analysis = AsyncMock(return_value=mock_analysis)
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Process query
        response = await bridge.process_stock_query(
            query="What's the analysis for AAPL?",
            conversation_id="test-conv-123"
        )
        
        # Verify response structure
        assert response is not None
        assert "content" in response
        assert "text" in response["content"]
        assert "AAPL" in response["content"]["text"]
        assert "conversation_id" in response
        assert response["conversation_id"] == "test-conv-123"
        
        # Verify analysis service was called
        mock_analysis_service.perform_complete_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_natural_language_query(self):
        """Test processing natural language queries."""
        mock_analysis_service = AsyncMock()
        
        mock_recommendation = InvestmentRecommendation(
            recommendation=RecommendationType.HOLD,
            confidence_score=70.0,
            reasoning="Mixed signals",
            key_factors=["Neutral momentum", "Mixed indicators"],
            risk_assessment="Medium risk"
        )
        
        mock_analysis = StockAnalysis(
            ticker="TSLA",
            company_name="Tesla Inc.",
            recommendation=mock_recommendation,
            summary="Neutral outlook"
        )
        
        mock_analysis_service.perform_complete_analysis = AsyncMock(return_value=mock_analysis)
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Test various natural language formats
        queries = [
            "analyze TSLA",
            "what about TSLA?",
            "tell me about TSLA stock",
            "TSLA analysis please"
        ]
        
        for query in queries:
            response = await bridge.process_stock_query(
                query=query,
                conversation_id=f"test-conv-{query[:4]}"
            )
            
            assert response is not None
            assert "content" in response
            assert "TSLA" in response["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_process_invalid_ticker_query(self):
        """Test handling of invalid ticker symbols."""
        mock_analysis_service = AsyncMock()
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Process query with invalid ticker
        response = await bridge.process_stock_query(
            query="analyze INVALID123",
            conversation_id="test-conv-invalid"
        )
        
        # Verify error response
        assert response is not None
        assert "content" in response
        assert "error" in response["content"]["text"].lower() or "invalid" in response["content"]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_process_query_without_ticker(self):
        """Test handling of queries without ticker symbols."""
        mock_analysis_service = AsyncMock()
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Process query without ticker
        response = await bridge.process_stock_query(
            query="What's the market doing today?",
            conversation_id="test-conv-no-ticker"
        )
        
        # Verify error response
        assert response is not None
        assert "content" in response
        text = response["content"]["text"].lower()
        assert "error" in text or "invalid" in text or "ticker" in text


class TestRegistryIntegration:
    """Test registry registration and lookup functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test successful agent registration with registry."""
        # Mock aiohttp session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "registered"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://test-registry:6900",
                agent_id="test-agent"
            )
            
            # Register agent
            success = await client.register_agent(
                agent_url="http://test-agent:6000",
                capabilities=["stock_analysis", "technical_analysis"],
                metadata={
                    "agent_name": "Test Stock Agent",
                    "domain": "financial analysis"
                }
            )
            
            assert success is True
            assert client.is_registered() is True
    
    @pytest.mark.asyncio
    async def test_agent_lookup(self):
        """Test looking up another agent in the registry."""
        # Mock aiohttp session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "agent_id": "financial-advisor",
            "agent_url": "http://advisor:6000"
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://test-registry:6900",
                agent_id="test-agent"
            )
            
            # Lookup agent
            agent_url = await client.lookup_agent("financial-advisor")
            
            assert agent_url == "http://advisor:6000"
    
    @pytest.mark.asyncio
    async def test_agent_lookup_not_found(self):
        """Test looking up a non-existent agent."""
        # Mock aiohttp session
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Agent not found")
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://test-registry:6900",
                agent_id="test-agent"
            )
            
            # Lookup non-existent agent
            agent_url = await client.lookup_agent("non-existent-agent")
            
            assert agent_url is None
    
    @pytest.mark.asyncio
    async def test_status_update(self):
        """Test updating agent status in registry."""
        # Mock aiohttp session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "updated"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://test-registry:6900",
                agent_id="test-agent"
            )
            
            # Update status
            success = await client.update_status("healthy")
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_deregistration(self):
        """Test agent deregistration from registry."""
        # Mock aiohttp session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "deregistered"})
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://test-registry:6900",
                agent_id="test-agent"
            )
            
            # Mark as registered first
            client._registered = True
            
            # Deregister
            success = await client.deregister()
            
            assert success is True
            assert client.is_registered() is False


class TestAgentToAgentCommunication:
    """Test agent-to-agent communication functionality."""
    
    @pytest.mark.asyncio
    async def test_send_message_to_agent(self):
        """Test sending a message to another agent."""
        # Mock registry client
        mock_registry = AsyncMock()
        mock_registry.lookup_agent = AsyncMock(return_value="http://target-agent:6000")
        
        # Mock HTTP response from target agent
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "role": "agent",
            "content": {"text": "Response from target agent", "type": "text"},
            "conversation_id": "test-conv"
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            registry_url="http://test-registry:6900"
        )
        bridge.registry_client = mock_registry
        bridge._session = mock_session
        
        # Send message
        response = await bridge.send_to_agent(
            target_agent_id="target-agent",
            message="Test message",
            conversation_id="test-conv"
        )
        
        assert response is not None
        assert "content" in response
        assert response["content"]["text"] == "Response from target agent"
        
        # Verify registry lookup was called
        mock_registry.lookup_agent.assert_called_once_with("target-agent")
    
    @pytest.mark.asyncio
    async def test_send_message_agent_not_found(self):
        """Test sending message when target agent is not found."""
        # Mock registry client
        mock_registry = AsyncMock()
        mock_registry.lookup_agent = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.closed = False
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            registry_url="http://test-registry:6900"
        )
        bridge.registry_client = mock_registry
        bridge._session = mock_session
        
        # Send message to non-existent agent
        response = await bridge.send_to_agent(
            target_agent_id="non-existent-agent",
            message="Test message",
            conversation_id="test-conv"
        )
        
        assert response is not None
        assert "error" in response
        assert ("not found" in response["message"].lower() or "not registered" in response["message"].lower())
    
    @pytest.mark.asyncio
    async def test_parse_agent_mention(self):
        """Test parsing @agent-id syntax from messages."""
        bridge = StockAgentBridge(agent_id="test-agent")
        
        # Test valid mention
        agent_id, remaining = bridge.parse_agent_mention("@financial-advisor Should I buy AAPL?")
        assert agent_id == "financial-advisor"
        assert remaining == "Should I buy AAPL?"
        
        # Test no mention
        agent_id, remaining = bridge.parse_agent_mention("What about AAPL?")
        assert agent_id is None
        assert remaining == "What about AAPL?"
    
    @pytest.mark.asyncio
    async def test_forward_message_to_agent(self):
        """Test forwarding a message with @agent-id syntax."""
        # Mock registry and HTTP session
        mock_registry = AsyncMock()
        mock_registry.lookup_agent = AsyncMock(return_value="http://advisor:6000")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "role": "agent",
            "content": {"text": "Buy recommendation", "type": "text"},
            "conversation_id": "test-conv"
        })
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.closed = False
        
        mock_analysis_service = AsyncMock()
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service,
            registry_url="http://test-registry:6900"
        )
        bridge.registry_client = mock_registry
        bridge._session = mock_session
        
        # Process query with @mention
        response = await bridge.process_stock_query(
            query="@financial-advisor Should I buy AAPL?",
            conversation_id="test-conv"
        )
        
        assert response is not None
        assert "content" in response
        assert "financial-advisor" in response["content"]["text"]


class TestStandaloneMode:
    """Test that standalone mode still works without NEST."""
    
    def test_config_standalone_mode(self):
        """Test configuration in standalone mode."""
        config = NESTConfig(enable_nest=False)
        
        assert config.enable_nest is False
        assert config.should_enable_nest() is False
    
    def test_config_validation_disabled(self):
        """Test that validation passes when NEST is disabled."""
        config = NESTConfig(
            enable_nest=False,
            agent_id="",  # Invalid but should be ignored
            nest_port=0   # Invalid but should be ignored
        )
        
        is_valid, errors = config.validate()
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_adapter_not_required_in_standalone(self):
        """Test that NEST adapter is not required in standalone mode."""
        config = NESTConfig(enable_nest=False)
        
        # Should be able to use the application without NEST adapter
        assert config.should_enable_nest() is False


class TestErrorHandling:
    """Test error handling for various failure scenarios."""
    
    @pytest.mark.asyncio
    async def test_analysis_service_failure(self):
        """Test handling of analysis service failures."""
        # Mock analysis service that raises an exception
        mock_analysis_service = AsyncMock()
        mock_analysis_service.perform_complete_analysis = AsyncMock(
            side_effect=Exception("Market data unavailable")
        )
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Process query
        response = await bridge.process_stock_query(
            query="analyze AAPL",
            conversation_id="test-conv-error"
        )
        
        # Verify error response
        assert response is not None
        assert "content" in response
        assert "error" in response["content"]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_registry_connection_failure(self):
        """Test handling of registry connection failures."""
        # Mock aiohttp session that raises connection error
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(side_effect=aiohttp.ClientError("Connection refused"))
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://unreachable-registry:6900",
                agent_id="test-agent"
            )
            
            # Try to register
            success = await client.register_agent(
                agent_url="http://test-agent:6000",
                capabilities=["stock_analysis"],
                metadata={"agent_name": "Test Agent"}
            )
            
            # Should fail gracefully
            assert success is False
    
    @pytest.mark.asyncio
    async def test_registry_timeout(self):
        """Test handling of registry timeouts."""
        # Mock aiohttp session that times out
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_session.closed = False
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            client = RegistryClient(
                registry_url="http://slow-registry:6900",
                agent_id="test-agent",
                max_retries=1  # Reduce retries for faster test
            )
            
            # Try to register
            success = await client.register_agent(
                agent_url="http://test-agent:6000",
                capabilities=["stock_analysis"],
                metadata={"agent_name": "Test Agent"}
            )
            
            # Should fail gracefully after retries
            assert success is False
    
    @pytest.mark.asyncio
    async def test_agent_communication_timeout(self):
        """Test handling of agent communication timeouts."""
        # Mock registry client
        mock_registry = AsyncMock()
        mock_registry.lookup_agent = AsyncMock(return_value="http://slow-agent:6000")
        
        # Mock response that times out
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            registry_url="http://test-registry:6900",
            message_timeout=1  # Short timeout for test
        )
        bridge.registry_client = mock_registry
        bridge._session = mock_session
        
        # Send message
        response = await bridge.send_to_agent(
            target_agent_id="slow-agent",
            message="Test message",
            conversation_id="test-conv"
        )
        
        # Should return timeout or error
        assert response is not None
        assert "error" in response
        # Accept timeout, did not respond, or error messages (all are valid error responses)
        message_lower = response["message"].lower()
        assert ("timeout" in message_lower or "did not respond" in message_lower or "error" in message_lower)
    
    @pytest.mark.asyncio
    async def test_invalid_a2a_message_format(self):
        """Test handling of invalid A2A message formats."""
        mock_analysis_service = AsyncMock()
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Test with invalid message format
        invalid_message = {
            "invalid_field": "test"
        }
        
        response = await bridge.handle_a2a_message(invalid_message)
        
        # Should return error response
        assert response is not None
        assert "content" in response
    
    def test_config_validation_errors(self):
        """Test configuration validation with invalid values."""
        config = NESTConfig(
            enable_nest=True,
            agent_id="",  # Invalid: empty
            nest_port=99999,  # Invalid: out of range
            capabilities=[]  # Invalid: no capabilities
        )
        
        is_valid, errors = config.validate()
        
        assert is_valid is False
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_incomplete_analysis_result(self):
        """Test handling of incomplete analysis results."""
        # Mock analysis service that returns incomplete analysis
        mock_analysis_service = AsyncMock()
        
        incomplete_analysis = StockAnalysis(
            ticker="AAPL",
            company_name="Apple Inc.",
            recommendation=None,  # Missing recommendation
            summary="Incomplete analysis"
        )
        
        mock_analysis_service.perform_complete_analysis = AsyncMock(
            return_value=incomplete_analysis
        )
        
        bridge = StockAgentBridge(
            agent_id="test-agent",
            analysis_service=mock_analysis_service
        )
        
        # Process query
        response = await bridge.process_stock_query(
            query="analyze AAPL",
            conversation_id="test-conv-incomplete"
        )
        
        # Should return error response
        assert response is not None
        assert "content" in response
        text = response["content"]["text"].lower()
        assert "error" in text or "unable" in text


class TestNESTAdapter:
    """Test NEST adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """Test NEST adapter initialization."""
        config = NESTConfig(
            agent_id="test-agent",
            nest_port=6000,
            enable_nest=True
        )
        
        adapter = StockAgentNEST(config=config)
        
        assert adapter.agent_id == "test-agent"
        assert adapter.port == 6000
        assert adapter.is_running() is False
    
    @pytest.mark.asyncio
    async def test_adapter_agent_logic(self):
        """Test adapter's agent_logic method."""
        config = NESTConfig(
            agent_id="test-agent",
            enable_nest=True
        )
        
        # Mock the bridge's process_stock_query method
        adapter = StockAgentNEST(config=config)
        
        mock_response = {
            "role": "agent",
            "content": {"text": "Analysis result", "type": "text"},
            "conversation_id": "test-conv"
        }
        
        adapter.bridge.process_stock_query = AsyncMock(return_value=mock_response)
        
        # Call agent_logic
        response = await adapter.agent_logic(
            message="analyze AAPL",
            conversation_id="test-conv"
        )
        
        assert response is not None
        assert "Analysis result" in response
    
    @pytest.mark.asyncio
    async def test_adapter_get_status(self):
        """Test getting adapter status."""
        config = NESTConfig(
            agent_id="test-agent",
            enable_nest=True
        )
        
        adapter = StockAgentNEST(config=config)
        
        # Mock bridge health status
        adapter.bridge.get_health_status = AsyncMock(return_value={
            "status": "healthy",
            "analysis_service": {"status": "healthy"}
        })
        
        status = await adapter.get_status()
        
        assert status is not None
        assert "agent_id" in status
        assert status["agent_id"] == "test-agent"
        assert "status" in status
        assert "bridge_health" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
