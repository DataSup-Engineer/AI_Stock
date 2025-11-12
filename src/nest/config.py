"""
NEST Configuration Management

This module handles configuration for NEST framework integration,
including environment variable loading, validation, and fallback logic.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class NESTConfig:
    """
    NEST integration configuration.
    
    Loads configuration from environment variables and provides
    validation and fallback to standalone mode when NEST is disabled.
    """
    
    # Agent Identity
    agent_id: str = "nasdaq-stock-agent"
    agent_name: str = "NASDAQ Stock Agent"
    domain: str = "financial analysis"
    specialization: str = "NASDAQ stock analysis and investment recommendations"
    
    # Network Configuration
    nest_port: int = 6000
    public_url: Optional[str] = None
    registry_url: Optional[str] = None
    mcp_registry_url: Optional[str] = None
    
    # Feature Flags
    enable_nest: bool = False
    enable_telemetry: bool = True
    enable_dual_mode: bool = False
    
    # Agent Metadata
    version: str = "1.0.0"
    capabilities: list[str] = field(default_factory=lambda: [
        "stock_analysis",
        "technical_analysis",
        "fundamental_analysis",
        "investment_recommendations",
        "market_data"
    ])
    description: str = "AI-powered stock analysis agent providing comprehensive investment analysis for NASDAQ stocks"
    expertise: list[str] = field(default_factory=lambda: [
        "NASDAQ stock analysis",
        "Technical indicators (RSI, MACD, Moving Averages)",
        "Fundamental analysis (P/E, EPS, Revenue)",
        "Market sentiment analysis",
        "Investment recommendations (BUY, SELL, HOLD)",
        "Risk assessment",
        "Portfolio optimization"
    ])
    
    # AI Model Configuration
    anthropic_api_key: Optional[str] = None
    model: str = "claude-3-sonnet-20240229"
    system_prompt: str = (
        "You are an expert NASDAQ stock analysis agent. Your role is to provide comprehensive, "
        "data-driven investment analysis and recommendations for NASDAQ-listed stocks. "
        "You analyze technical indicators, fundamental metrics, market trends, and sentiment "
        "to deliver actionable insights. Always provide clear reasoning for your recommendations "
        "and consider both opportunities and risks. When communicating with other agents, "
        "be concise and focus on key insights relevant to their queries."
    )
    
    @classmethod
    def from_env(cls) -> 'NESTConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            NESTConfig: Configuration object with values from environment
            
        Environment Variables:
            NEST_ENABLED: Enable/disable NEST integration (default: false)
            NEST_AGENT_ID: Unique agent identifier (default: "nasdaq-stock-agent")
            NEST_AGENT_NAME: Display name (default: "NASDAQ Stock Agent")
            NEST_PORT: A2A server port (default: 6000)
            NEST_PUBLIC_URL: Public URL for registration
            NEST_REGISTRY_URL: NANDA registry URL
            NEST_MCP_REGISTRY_URL: MCP registry URL (optional)
            NEST_TELEMETRY: Enable telemetry (default: true)
            NEST_DUAL_MODE: Run both FastAPI and A2A servers (default: false)
            ANTHROPIC_API_KEY: Anthropic API key for AI model
            ANTHROPIC_MODEL: AI model to use (default: claude-3-sonnet-20240229)
            NEST_SYSTEM_PROMPT: Custom system prompt for the agent
        """
        config = cls()
        
        # Feature flags
        config.enable_nest = cls._parse_bool(os.getenv("NEST_ENABLED", "false"))
        config.enable_telemetry = cls._parse_bool(os.getenv("NEST_TELEMETRY", "true"))
        config.enable_dual_mode = cls._parse_bool(os.getenv("NEST_DUAL_MODE", "false"))
        
        # Agent identity
        config.agent_id = os.getenv("NEST_AGENT_ID", config.agent_id)
        config.agent_name = os.getenv("NEST_AGENT_NAME", config.agent_name)
        config.domain = os.getenv("NEST_DOMAIN", config.domain)
        config.specialization = os.getenv("NEST_SPECIALIZATION", config.specialization)
        
        # Network configuration
        config.nest_port = int(os.getenv("NEST_PORT", str(config.nest_port)))
        config.public_url = os.getenv("NEST_PUBLIC_URL")
        config.registry_url = os.getenv("NEST_REGISTRY_URL")
        config.mcp_registry_url = os.getenv("NEST_MCP_REGISTRY_URL")
        
        # Optional metadata overrides
        config.version = os.getenv("NEST_VERSION", config.version)
        config.description = os.getenv("NEST_DESCRIPTION", config.description)
        
        # Parse capabilities if provided
        capabilities_str = os.getenv("NEST_CAPABILITIES")
        if capabilities_str:
            config.capabilities = [cap.strip() for cap in capabilities_str.split(",")]
        
        # Parse expertise if provided
        expertise_str = os.getenv("NEST_EXPERTISE")
        if expertise_str:
            config.expertise = [exp.strip() for exp in expertise_str.split(",")]
        
        # AI Model configuration
        config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        config.model = os.getenv("ANTHROPIC_MODEL", config.model)
        
        # System prompt override
        system_prompt_override = os.getenv("NEST_SYSTEM_PROMPT")
        if system_prompt_override:
            config.system_prompt = system_prompt_override
        
        return config
    
    @staticmethod
    def _parse_bool(value: str) -> bool:
        """
        Parse boolean value from string.
        
        Args:
            value: String value to parse
            
        Returns:
            bool: Parsed boolean value
        """
        return value.lower() in ("true", "1", "yes", "on")
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration and return validation results.
        
        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []
        
        # If NEST is disabled, no validation needed
        if not self.enable_nest:
            logger.info("NEST integration is disabled - running in standalone mode")
            return True, []
        
        # Validate required fields when NEST is enabled
        if not self.agent_id:
            errors.append("NEST_AGENT_ID is required when NEST is enabled")
        
        if not self.agent_name:
            errors.append("NEST_AGENT_NAME is required when NEST is enabled")
        
        if self.nest_port <= 0 or self.nest_port > 65535:
            errors.append(f"NEST_PORT must be between 1 and 65535, got {self.nest_port}")
        
        # Warn about optional fields
        if not self.public_url:
            logger.warning("NEST_PUBLIC_URL not set - agent may not be accessible externally")
        
        if not self.registry_url:
            logger.warning("NEST_REGISTRY_URL not set - agent will not register with registry")
        
        # Validate capabilities
        if not self.capabilities:
            errors.append("Agent must have at least one capability")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"NEST configuration validated successfully for agent '{self.agent_id}'")
        else:
            logger.error(f"NEST configuration validation failed: {', '.join(errors)}")
        
        return is_valid, errors
    
    def should_enable_nest(self) -> bool:
        """
        Determine if NEST should be enabled based on configuration.
        
        Returns:
            bool: True if NEST should be enabled, False for standalone mode
        """
        if not self.enable_nest:
            logger.info("NEST is disabled via configuration - using standalone mode")
            return False
        
        is_valid, errors = self.validate()
        
        if not is_valid:
            logger.warning(
                f"NEST configuration is invalid, falling back to standalone mode. "
                f"Errors: {', '.join(errors)}"
            )
            return False
        
        return True
    
    def get_agent_metadata(self) -> dict:
        """
        Get agent metadata for registry registration and agent-to-agent communication.
        
        Returns:
            dict: Complete agent metadata dictionary with all required fields
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "specialization": self.specialization,
            "description": self.description,
            "expertise": self.expertise,
            "registry_url": self.registry_url,
            "mcp_registry_url": self.mcp_registry_url,
            "public_url": self.public_url or f"http://localhost:{self.nest_port}",
            "system_prompt": self.system_prompt,
            "anthropic_api_key": self.anthropic_api_key,
            "model": self.model,
            "capabilities": self.capabilities,
            "version": self.version,
            "status": "healthy",
            "port": self.nest_port
        }
    
    def get_agent_config_for_communication(self) -> dict:
        """
        Get agent configuration optimized for agent-to-agent communication.
        This excludes sensitive information like API keys.
        
        Returns:
            dict: Agent configuration for sharing with other agents
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "specialization": self.specialization,
            "description": self.description,
            "expertise": self.expertise,
            "public_url": self.public_url or f"http://localhost:{self.nest_port}",
            "capabilities": self.capabilities,
            "model": self.model,
            "version": self.version
        }
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"NESTConfig("
            f"agent_id='{self.agent_id}', "
            f"enable_nest={self.enable_nest}, "
            f"nest_port={self.nest_port}, "
            f"registry_url='{self.registry_url}', "
            f"public_url='{self.public_url}'"
            f")"
        )
