"""MongoDB connection management with pooling and resilient retry logic.

This module provides database connection management with:
- Connection pooling (min 5, max 20 connections)
- Exponential backoff retry logic for connection failures
- Automatic connection health checks
- Graceful fallback handling
- Slow query monitoring

Requirements: 8.5 (Database Layer shall implement connection pooling)
"""

import time
import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
    PyMongoError
)

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection cannot be established."""
    pass


class DatabaseService:
    """Optimized MongoDB service with connection pooling and retry logic.
    
    Features:
    - Connection pooling with configurable min/max connections
    - Exponential backoff retry logic with jitter
    - Automatic index creation for query optimization
    - Slow query monitoring and logging
    - Connection health checks
    - Graceful error handling
    
    Attributes:
        client: MongoDB client instance
        db: Database instance
        connected: Connection status flag
        retry_config: Retry configuration parameters
    """
    
    def __init__(
        self,
        mongo_uri: str,
        db_name: str,
        min_pool_size: int = 5,
        max_pool_size: int = 20,
        max_retries: int = 5,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        retry_backoff_factor: float = 2.0
    ):
        """Initialize database service with connection pooling and retry configuration.
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name to connect to
            min_pool_size: Minimum number of connections in pool (default: 5)
            max_pool_size: Maximum number of connections in pool (default: 20)
            max_retries: Maximum number of connection retry attempts (default: 5)
            initial_retry_delay: Initial retry delay in seconds (default: 1.0)
            max_retry_delay: Maximum retry delay in seconds (default: 30.0)
            retry_backoff_factor: Exponential backoff multiplier (default: 2.0)
        
        Raises:
            DatabaseConnectionError: If connection cannot be established after retries
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        
        # Retry configuration
        self.retry_config = {
            'max_retries': max_retries,
            'initial_delay': initial_retry_delay,
            'max_delay': max_retry_delay,
            'backoff_factor': retry_backoff_factor
        }
        
        # Connection state
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.connected: bool = False
        
        # Initialize connection with retry logic
        self._setup_connection_with_retry()
        
        # Setup indexes if connected
        if self.connected:
            self._ensure_indexes()
    
    def _setup_connection_with_retry(self) -> None:
        """Establish MongoDB connection with exponential backoff retry logic.
        
        Implements retry logic with:
        - Exponential backoff between retries
        - Jitter to prevent thundering herd
        - Maximum retry delay cap
        - Detailed logging of retry attempts
        
        Raises:
            DatabaseConnectionError: If all retry attempts fail
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.retry_config['max_retries']:
            try:
                if retry_count > 0:
                    # Calculate exponential backoff delay with jitter
                    delay = min(
                        self.retry_config['initial_delay'] * (
                            self.retry_config['backoff_factor'] ** (retry_count - 1)
                        ),
                        self.retry_config['max_delay']
                    )
                    # Add jitter (±20% randomness to prevent thundering herd)
                    import random
                    jitter = delay * 0.2 * (random.random() * 2 - 1)
                    actual_delay = delay + jitter
                    
                    logger.warning(
                        f"MongoDB connection attempt {retry_count}/{self.retry_config['max_retries']} "
                        f"failed. Retrying in {actual_delay:.2f}s... Error: {last_error}"
                    )
                    time.sleep(actual_delay)
                
                # Attempt connection
                logger.info(
                    f"Attempting MongoDB connection (attempt {retry_count + 1}/{self.retry_config['max_retries'] + 1})..."
                )
                
                self.client = MongoClient(
                    self.mongo_uri,
                    minPoolSize=self.min_pool_size,
                    maxPoolSize=self.max_pool_size,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=10000,  # 10 second connection timeout
                    socketTimeoutMS=30000,  # 30 second socket timeout
                    retryWrites=True,  # Enable automatic write retries
                    retryReads=True,  # Enable automatic read retries
                    # Connection pool settings
                    maxIdleTimeMS=300000,  # 5 minutes max idle time
                    waitQueueTimeoutMS=10000  # 10 second wait queue timeout
                )
                
                # Test connection with ping
                self.client.admin.command('ping')
                
                # Get database instance
                self.db = self.client[self.db_name]
                
                # Mark as connected
                self.connected = True
                
                logger.info(
                    f"Successfully connected to MongoDB database '{self.db_name}' "
                    f"with connection pool (min={self.min_pool_size}, max={self.max_pool_size})"
                )
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                last_error = str(e)
                retry_count += 1
                
                if retry_count > self.retry_config['max_retries']:
                    error_msg = (
                        f"Failed to connect to MongoDB after {self.retry_config['max_retries']} retries. "
                        f"Last error: {last_error}"
                    )
                    logger.error(error_msg)
                    # Mark as not connected but don't raise exception
                    # This allows the application to start with fallback storage
                    self.connected = False
                    return
                    
            except Exception as e:
                error_msg = f"Unexpected error connecting to MongoDB: {str(e)}"
                logger.error(error_msg)
                self.connected = False
                return
    
    def _ensure_indexes(self) -> None:
        """Create indexes on frequently queried fields for query optimization.
        
        Creates compound indexes for common query patterns:
        - userId + date (for user's events sorted by date)
        - userId + status (for filtering user's events by status)
        - eventId + category (for event-specific category queries)
        
        Requirement: 8.1 (Database Layer shall create indexes on frequently queried fields)
        """
        if not self.connected or self.db is None:
            logger.warning("Cannot create indexes: database not connected")
            return
        
        try:
            events_collection = self.db.events
            
            # Create compound indexes for common queries
            indexes_to_create = [
                {
                    'keys': [('userId', ASCENDING), ('date', DESCENDING)],
                    'name': 'idx_userId_date',
                    'background': True
                },
                {
                    'keys': [('userId', ASCENDING), ('status', ASCENDING)],
                    'name': 'idx_userId_status',
                    'background': True
                },
                {
                    'keys': [('eventId', ASCENDING), ('category', ASCENDING)],
                    'name': 'idx_eventId_category',
                    'background': True
                },
                {
                    'keys': [('userId', ASCENDING), ('createdAt', DESCENDING)],
                    'name': 'idx_userId_createdAt',
                    'background': True
                }
            ]
            
            for index_spec in indexes_to_create:
                try:
                    events_collection.create_index(
                        index_spec['keys'],
                        name=index_spec['name'],
                        background=index_spec['background']
                    )
                    logger.info(f"Created index: {index_spec['name']}")
                except OperationFailure as e:
                    # Index might already exist
                    if 'already exists' not in str(e).lower():
                        logger.warning(f"Failed to create index {index_spec['name']}: {e}")
            
            logger.info("Database indexes ensured successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def check_connection_health(self) -> bool:
        """Check if database connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.connected or self.client is None:
            return False
        
        try:
            # Ping database to check health
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.connected = False
            return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to database if connection is lost.
        
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        logger.info("Attempting database reconnection...")
        self._setup_connection_with_retry()
        return self.connected
    
    def find_events(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        projection: Optional[Dict[str, int]] = None,
        sort_by: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find events with pagination, projection, and sorting.
        
        Args:
            user_id: User identifier for data isolation
            filters: Additional query filters (default: None)
            page: Page number (1-indexed, default: 1)
            page_size: Records per page (max 100, default: 100)
            projection: Fields to return (None = all fields)
            sort_by: Sort specification as list of (field, direction) tuples
        
        Returns:
            List of event documents
        
        Raises:
            ValueError: If page or page_size are invalid
            
        Example:
            >>> db.find_events(
            ...     user_id="user123",
            ...     filters={"status": "active"},
            ...     page=1,
            ...     page_size=50,
            ...     projection={"name": 1, "date": 1},
            ...     sort_by=[("date", -1)]
            ... )
        """
        if not self.connected or self.db is None:
            logger.warning("Cannot find events: database not connected")
            return []
        
        # Validate pagination parameters
        if page < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("Page size must be between 1 and 100")
        
        try:
            # Build query with user isolation
            query = {"userId": user_id}
            if filters:
                query.update(filters)
            
            # Calculate skip for pagination
            skip = (page - 1) * page_size
            
            # Start timing for slow query detection
            start_time = time.time()
            
            # Execute query with projection and pagination
            cursor = self.db.events.find(query, projection)
            
            # Apply sorting if specified
            if sort_by:
                cursor = cursor.sort(sort_by)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(page_size)
            
            # Execute query and convert to list
            results = list(cursor)
            
            # Check for slow query
            execution_time_ms = (time.time() - start_time) * 1000
            if execution_time_ms > 100:
                self.log_slow_query(query, execution_time_ms, "find_events")
            
            return results
            
        except PyMongoError as e:
            logger.error(f"Error finding events: {e}")
            return []
    
    def aggregate_budget_summary(self, event_id: str) -> Dict[str, float]:
        """Aggregate budget summary using MongoDB aggregation pipeline.
        
        Args:
            event_id: Event identifier
        
        Returns:
            Dictionary with total_allocated, total_spent, remaining
            
        Requirement: 8.4 (Use MongoDB aggregation pipeline for aggregations)
        """
        if not self.connected or self.db is None:
            logger.warning("Cannot aggregate budget: database not connected")
            return {"total_allocated": 0.0, "total_spent": 0.0, "remaining": 0.0}
        
        try:
            start_time = time.time()
            
            # Aggregation pipeline for budget calculation
            pipeline = [
                {"$match": {"id": event_id}},
                {"$unwind": "$budgetItems"},
                {
                    "$group": {
                        "_id": "$id",
                        "total_allocated": {"$sum": "$budgetItems.allocated"},
                        "total_spent": {"$sum": "$budgetItems.spent"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_allocated": 1,
                        "total_spent": 1,
                        "remaining": {"$subtract": ["$total_allocated", "$total_spent"]}
                    }
                }
            ]
            
            result = list(self.db.events.aggregate(pipeline))
            
            # Check for slow query
            execution_time_ms = (time.time() - start_time) * 1000
            if execution_time_ms > 100:
                self.log_slow_query({"event_id": event_id}, execution_time_ms, "aggregate_budget_summary")
            
            if result:
                return result[0]
            else:
                return {"total_allocated": 0.0, "total_spent": 0.0, "remaining": 0.0}
                
        except PyMongoError as e:
            logger.error(f"Error aggregating budget summary: {e}")
            return {"total_allocated": 0.0, "total_spent": 0.0, "remaining": 0.0}
    
    def log_slow_query(
        self,
        query: Dict[str, Any],
        execution_time_ms: float,
        operation: str = "unknown"
    ) -> None:
        """Log queries exceeding 100ms threshold for optimization.
        
        Args:
            query: Query that was executed
            execution_time_ms: Query execution time in milliseconds
            operation: Name of the operation (default: "unknown")
            
        Requirement: 8.6 (Monitor slow queries exceeding 100ms)
        """
        logger.warning(
            f"SLOW QUERY DETECTED - Operation: {operation}, "
            f"Execution time: {execution_time_ms:.2f}ms, "
            f"Query: {query}"
        )
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """Insert a single document into a collection.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
        
        Returns:
            Inserted document ID as string, or None if failed
        """
        if not self.connected or self.db is None:
            logger.warning(f"Cannot insert into {collection_name}: database not connected")
            return None
        
        try:
            result = self.db[collection_name].insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            return None
    
    def update_one(
        self,
        collection_name: str,
        filter_query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """Update a single document in a collection.
        
        Args:
            collection_name: Name of the collection
            filter_query: Query to find document to update
            update: Update operations to apply
        
        Returns:
            True if update successful, False otherwise
        """
        if not self.connected or self.db is None:
            logger.warning(f"Cannot update {collection_name}: database not connected")
            return False
        
        try:
            result = self.db[collection_name].update_one(filter_query, update)
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    def delete_one(self, collection_name: str, filter_query: Dict[str, Any]) -> bool:
        """Delete a single document from a collection.
        
        Args:
            collection_name: Name of the collection
            filter_query: Query to find document to delete
        
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.connected or self.db is None:
            logger.warning(f"Cannot delete from {collection_name}: database not connected")
            return False
        
        try:
            result = self.db[collection_name].delete_one(filter_query)
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """Get a collection instance for direct operations.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Collection instance or None if not connected
        """
        if not self.connected or self.db is None:
            logger.warning("Cannot get collection: database not connected")
            return None
        
        return self.db[collection_name]
    
    def close(self) -> None:
        """Close database connection and cleanup resources.
        
        Should be called during application shutdown.
        """
        if self.client:
            logger.info("Closing MongoDB connection...")
            self.client.close()
            self.connected = False
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed."""
        self.close()
        return False


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> Optional[DatabaseService]:
    """Get the global database service instance.
    
    Returns:
        DatabaseService instance or None if not initialized
    """
    return _db_service


def init_database_service(config) -> DatabaseService:
    """Initialize the global database service instance.
    
    Args:
        config: Configuration object with MongoDB settings
    
    Returns:
        Initialized DatabaseService instance
    
    Example:
        >>> from config.settings import get_config
        >>> config = get_config()
        >>> db_service = init_database_service(config)
    """
    global _db_service
    
    logger.info("Initializing database service...")
    
    _db_service = DatabaseService(
        mongo_uri=config.MONGODB_URI,
        db_name=config.MONGODB_DB,
        min_pool_size=config.MONGODB_MIN_POOL_SIZE,
        max_pool_size=config.MONGODB_MAX_POOL_SIZE
    )
    
    return _db_service


def close_database_service() -> None:
    """Close the global database service instance.
    
    Should be called during application shutdown.
    """
    global _db_service
    
    if _db_service:
        _db_service.close()
        _db_service = None
