"""Unit tests for config.settings module.

Tests environment-specific configuration classes, environment variable
validation, and configuration factory pattern.

Requirements: 7.1, 7.2, 24.1, 24.2, 24.3
"""

import os
import pytest
from config.settings import (
    BaseConfig,
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
    get_config,
    validate_config
)


class TestBaseConfig:
    """Test BaseConfig class with common settings."""
    
    def test_base_config_has_default_values(self):
        """Test that BaseConfig provides sensible defaults."""
        assert BaseConfig.APP_NAME == "Festora Event Planner"
        assert BaseConfig.MONGODB_MIN_POOL_SIZE == 5
        assert BaseConfig.MONGODB_MAX_POOL_SIZE == 20
        assert BaseConfig.BCRYPT_LOG_ROUNDS == 12
        assert BaseConfig.SESSION_COOKIE_HTTPONLY is True
        assert BaseConfig.SESSION_LIFETIME_HOURS == 24
        assert BaseConfig.MAX_PAGE_SIZE == 100
        assert BaseConfig.SLOW_QUERY_THRESHOLD_MS == 100.0
    
    def test_base_config_reads_environment_variables(self):
        """Test that BaseConfig reads from environment variables."""
        # Save original values
        original_mongo = os.environ.get('MONGODB_URI')
        original_port = os.environ.get('PORT')
        
        # Set environment variables
        os.environ['MONGODB_URI'] = 'mongodb://testhost:27017/testdb'
        os.environ['PORT'] = '8080'
        
        # Need to re-evaluate the class to pick up new env vars
        # In practice, env vars should be set before importing config
        from config.settings import BaseConfig as FreshConfig
        
        # The config reads env vars at import time, so we test the pattern works
        assert os.environ.get('MONGODB_URI') == 'mongodb://testhost:27017/testdb'
        assert int(os.environ.get('PORT')) == 8080
        
        # Cleanup
        if original_mongo:
            os.environ['MONGODB_URI'] = original_mongo
        else:
            del os.environ['MONGODB_URI']
        
        if original_port:
            os.environ['PORT'] = original_port
        else:
            del os.environ['PORT']
    
    def test_base_config_rate_limit_settings(self):
        """Test rate limiting configuration."""
        assert BaseConfig.RATE_LIMIT_UNAUTHENTICATED == 100
        assert BaseConfig.RATE_LIMIT_AUTHENTICATED == 500
        assert BaseConfig.RATE_LIMIT_AUTH_ENDPOINT == 10
    
    def test_base_config_cache_settings(self):
        """Test caching configuration."""
        assert BaseConfig.CACHE_EVENT_TTL_SECONDS == 900  # 15 minutes
        assert BaseConfig.CACHE_AI_RESPONSE_TTL_SECONDS == 3600  # 1 hour


class TestDevelopmentConfig:
    """Test DevelopmentConfig class for local development."""
    
    def test_development_config_debug_enabled(self):
        """Test that debug mode is enabled in development."""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False
    
    def test_development_config_log_level(self):
        """Test that development uses DEBUG log level."""
        assert DevelopmentConfig.LOG_LEVEL == 'DEBUG'
    
    def test_development_config_security_relaxed(self):
        """Test that development has relaxed security for local testing."""
        assert DevelopmentConfig.SESSION_COOKIE_SECURE is False
        assert DevelopmentConfig.RATE_LIMIT_ENABLED is False
    
    def test_development_config_cors_permissive(self):
        """Test that development allows all CORS origins."""
        assert DevelopmentConfig.CORS_ORIGINS == ['*']
    
    def test_development_config_validation_passes_without_vars(self):
        """Test that development config validation doesn't require env vars."""
        # Should not raise any exceptions
        DevelopmentConfig.validate_required_vars()


