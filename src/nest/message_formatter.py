"""
A2A message formatting utilities for NEST integration

This module provides utilities for formatting stock analysis results and errors
into A2A (Agent-to-Agent) message format for communication with other agents
in the NANDA network.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from src.models.analysis import StockAnalysis, InvestmentRecommendation


def format_analysis_response(
    analysis: StockAnalysis,
    conversation_id: str,
    parent_message_id: Optional[str] = None,
    agent_id: str = "nasdaq-stock-agent"
) -> Dict[str, Any]:
    """
    Format a StockAnalysis object into an A2A response message.
    
    Args:
        analysis: StockAnalysis object containing the analysis results
        conversation_id: Unique identifier for the conversation
        parent_message_id: Optional ID of the message being responded to
        agent_id: Agent identifier (default: "nasdaq-stock-agent")
    
    Returns:
        Dictionary containing the A2A response message
    
    Example:
        >>> analysis = StockAnalysis(ticker="AAPL", company_name="Apple Inc.", ...)
        >>> response = format_analysis_response(analysis, "conv-123", "msg-456")
    """
    # Build the response text
    text_parts = [f"[{agent_id}] {analysis.company_name} ({analysis.ticker}) Analysis:"]
    text_parts.append("")  # Empty line
    
    # Add market data if available
    if analysis.market_data:
        price_change = analysis.market_data.get_price_change_percentage()
        price_change_sign = "+" if price_change >= 0 else ""
        text_parts.append(
            f"Current Price: ${analysis.market_data.current_price:.2f} "
            f"({price_change_sign}{price_change:.1f}%)"
        )
    
    # Add recommendation if available
    if analysis.recommendation:
        rec = analysis.recommendation
        text_parts.append(
            f"AI Recommendation: {rec.recommendation.value.upper()} "
            f"(Confidence: {rec.confidence_score:.0f}%)"
        )
        text_parts.append("")  # Empty line
        
        # Add key factors
        if rec.key_factors:
            text_parts.append("Key Factors:")
            for factor in rec.key_factors:
                text_parts.append(f"• {factor}")
        
        text_parts.append("")  # Empty line
        text_parts.append(f"Risk Assessment: {rec.risk_assessment}")
        text_parts.append("")  # Empty line
        text_parts.append(f"Reasoning: {rec.reasoning}")
    
    # Add summary if available
    if analysis.summary:
        text_parts.append("")  # Empty line
        text_parts.append(f"Summary: {analysis.summary}")
    
    # Build the A2A response message
    response = {
        "role": "agent",
        "content": {
            "text": "\n".join(text_parts),
            "type": "text"
        },
        "conversation_id": conversation_id
    }
    
    # Add parent message ID if provided
    if parent_message_id:
        response["parent_message_id"] = parent_message_id
    
    return response


def format_error_response(
    error_message: str,
    conversation_id: str,
    parent_message_id: Optional[str] = None,
    agent_id: str = "nasdaq-stock-agent",
    error_code: Optional[str] = None,
    suggestions: Optional[list] = None
) -> Dict[str, Any]:
    """
    Format an error message into an A2A response message.
    
    Args:
        error_message: Human-readable error message
        conversation_id: Unique identifier for the conversation
        parent_message_id: Optional ID of the message being responded to
        agent_id: Agent identifier (default: "nasdaq-stock-agent")
        error_code: Optional error code for categorization
        suggestions: Optional list of suggestions to help resolve the error
    
    Returns:
        Dictionary containing the A2A error response message
    
    Example:
        >>> response = format_error_response(
        ...     "Invalid ticker symbol",
        ...     "conv-123",
        ...     error_code="INVALID_TICKER",
        ...     suggestions=["Please provide a valid NASDAQ ticker symbol"]
        ... )
    """
    # Build the error text
    text_parts = [f"[{agent_id}] ❌ Error: {error_message}"]
    
    # Add error code if provided
    if error_code:
        text_parts.append(f"Error Code: {error_code}")
    
    # Add suggestions if provided
    if suggestions:
        text_parts.append("")  # Empty line
        text_parts.append("Suggestions:")
        for suggestion in suggestions:
            text_parts.append(f"• {suggestion}")
    
    # Build the A2A response message
    response = {
        "role": "agent",
        "content": {
            "text": "\n".join(text_parts),
            "type": "text"
        },
        "conversation_id": conversation_id
    }
    
    # Add parent message ID if provided
    if parent_message_id:
        response["parent_message_id"] = parent_message_id
    
    return response


def parse_a2a_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse an incoming A2A message and extract relevant information.
    
    Args:
        message: A2A message dictionary
    
    Returns:
        Dictionary containing parsed message information:
        - query: The text content of the message
        - conversation_id: Conversation identifier
        - message_id: Message identifier (if available)
        - from_agent_id: Source agent identifier (if available)
        - metadata: Additional metadata (if available)
    
    Example:
        >>> message = {
        ...     "content": {"text": "Analyze AAPL"},
        ...     "conversation_id": "conv-123",
        ...     "message_id": "msg-456"
        ... }
        >>> parsed = parse_a2a_message(message)
        >>> print(parsed["query"])
        "Analyze AAPL"
    """
    parsed = {
        "query": "",
        "conversation_id": "",
        "message_id": None,
        "from_agent_id": None,
        "metadata": {}
    }
    
    # Extract content
    if "content" in message:
        content = message["content"]
        if isinstance(content, dict):
            parsed["query"] = content.get("text", "")
        elif isinstance(content, str):
            parsed["query"] = content
    
    # Extract conversation ID
    parsed["conversation_id"] = message.get("conversation_id", "")
    
    # Extract message ID
    parsed["message_id"] = message.get("message_id") or message.get("id")
    
    # Extract metadata
    if "metadata" in message:
        metadata = message["metadata"]
        parsed["metadata"] = metadata
        parsed["from_agent_id"] = metadata.get("from_agent_id")
    
    return parsed


def create_conversation_id() -> str:
    """
    Create a unique conversation ID for tracking conversations.
    
    Returns:
        String containing a unique conversation identifier
    
    Example:
        >>> conv_id = create_conversation_id()
        >>> print(conv_id)
        "conv-20241112-103045-abc123"
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return f"conv-{timestamp}-{unique_id}"
