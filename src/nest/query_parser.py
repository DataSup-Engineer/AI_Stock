"""
Query Parser for NEST Integration

This module handles parsing of natural language queries to extract ticker symbols
and validate them for stock analysis requests.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_ticker_from_query(query: str) -> Optional[str]:
    """
    Extract ticker symbol from natural language query.
    
    Supports multiple query formats:
    - Direct ticker: "AAPL", "TSLA", "MSFT"
    - Analyze format: "analyze AAPL", "analyze Apple"
    - Question format: "what about AAPL?", "how is TSLA doing?"
    - Information format: "tell me about MSFT", "give me info on GOOGL"
    
    Args:
        query: Natural language query string
        
    Returns:
        Optional[str]: Extracted ticker symbol in uppercase, or None if not found
        
    Examples:
        >>> extract_ticker_from_query("AAPL")
        'AAPL'
        >>> extract_ticker_from_query("analyze TSLA")
        'TSLA'
        >>> extract_ticker_from_query("what about MSFT?")
        'MSFT'
        >>> extract_ticker_from_query("tell me about GOOGL")
        'GOOGL'
    """
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid query input: {query}")
        return None
    
    # Clean and normalize the query
    query = query.strip()
    
    # Pattern 1: Direct ticker (1-5 uppercase letters, possibly with $ prefix)
    # Examples: "AAPL", "$AAPL", "TSLA"
    direct_pattern = r'^\$?([A-Z]{1,5})$'
    match = re.match(direct_pattern, query)
    if match:
        ticker = match.group(1).upper()
        logger.debug(f"Extracted ticker '{ticker}' using direct pattern")
        return ticker
    
    # Pattern 2: Analyze/check format
    # Examples: "analyze AAPL", "check TSLA", "look at MSFT"
    analyze_pattern = r'(?:analyze|check|look\s+at|review)\s+\$?([A-Z]{1,5})\b'
    match = re.search(analyze_pattern, query, re.IGNORECASE)
    if match:
        ticker = match.group(1).upper()
        logger.debug(f"Extracted ticker '{ticker}' using analyze pattern")
        return ticker
    
    # Pattern 3: Question format
    # Examples: "what about AAPL?", "how is TSLA doing?", "what's MSFT?"
    question_pattern = r'(?:what|how)(?:\s+is|\s+about|\'s)?\s+\$?([A-Z]{1,5})\b'
    match = re.search(question_pattern, query, re.IGNORECASE)
    if match:
        ticker = match.group(1).upper()
        logger.debug(f"Extracted ticker '{ticker}' using question pattern")
        return ticker
    
    # Pattern 4: Information request format
    # Examples: "tell me about AAPL", "give me info on TSLA", "show me MSFT"
    info_pattern = r'(?:tell\s+me\s+about|give\s+me\s+info\s+on|show\s+me|info\s+on)\s+\$?([A-Z]{1,5})\b'
    match = re.search(info_pattern, query, re.IGNORECASE)
    if match:
        ticker = match.group(1).upper()
        logger.debug(f"Extracted ticker '{ticker}' using info pattern")
        return ticker
    
    # Pattern 5: Generic ticker extraction (fallback)
    # Look for any 1-5 uppercase letter sequence that might be a ticker
    # Examples: "I want to know about AAPL", "Can you analyze TSLA for me?"
    generic_pattern = r'\b\$?([A-Z]{1,5})\b'
    matches = re.findall(generic_pattern, query)
    
    if matches:
        # Filter out common English words that might match the pattern
        common_words = {
            'I', 'A', 'AN', 'THE', 'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN',
            'HAVE', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL', 'WOULD', 'CAN',
            'COULD', 'MAY', 'MIGHT', 'MUST', 'SHALL', 'SHOULD', 'AM', 'OR',
            'AND', 'BUT', 'IF', 'SO', 'AS', 'AT', 'BY', 'FOR', 'IN', 'OF',
            'ON', 'TO', 'UP', 'IT', 'ME', 'MY', 'WE', 'US', 'YOU', 'HE', 'SHE',
            'HELLO', 'HI', 'THANKS', 'THANK', 'PLEASE', 'YES', 'NO', 'OK', 'OKAY'
        }
        
        # Find the first match that's not a common word
        for match in matches:
            ticker = match.upper()
            if ticker not in common_words and is_valid_ticker(ticker):
                logger.debug(f"Extracted ticker '{ticker}' using generic pattern")
                return ticker
    
    logger.warning(f"Could not extract ticker from query: '{query}'")
    return None


def is_valid_ticker(ticker: str) -> bool:
    """
    Validate if a string is a valid ticker symbol.
    
    A valid ticker symbol:
    - Contains 1-5 uppercase letters
    - May contain numbers (but not as the first character)
    - No special characters except hyphens in some cases
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        bool: True if valid ticker format, False otherwise
        
    Examples:
        >>> is_valid_ticker("AAPL")
        True
        >>> is_valid_ticker("TSLA")
        True
        >>> is_valid_ticker("BRK.B")
        True
        >>> is_valid_ticker("A")
        True
        >>> is_valid_ticker("TOOLONG")
        False
        >>> is_valid_ticker("123")
        False
        >>> is_valid_ticker("")
        False
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    ticker = ticker.strip().upper()
    
    # Check length (1-5 characters for most tickers)
    if len(ticker) < 1 or len(ticker) > 5:
        return False
    
    # Basic pattern: starts with letter, may contain letters, numbers, or dots
    # Examples: AAPL, BRK.B, GOOG
    pattern = r'^[A-Z][A-Z0-9.]{0,4}$'
    
    if not re.match(pattern, ticker):
        return False
    
    # Additional validation: ticker shouldn't be all numbers
    if ticker.replace('.', '').isdigit():
        return False
    
    return True