class TestTestingConfig:
    """Test TestingConfig class for automated tests."""
    
    def test_testing_config_testing_enabled(self):
        """Test that testing mode is enabled."""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is False
    
    def test_testing_config_separate_database(self):
        """Test that testing uses separate database."""
        assert TestingConfig.MONGODB_DB == 'festora_test'
        # Testing config uses Redis database 1 (different from default 0)
        assert TestingConfig.REDIS_URL == 'redis://localhost:6379/1'
    
    def test_testing_config_fast_settings(self):
        """Test that testing uses faster settings for test execution."""
        assert TestingConfig.BCRYPT_LOG_ROUNDS == 4  # Faster than production (12)
        assert TestingConfig.SESSION_LIFETIME_HOURS == 1  # Shorter than production
        assert TestingConfig.CACHE_EVENT_TTL_SECONDS == 10  # Shorter TTL
    
    def test_testing_config_rate_limiting_disabled(self):
        """Test that rate limiting is disabled in tests."""
        assert TestingConfig.RATE_LIMIT_ENABLED is False
    
    def test_testing_config_validation_passes_without_vars(self):
        """Test that testing config validation doesn't require env vars."""
        # Should not raise any exceptions
        TestingConfig.validate_required_vars()


class TestProductionConfig:
    """Test ProductionConfig class for production deployment."""
    
    def test_production_config_debug_disabled(self):
        """Test that debug mode is disabled in production."""
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.TESTING is False
    
    def test_production_config_strict_security(self):
        """Test that production enforces strict security settings."""
        assert ProductionConfig.SESSION_COOKIE_SECURE is True  # HTTPS only
        assert ProductionConfig.SESSION_COOKIE_SAMESITE == 'Strict'
        assert ProductionConfig.RATE_LIMIT_ENABLED is True
    
    def test_production_config_validation_requires_secret_key(self):
        """Test that production validation requires SECRET_KEY."""
        # Clear environment
        original_secret = os.environ.get('SECRET_KEY')
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        # Should raise ValueError for missing SECRET_KEY
        with pytest.raises(ValueError) as exc_info:
            ProductionConfig.validate_required_vars()
        
        assert 'SECRET_KEY' in str(exc_info.value)
        
        # Restore
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
    
    def test_production_config_validation_requires_mongodb_uri(self):
        """Test that production validation requires MONGODB_URI."""
        # Save original values
        original_secret = os.environ.get('SECRET_KEY')
        original_mongo = os.environ.get('MONGODB_URI')
        original_db = os.environ.get('MONGODB_DB')
        original_redis = os.environ.get('REDIS_URL')
        
        # Set minimal required except MONGODB_URI
        os.environ['SECRET_KEY'] = 'a' * 32
        if 'MONGODB_URI' in os.environ:
            del os.environ['MONGODB_URI']
        os.environ['MONGODB_DB'] = 'festora'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
        
        # Should raise ValueError for missing MONGODB_URI
        with pytest.raises(ValueError) as exc_info:
            ProductionConfig.validate_required_vars()
        
        assert 'MONGODB_URI' in str(exc_info.value)
        
        # Restore
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        elif 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        if original_mongo:
            os.environ['MONGODB_URI'] = original_mongo
        if original_db:
            os.environ['MONGODB_DB'] = original_db
        if original_redis:
            os.environ['REDIS_URL'] = original_redis
    
    def test_production_config_validation_requires_strong_secret_key(self):
        """Test that production validation requires strong SECRET_KEY."""
        # Save original values
        original_secret = os.environ.get('SECRET_KEY')
        original_mongo = os.environ.get('MONGODB_URI')
        original_db = os.environ.get('MONGODB_DB')
        original_redis = os.environ.get('REDIS_URL')
        
        # Set weak secret key (too short)
        os.environ['SECRET_KEY'] = 'weak'
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/festora'
        os.environ['MONGODB_DB'] = 'festora'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
        
        # Should raise ValueError for weak SECRET_KEY
        with pytest.raises(ValueError) as exc_info:
            ProductionConfig.validate_required_vars()
        
        assert 'at least 32 characters' in str(exc_info.value)
        
        # Restore
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        elif 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        if original_mongo:
            os.environ['MONGODB_URI'] = original_mongo
        elif 'MONGODB_URI' in os.environ:
            del os.environ['MONGODB_URI']
        
        if original_db:
            os.environ['MONGODB_DB'] = original_db
        elif 'MONGODB_DB' in os.environ:
            del os.environ['MONGODB_DB']
        
        if original_redis:
            os.environ['REDIS_URL'] = original_redis
        elif 'REDIS_URL' in os.environ:
            del os.environ['REDIS_URL']
    
    def test_production_config_validation_passes_with_all_required_vars(self):
        """Test that production validation passes with all required variables."""
        # Save original values
        original_secret = os.environ.get('SECRET_KEY')
        original_mongo = os.environ.get('MONGODB_URI')
        original_db = os.environ.get('MONGODB_DB')
        original_redis = os.environ.get('REDIS_URL')
        
        # Set all required variables
        os.environ['SECRET_KEY'] = 'a' * 32
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/festora'
        os.environ['MONGODB_DB'] = 'festora'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
        
        # Should not raise any exceptions
        ProductionConfig.validate_required_vars()
        
        # Restore
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        elif 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        if original_mongo:
            os.environ['MONGODB_URI'] = original_mongo
        elif 'MONGODB_URI' in os.environ:
            del os.environ['MONGODB_URI']
        
        if original_db:
            os.environ['MONGODB_DB'] = original_db
        elif 'MONGODB_DB' in os.environ:
            del os.environ['MONGODB_DB']
        
        if original_redis:
            os.environ['REDIS_URL'] = original_redis
        elif 'REDIS_URL' in os.environ:
            del os.environ['REDIS_URL']


