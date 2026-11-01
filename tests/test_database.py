"""Unit tests for database.py - MongoDB connection management.

Tests cover:
- Connection pooling configuration
- Exponential backoff retry logic
- Connection health checks
- Query operations with pagination
- Slow query monitoring
- Index creation
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import DatabaseService, DatabaseConnectionError


class TestDatabaseService:
    """Unit tests for DatabaseService class."""
    
    @patch('config.database.MongoClient')
    def test_successful_connection_with_pooling(self, mock_mongo_client):
        """Test successful database connection with connection pooling parameters."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db',
            min_pool_size=5,
            max_pool_size=20
        )
        
        # Assertions
        assert db_service.connected is True
        assert db_service.min_pool_size == 5
        assert db_service.max_pool_size == 20
        
        # Verify MongoClient was called with pooling parameters
        mock_mongo_client.assert_called_once()
        call_kwargs = mock_mongo_client.call_args[1]
        assert call_kwargs['minPoolSize'] == 5
        assert call_kwargs['maxPoolSize'] == 20
        assert call_kwargs['retryWrites'] is True
        assert call_kwargs['retryReads'] is True
    
    @patch('config.database.MongoClient')
    @patch('config.database.time.sleep')
    def test_connection_retry_with_exponential_backoff(self, mock_sleep, mock_mongo_client):
        """Test connection retry logic with exponential backoff."""
        # Setup mock to fail first 2 attempts, succeed on 3rd
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionFailure("Connection failed")
            return mock_client_instance
        
        mock_mongo_client.side_effect = side_effect
        
        # Create database service (will trigger connection with retry)
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db',
            max_retries=5,
            initial_retry_delay=1.0,
            retry_backoff_factor=2.0
        )
        
        # Assertions
        assert db_service.connected is True
        assert mock_mongo_client.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries before success
        
        # Verify exponential backoff delays (approximately 1s, then 2s with jitter)
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 0.8 <= sleep_calls[0] <= 1.2  # First delay ~1s with jitter
        assert 1.6 <= sleep_calls[1] <= 2.4  # Second delay ~2s with jitter
    
    @patch('config.database.MongoClient')
    @patch('config.database.time.sleep')
    def test_connection_max_retries_exceeded(self, mock_sleep, mock_mongo_client):
        """Test that connection fails gracefully after max retries exceeded."""
        # Setup mock to always fail
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        # Create database service with low max_retries
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db',
            max_retries=2,
            initial_retry_delay=0.1  # Short delay for faster test
        )
        
        # Assertions - should not be connected but should not raise exception
        assert db_service.connected is False
        assert mock_mongo_client.call_count == 3  # Initial + 2 retries
    
    @patch('config.database.MongoClient')
    def test_connection_health_check(self, mock_mongo_client):
        """Test connection health check functionality."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Test healthy connection
        assert db_service.check_connection_health() is True
        
        # Test unhealthy connection
        mock_client_instance.admin.command.side_effect = ConnectionFailure("Connection lost")
        assert db_service.check_connection_health() is False
        assert db_service.connected is False
    
    @patch('config.database.MongoClient')
    def test_find_events_with_pagination(self, mock_mongo_client):
        """Test find_events with pagination parameters."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Mock cursor chain
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter([
            {'id': '1', 'name': 'Event 1'},
            {'id': '2', 'name': 'Event 2'}
        ])
        
        mock_collection.find.return_value = mock_cursor
        mock_db.events = mock_collection
        mock_client_instance.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Test find_events with pagination
        results = db_service.find_events(
            user_id='user123',
            filters={'status': 'active'},
            page=2,
            page_size=50,
            sort_by=[('date', -1)]
        )
        
        # Assertions
        assert len(results) == 2
        mock_collection.find.assert_called_once()
        mock_cursor.skip.assert_called_once_with(50)  # page 2 = skip 50
        mock_cursor.limit.assert_called_once_with(50)
        mock_cursor.sort.assert_called_once_with([('date', -1)])
    
    @patch('config.database.MongoClient')
    def test_find_events_pagination_validation(self, mock_mongo_client):
        """Test that find_events validates pagination parameters."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Test invalid page number
        with pytest.raises(ValueError, match="Page number must be >= 1"):
            db_service.find_events(user_id='user123', page=0)
        
        # Test invalid page size (too small)
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            db_service.find_events(user_id='user123', page_size=0)
        
        # Test invalid page size (too large)
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            db_service.find_events(user_id='user123', page_size=101)
    
    @patch('config.database.MongoClient')
    @patch('config.database.logger')
    def test_slow_query_logging(self, mock_logger, mock_mongo_client):
        """Test that slow queries (>100ms) are logged."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Mock cursor that takes long time
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        # Simulate slow query by making iteration take time
        def slow_iter(self):
            time.sleep(0.15)  # 150ms delay
            return iter([])
        
        mock_cursor.__iter__ = slow_iter
        mock_collection.find.return_value = mock_cursor
        mock_db.events = mock_collection
        mock_client_instance.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Execute query
        db_service.find_events(user_id='user123')
        
        # Verify slow query was logged
        slow_query_logged = any(
            'SLOW QUERY DETECTED' in str(call)
            for call in mock_logger.warning.call_args_list
        )
        assert slow_query_logged
    
    @patch('config.database.MongoClient')
    def test_aggregate_budget_summary(self, mock_mongo_client):
        """Test budget aggregation using MongoDB pipeline."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Mock aggregation result
        mock_collection.aggregate.return_value = [
            {
                'total_allocated': 10000.0,
                'total_spent': 7500.0,
                'remaining': 2500.0
            }
        ]
        
        mock_db.events = mock_collection
        mock_client_instance.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Test budget aggregation
        result = db_service.aggregate_budget_summary(event_id='event123')
        
        # Assertions
        assert result['total_allocated'] == 10000.0
        assert result['total_spent'] == 7500.0
        assert result['remaining'] == 2500.0
        mock_collection.aggregate.assert_called_once()
    
    @patch('config.database.MongoClient')
    def test_insert_update_delete_operations(self, mock_mongo_client):
        """Test basic CRUD operations."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Mock insert result
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = 'inserted_id_123'
        mock_collection.insert_one.return_value = mock_insert_result
        
        # Mock update result
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_collection.update_one.return_value = mock_update_result
        
        # Mock delete result
        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 1
        mock_collection.delete_one.return_value = mock_delete_result
        
        mock_db.__getitem__.return_value = mock_collection
        mock_client_instance.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client_instance
        
        # Create database service
        db_service = DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        )
        
        # Test insert
        doc_id = db_service.insert_one('events', {'name': 'Test Event'})
        assert doc_id == 'inserted_id_123'
        
        # Test update
        success = db_service.update_one(
            'events',
            {'id': 'event123'},
            {'$set': {'name': 'Updated Event'}}
        )
        assert success is True
        
        # Test delete
        success = db_service.delete_one('events', {'id': 'event123'})
        assert success is True
    
    @patch('config.database.MongoClient')
    def test_context_manager(self, mock_mongo_client):
        """Test DatabaseService works as context manager."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Test context manager
        with DatabaseService(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db'
        ) as db_service:
            assert db_service.connected is True
        
        # Verify close was called
        mock_client_instance.close.assert_called_once()


class TestDatabaseServiceHelpers:
    """Tests for module-level helper functions."""
    
    @patch('config.database.DatabaseService')
    def test_init_database_service(self, mock_db_service_class):
        """Test initialization of global database service."""
        from config.database import init_database_service, get_database_service
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.MONGODB_URI = 'mongodb://localhost:27017'
        mock_config.MONGODB_DB = 'test_db'
        mock_config.MONGODB_MIN_POOL_SIZE = 5
        mock_config.MONGODB_MAX_POOL_SIZE = 20
        
        # Initialize service
        service = init_database_service(mock_config)
        
        # Verify DatabaseService was instantiated with correct parameters
        mock_db_service_class.assert_called_once_with(
            mongo_uri='mongodb://localhost:27017',
            db_name='test_db',
            min_pool_size=5,
            max_pool_size=20
        )
    
    @patch('config.database.MongoClient')
    def test_close_database_service(self, mock_mongo_client):
        """Test closing global database service."""
        from config.database import init_database_service, close_database_service, get_database_service
        
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.MONGODB_URI = 'mongodb://localhost:27017'
        mock_config.MONGODB_DB = 'test_db'
        mock_config.MONGODB_MIN_POOL_SIZE = 5
        mock_config.MONGODB_MAX_POOL_SIZE = 20
        
        # Initialize and close
        init_database_service(mock_config)
        close_database_service()
        
        # Verify service is None after close
        assert get_database_service() is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