def parse_query_intent(query: str) -> dict:
    """
    Parse query to determine intent and extract relevant information.
    
    Args:
        query: Natural language query string
        
    Returns:
        dict: Dictionary containing:
            - ticker: Extracted ticker symbol (or None)
            - intent: Query intent (analyze, compare, etc.)
            - valid: Whether the query is valid for processing
            - error: Error message if invalid
            
    Examples:
        >>> parse_query_intent("analyze AAPL")
        {'ticker': 'AAPL', 'intent': 'analyze', 'valid': True, 'error': None}
        >>> parse_query_intent("what about TSLA?")
        {'ticker': 'TSLA', 'intent': 'analyze', 'valid': True, 'error': None}
        >>> parse_query_intent("hello")
        {'ticker': None, 'intent': 'unknown', 'valid': False, 'error': 'No ticker symbol found'}
    """
    result = {
        'ticker': None,
        'intent': 'analyze',  # Default intent
        'valid': False,
        'error': None
    }
    
    if not query or not isinstance(query, str):
        result['error'] = 'Invalid query input'
        return result
    
    # Extract ticker
    ticker = extract_ticker_from_query(query)
    
    if not ticker:
        result['error'] = 'No ticker symbol found in query'
        result['intent'] = 'unknown'
        return result
    
    # Validate ticker
    if not is_valid_ticker(ticker):
        result['error'] = f'Invalid ticker symbol: {ticker}'
        result['ticker'] = ticker
        return result
    
    # Ticker is valid
    result['ticker'] = ticker
    result['valid'] = True
    
    # Determine intent (for now, all valid queries are analysis requests)
    # Future enhancement: support compare, historical, etc.
    result['intent'] = 'analyze'
    
    logger.info(f"Parsed query intent: ticker={ticker}, intent={result['intent']}")
    
    return result


def format_ticker_error(ticker: Optional[str] = None) -> str:
    """
    Format error message for invalid or missing ticker.
    
    Args:
        ticker: The invalid ticker symbol (if any)
        
    Returns:
        str: Formatted error message
    """
    if ticker:
        return (
            f"❌ Invalid ticker symbol '{ticker}'. "
            f"Please provide a valid NASDAQ ticker symbol (1-5 letters)."
        )
    else:
        return (
            "❌ No ticker symbol found in your query. "
            "Please include a valid NASDAQ ticker symbol (e.g., AAPL, TSLA, MSFT)."
        )