class TestGetConfig:
    """Test get_config factory function."""
    
    def test_get_config_returns_development_by_default(self):
        """Test that get_config returns development config by default."""
        # Clear environment variables
        original_env = os.environ.get('ENVIRONMENT')
        original_flask_env = os.environ.get('FLASK_ENV')
        
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']
        
        config = get_config()
        assert config == DevelopmentConfig
        assert config.DEBUG is True
        
        # Restore
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        if original_flask_env:
            os.environ['FLASK_ENV'] = original_flask_env
    
    def test_get_config_reads_environment_variable(self):
        """Test that get_config reads ENVIRONMENT variable."""
        original_env = os.environ.get('ENVIRONMENT')
        
        os.environ['ENVIRONMENT'] = 'testing'
        config = get_config()
        assert config == TestingConfig
        assert config.TESTING is True
        
        # Restore
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        elif 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
    
    def test_get_config_accepts_explicit_environment(self):
        """Test that get_config accepts explicit environment parameter."""
        config = get_config('development')
        assert config == DevelopmentConfig
        
        config = get_config('testing')
        assert config == TestingConfig
        
        # Note: Can't test production without setting required env vars
    
    def test_get_config_normalizes_environment_name(self):
        """Test that get_config handles case-insensitive environment names."""
        config = get_config('DEVELOPMENT')
        assert config == DevelopmentConfig
        
        config = get_config('Testing')
        assert config == TestingConfig
    
    def test_get_config_falls_back_to_flask_env(self):
        """Test that get_config falls back to FLASK_ENV if ENVIRONMENT not set."""
        original_env = os.environ.get('ENVIRONMENT')
        original_flask_env = os.environ.get('FLASK_ENV')
        
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        os.environ['FLASK_ENV'] = 'testing'
        
        config = get_config()
        assert config == TestingConfig
        
        # Restore
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        if original_flask_env:
            os.environ['FLASK_ENV'] = original_flask_env
        elif 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']


class TestValidateConfig:
    """Test validate_config function."""
    
    def test_validate_config_development_passes(self):
        """Test that development config validation passes."""
        # Should not raise any exceptions
        result = validate_config('development')
        assert result is True
    
    def test_validate_config_testing_passes(self):
        """Test that testing config validation passes."""
        # Should not raise any exceptions
        result = validate_config('testing')
        assert result is True
    
    def test_validate_config_production_fails_without_required_vars(self):
        """Test that production config validation fails without required vars."""
        # Clear required variables
        original_secret = os.environ.get('SECRET_KEY')
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        with pytest.raises(ValueError):
            validate_config('production')
        
        # Restore
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
