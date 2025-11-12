# Implementation Plan

- [x] 1. Set up NEST framework dependencies and project structure
  - Install python-a2a package and NEST framework dependencies
  - Create src/nest/ directory structure for NEST integration modules
  - Add NEST configuration to requirements.txt
  - _Requirements: 1.1, 5.1, 5.2_

- [x] 2. Implement NEST configuration management
  - Create src/nest/config.py with NESTConfig class
  - Implement environment variable loading for NEST settings
  - Add validation for required configuration fields
  - Implement fallback to standalone mode when NEST is disabled
  - _Requirements: 5.1, 5.2, 5.3, 6.1_

- [x] 3. Implement ticker extraction and query parsing
  - Create src/nest/query_parser.py module
  - Implement extract_ticker_from_query() function to parse natural language
  - Support multiple query formats (direct ticker, "analyze X", "what about X")
  - Add validation for ticker symbols
  - _Requirements: 3.1, 3.3_

- [x] 4. Implement A2A message formatting utilities
  - Create src/nest/message_formatter.py module
  - Implement format_analysis_response() to convert StockAnalysis to A2A format
  - Implement format_error_response() for error messages
  - Add support for conversation tracking
  - _Requirements: 3.3, 3.4_

- [x] 5. Implement A2A Bridge for stock agent
  - Create src/nest/bridge.py with StockAgentBridge class
  - Extend SimpleAgentBridge from NEST framework
  - Implement process_stock_query() method using ComprehensiveAnalysisService
  - Integrate ticker extraction and message formatting
  - Add error handling for invalid queries and analysis failures
  - _Requirements: 1.3, 3.1, 3.2, 3.3_

- [x] 6. Implement Registry Client
  - Create src/nest/registry.py with RegistryClient class
  - Implement register_agent() method with agent metadata
  - Implement lookup_agent() for discovering other agents
  - Implement update_status() for health check updates
  - Add connection error handling and retry logic
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.2_

- [x] 7. Implement NEST Adapter
  - Create src/nest/adapter.py with StockAgentNEST class
  - Initialize NANDA adapter from NEST framework
  - Implement agent_logic() wrapper for stock analysis
  - Integrate A2A bridge and registry client
  - Implement start() and stop() lifecycle methods
  - _Requirements: 1.1, 1.2, 2.1, 6.2_

- [x] 8. Implement outgoing A2A communication
  - Add send_to_agent() method in StockAgentBridge
  - Implement @agent-id syntax parsing
  - Integrate registry lookup for target agents
  - Add timeout and error handling for agent communication
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 9. Implement dual-mode launcher
  - Create src/nest/launcher.py with AgentLauncher class
  - Implement start_standalone() for FastAPI-only mode
  - Implement start_nest() for A2A-only mode
  - Implement start_dual() to run both servers concurrently
  - Add graceful shutdown handling
  - _Requirements: 1.4, 5.2, 5.3, 6.1_

- [x] 10. Add NEST integration to main application
  - Update main.py to check NEST_ENABLED environment variable
  - Add conditional NEST initialization on startup
  - Ensure FastAPI server continues to work independently
  - Add NEST status to health check endpoint
  - _Requirements: 1.4, 5.2, 5.3_

- [x] 11. Add monitoring and logging for NEST integration
  - Add NEST-specific logging to existing logging_service
  - Log A2A message send/receive events
  - Log registry operations (register, lookup, status updates)
  - Add NEST metrics to health check response
  - _Requirements: 2.3, 6.3_

- [ ] 12. Create deployment configuration
  - Create docker-compose-nest.yml for NEST deployment
  - Add NEST environment variables to .env.example
  - Create deployment documentation in docs/NEST_DEPLOYMENT.md
  - Add AWS deployment script integration notes
  - _Requirements: 5.1, 5.2_

- [x] 13. Integration testing and validation
  - Test A2A message processing with sample queries
  - Test registry registration and lookup
  - Test agent-to-agent communication with test agent
  - Verify standalone mode still works without NEST
  - Test error handling for various failure scenarios
  - _Requirements: 1.3, 2.1, 3.2, 4.3_
