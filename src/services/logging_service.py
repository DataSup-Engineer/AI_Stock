"""
Comprehensive logging service for NASDAQ Stock Agent with MongoDB integration
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
import traceback
import json
from dataclasses import asdict
from src.services.database import mongodb_client, database_service
from src.models.logging import AnalysisLogEntry, ErrorLogEntry, LogQueryRequest, LogQueryResponse
from src.models.analysis import StockAnalysis, AnalysisRequest, AnalysisResponse
from src.config.settings import settings

logger = logging.getLogger(__name__)


class LoggingService:
    """Comprehensive logging service with MongoDB persistence and 30-day TTL"""
    
    def __init__(self):
        self.database_service = database_service
        self.mongodb_client = mongodb_client
        self.cleanup_interval_hours = 24  # Run cleanup daily
        self._cleanup_task: Optional[asyncio.Task] = None
        # Don't start cleanup task here - will be started when event loop is running
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        try:
            # Only create task if event loop is running
            if self._cleanup_task is None or self._cleanup_task.done():
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                else:
                    # Event loop not running yet, task will be started later
                    pass
        except RuntimeError:
            # No event loop, task will be started when one is available
            pass
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired log entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
                await self.cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")
    
    async def log_analysis_request(self, request: AnalysisRequest, response: AnalysisResponse) -> str:
        """Log a complete analysis request and response"""
        try:
            log_entry = AnalysisLogEntry(
                analysis_id=response.analysis_id,
                user_query=request.query,
                ticker_symbol=response.ticker,
                company_name=response.company_name,
                recommendation=response.recommendation,
                confidence_score=response.confidence_score,
                processing_time_ms=response.processing_time_ms
            )
            
            log_id = await self.database_service.log_analysis(log_entry)
            
            logger.info(f"Analysis logged: {response.analysis_id} for {response.ticker}")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log analysis request: {e}")
            # Log the logging error itself
            await self.log_error(e, {
                'context': 'log_analysis_request',
                'analysis_id': getattr(response, 'analysis_id', 'unknown'),
                'ticker': getattr(response, 'ticker', 'unknown')
            })
            raise
    
    async def log_stock_analysis(self, stock_analysis: StockAnalysis) -> str:
        """Log a StockAnalysis object"""
        try:
            if not stock_analysis.recommendation:
                # Create a default log entry for failed analysis
                log_entry = AnalysisLogEntry(
                    analysis_id=stock_analysis.analysis_id,
                    user_query=stock_analysis.query_text,
                    ticker_symbol=stock_analysis.ticker,
                    company_name=stock_analysis.company_name,
                    recommendation="Error",
                    confidence_score=0.0,
                    processing_time_ms=stock_analysis.processing_time_ms
                )
            else:
                log_entry = AnalysisLogEntry(
                    analysis_id=stock_analysis.analysis_id,
                    user_query=stock_analysis.query_text,
                    ticker_symbol=stock_analysis.ticker,
                    company_name=stock_analysis.company_name,
                    recommendation=stock_analysis.recommendation.recommendation.value,
                    confidence_score=stock_analysis.recommendation.confidence_score,
                    processing_time_ms=stock_analysis.processing_time_ms
                )
            
            log_id = await self.database_service.log_analysis(log_entry)
            
            logger.info(f"Stock analysis logged: {stock_analysis.analysis_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log stock analysis: {e}")
            await self.log_error(e, {
                'context': 'log_stock_analysis',
                'analysis_id': stock_analysis.analysis_id,
                'ticker': stock_analysis.ticker
            })
            raise
    
    async def log_error(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """Log an error with context information"""
        try:
            error_entry = ErrorLogEntry(
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            log_id = await self.database_service.log_error(error_entry)
            
            logger.error(f"Error logged: {error_entry.error_id} - {error_entry.error_message}")
            return log_id
            
        except Exception as e:
            # If we can't log to database, at least log to application logger
            logger.critical(f"Failed to log error to database: {e}. Original error: {error}")
            return "failed_to_log"
    
    async def log_api_request(self, endpoint: str, method: str, request_data: Dict[str, Any], 
                             response_data: Dict[str, Any], status_code: int, 
                             processing_time_ms: int) -> str:
        """Log API request and response"""
        try:
            # Create a custom log entry for API requests
            api_log_context = {
                'log_type': 'api_request',
                'endpoint': endpoint,
                'method': method,
                'request_data': request_data,
                'response_data': response_data,
                'status_code': status_code,
                'processing_time_ms': processing_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store as error log entry with special type
            error_entry = ErrorLogEntry(
                error_type='API_REQUEST_LOG',
                error_message=f"{method} {endpoint} - Status: {status_code}",
                stack_trace=None,
                context=api_log_context
            )
            
            log_id = await self.database_service.log_error(error_entry)
            
            logger.info(f"API request logged: {method} {endpoint} - {status_code} ({processing_time_ms}ms)")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            return "failed_to_log"
    
    async def get_analysis_logs(self, query_request: LogQueryRequest) -> LogQueryResponse:
        """Retrieve analysis logs based on query parameters"""
        try:
            # Build query filter
            query_filter = {}
            
            if query_request.analysis_id:
                query_filter['analysis_id'] = query_request.analysis_id
            
            if query_request.ticker_symbol:
                query_filter['ticker_symbol'] = query_request.ticker_symbol.upper()
            
            if query_request.start_date:
                query_filter.setdefault('timestamp', {})['$gte'] = query_request.start_date
            
            if query_request.end_date:
                query_filter.setdefault('timestamp', {})['$lte'] = query_request.end_date
            
            # Get analyses collection
            collection = self.mongodb_client.get_collection('analyses')
            
            # Count total matching documents
            total_count = await collection.count_documents(query_filter)
            
            # Get paginated results
            cursor = collection.find(query_filter).sort('timestamp', -1).limit(query_request.limit)
            
            entries = []
            async for document in cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in document:
                    document['_id'] = str(document['_id'])
                entries.append(document)
            
            response = LogQueryResponse(
                total_count=total_count,
                entries=entries
            )
            
            logger.info(f"Retrieved {len(entries)} analysis logs (total: {total_count})")
            return response
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis logs: {e}")
            await self.log_error(e, {'context': 'get_analysis_logs', 'query': asdict(query_request)})
            
            return LogQueryResponse(
                total_count=0,
                entries=[]
            )
    
    async def get_error_logs(self, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None, 
                           error_type: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve error logs with optional filtering"""
        try:
            # Build query filter
            query_filter = {}
            
            if error_type:
                query_filter['error_type'] = error_type
            
            if start_date:
                query_filter.setdefault('timestamp', {})['$gte'] = start_date
            
            if end_date:
                query_filter.setdefault('timestamp', {})['$lte'] = end_date
            
            # Get errors collection
            collection = self.mongodb_client.get_collection('errors')
            
            # Get results
            cursor = collection.find(query_filter).sort('timestamp', -1).limit(limit)
            
            entries = []
            async for document in cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in document:
                    document['_id'] = str(document['_id'])
                entries.append(document)
            
            logger.info(f"Retrieved {len(entries)} error logs")
            return entries
            
        except Exception as e:
            logger.error(f"Failed to retrieve error logs: {e}")
            return []
    
    async def get_recent_analyses(self, ticker: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent analyses, optionally filtered by ticker"""
        try:
            if ticker:
                analyses = await self.database_service.get_analyses_by_ticker(ticker.upper(), limit)
            else:
                analyses = await self.database_service.get_recent_analyses(limit)
            
            logger.info(f"Retrieved {len(analyses)} recent analyses")
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            await self.log_error(e, {'context': 'get_recent_analyses', 'ticker': ticker})
            return []
    
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific analysis by ID"""
        try:
            analysis = await self.database_service.get_analysis_by_id(analysis_id)
            
            if analysis:
                logger.info(f"Retrieved analysis: {analysis_id}")
            else:
                logger.warning(f"Analysis not found: {analysis_id}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get analysis by ID {analysis_id}: {e}")
            await self.log_error(e, {'context': 'get_analysis_by_id', 'analysis_id': analysis_id})
            return None
    
    async def cleanup_expired_entries(self) -> Dict[str, int]:
        """Manually clean up expired entries (TTL should handle this automatically)"""
        try:
            cleanup_result = await self.mongodb_client.cleanup_expired_entries()
            
            logger.info(f"Cleanup completed: {cleanup_result}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            await self.log_error(e, {'context': 'cleanup_expired_entries'})
            return {'analyses_deleted': 0, 'errors_deleted': 0}
    
    async def get_logging_statistics(self) -> Dict[str, Any]:
        """Get logging service statistics"""
        try:
            # Get database health
            db_health = await self.mongodb_client.health_check()
            
            # Get collection counts
            analyses_collection = self.mongodb_client.get_collection('analyses')
            errors_collection = self.mongodb_client.get_collection('errors')
            
            analyses_count = await analyses_collection.count_documents({})
            errors_count = await errors_collection.count_documents({})
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_analyses = await analyses_collection.count_documents({
                'timestamp': {'$gte': yesterday}
            })
            recent_errors = await errors_collection.count_documents({
                'timestamp': {'$gte': yesterday}
            })
            
            stats = {
                'service': 'LoggingService',
                'database_health': db_health,
                'total_analyses': analyses_count,
                'total_errors': errors_count,
                'recent_analyses_24h': recent_analyses,
                'recent_errors_24h': recent_errors,
                'cleanup_task_running': not (self._cleanup_task is None or self._cleanup_task.done()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get logging statistics: {e}")
            return {
                'service': 'LoggingService',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def log_nest_message(
        self,
        message_type: str,
        direction: str,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        message_content: Optional[str] = None,
        target_agent_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log NEST A2A message send/receive events.
        
        Args:
            message_type: Type of message (e.g., 'stock_query', 'analysis_response', 'agent_forward')
            direction: 'incoming' or 'outgoing'
            agent_id: ID of the agent sending/receiving the message
            conversation_id: Conversation identifier
            message_content: Content of the message (truncated if too long)
            target_agent_id: For outgoing messages, the target agent ID
            status: 'success', 'error', or 'timeout'
            error_message: Error message if status is 'error'
            processing_time_ms: Time taken to process the message
            metadata: Additional metadata
            
        Returns:
            str: Log entry ID
        """
        try:
            # Truncate message content if too long
            if message_content and len(message_content) > 500:
                message_content = message_content[:500] + "... (truncated)"
            
            nest_log_context = {
                'log_type': 'nest_message',
                'message_type': message_type,
                'direction': direction,
                'agent_id': agent_id,
                'conversation_id': conversation_id,
                'message_content': message_content,
                'target_agent_id': target_agent_id,
                'status': status,
                'error_message': error_message,
                'processing_time_ms': processing_time_ms,
                'timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store as error log entry with special type for NEST messages
            error_entry = ErrorLogEntry(
                error_type='NEST_MESSAGE_LOG',
                error_message=f"{direction.upper()} {message_type} - {status}",
                stack_trace=None,
                context=nest_log_context
            )
            
            log_id = await self.database_service.log_error(error_entry)
            
            logger.info(
                f"NEST message logged: {direction} {message_type} "
                f"(conversation: {conversation_id}, status: {status})"
            )
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log NEST message: {e}")
            return "failed_to_log"
    
    async def log_nest_registry_operation(
        self,
        operation: str,
        agent_id: str,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log NEST registry operations (register, lookup, status update, deregister).
        
        Args:
            operation: Type of operation ('register', 'lookup', 'status_update', 'deregister')
            agent_id: ID of the agent performing the operation
            status: 'success', 'error', or 'retry'
            error_message: Error message if status is 'error'
            metadata: Additional metadata (e.g., target_agent_id for lookup, capabilities for register)
            
        Returns:
            str: Log entry ID
        """
        try:
            registry_log_context = {
                'log_type': 'nest_registry',
                'operation': operation,
                'agent_id': agent_id,
                'status': status,
                'error_message': error_message,
                'timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store as error log entry with special type for registry operations
            error_entry = ErrorLogEntry(
                error_type='NEST_REGISTRY_LOG',
                error_message=f"Registry {operation} - {status}",
                stack_trace=None,
                context=registry_log_context
            )
            
            log_id = await self.database_service.log_error(error_entry)
            
            logger.info(f"NEST registry operation logged: {operation} for {agent_id} ({status})")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log NEST registry operation: {e}")
            return "failed_to_log"
    
    async def get_nest_statistics(self) -> Dict[str, Any]:
        """
        Get NEST integration statistics.
        
        Returns:
            Dict containing NEST-specific metrics
        """
        try:
            errors_collection = self.mongodb_client.get_collection('errors')
            
            # Get counts for last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Count NEST messages
            nest_messages = await errors_collection.count_documents({
                'error_type': 'NEST_MESSAGE_LOG',
                'timestamp': {'$gte': yesterday}
            })
            
            # Count incoming vs outgoing
            incoming_messages = await errors_collection.count_documents({
                'error_type': 'NEST_MESSAGE_LOG',
                'context.direction': 'incoming',
                'timestamp': {'$gte': yesterday}
            })
            
            outgoing_messages = await errors_collection.count_documents({
                'error_type': 'NEST_MESSAGE_LOG',
                'context.direction': 'outgoing',
                'timestamp': {'$gte': yesterday}
            })
            
            # Count successful vs failed messages
            successful_messages = await errors_collection.count_documents({
                'error_type': 'NEST_MESSAGE_LOG',
                'context.status': 'success',
                'timestamp': {'$gte': yesterday}
            })
            
            failed_messages = await errors_collection.count_documents({
                'error_type': 'NEST_MESSAGE_LOG',
                'context.status': {'$in': ['error', 'timeout']},
                'timestamp': {'$gte': yesterday}
            })
            
            # Count registry operations
            registry_operations = await errors_collection.count_documents({
                'error_type': 'NEST_REGISTRY_LOG',
                'timestamp': {'$gte': yesterday}
            })
            
            # Count successful registry operations
            successful_registry = await errors_collection.count_documents({
                'error_type': 'NEST_REGISTRY_LOG',
                'context.status': 'success',
                'timestamp': {'$gte': yesterday}
            })
            
            # Get average processing time for messages
            pipeline = [
                {
                    '$match': {
                        'error_type': 'NEST_MESSAGE_LOG',
                        'context.processing_time_ms': {'$exists': True},
                        'timestamp': {'$gte': yesterday}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'avg_processing_time': {'$avg': '$context.processing_time_ms'},
                        'max_processing_time': {'$max': '$context.processing_time_ms'},
                        'min_processing_time': {'$min': '$context.processing_time_ms'}
                    }
                }
            ]
            
            processing_stats = await errors_collection.aggregate(pipeline).to_list(length=1)
            
            stats = {
                'service': 'NEST Integration',
                'period': '24 hours',
                'messages': {
                    'total': nest_messages,
                    'incoming': incoming_messages,
                    'outgoing': outgoing_messages,
                    'successful': successful_messages,
                    'failed': failed_messages,
                    'success_rate': f"{(successful_messages / nest_messages * 100):.1f}%" if nest_messages > 0 else "N/A"
                },
                'registry': {
                    'total_operations': registry_operations,
                    'successful_operations': successful_registry,
                    'success_rate': f"{(successful_registry / registry_operations * 100):.1f}%" if registry_operations > 0 else "N/A"
                },
                'performance': processing_stats[0] if processing_stats else {
                    'avg_processing_time': None,
                    'max_processing_time': None,
                    'min_processing_time': None
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get NEST statistics: {e}")
            return {
                'service': 'NEST Integration',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def export_logs(self, start_date: datetime, end_date: datetime, 
                         log_type: str = 'analyses') -> List[Dict[str, Any]]:
        """Export logs for a date range"""
        try:
            collection_name = 'analyses' if log_type == 'analyses' else 'errors'
            collection = self.mongodb_client.get_collection(collection_name)
            
            query_filter = {
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            
            cursor = collection.find(query_filter).sort('timestamp', 1)
            
            exported_logs = []
            async for document in cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in document:
                    document['_id'] = str(document['_id'])
                
                # Convert datetime objects to ISO strings
                for key, value in document.items():
                    if isinstance(value, datetime):
                        document[key] = value.isoformat()
                
                exported_logs.append(document)
            
            logger.info(f"Exported {len(exported_logs)} {log_type} logs from {start_date} to {end_date}")
            return exported_logs
            
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            await self.log_error(e, {
                'context': 'export_logs',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'log_type': log_type
            })
            return []
    
    async def initialize(self):
        """Initialize the logging service and start background tasks"""
        try:
            # Start cleanup task now that event loop is running
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.info("Logging service cleanup task started")
        except Exception as e:
            logger.error(f"Failed to start logging service cleanup task: {e}")
    
    def shutdown(self):
        """Shutdown the logging service"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        logger.info("Logging service shutdown")


# Global logging service instance
logging_service = LoggingService()