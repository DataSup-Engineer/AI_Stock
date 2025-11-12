"""
NEST Integration Module

This module provides integration with the NEST (NANDA Sandbox and Testbed)
framework for agent-to-agent communication.
"""

from src.nest.adapter import StockAgentNEST
from src.nest.bridge import StockAgentBridge
from src.nest.config import NESTConfig
from src.nest.registry import RegistryClient

__all__ = [
    'StockAgentNEST',
    'StockAgentBridge',
    'NESTConfig',
    'RegistryClient'
]
