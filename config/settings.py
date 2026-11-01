"""Environment-specific configuration classes for Festora application.

This module provides configuration classes for different environments
(development, testing, production) with environment variable validation
and secure defaults.

Requirements: 7.1, 7.2, 24.1, 24.2, 24.3
"""

import os
import secrets
from typing import Optional


class BaseConfig:
    """Base configuration class with common settings across all environments."""
    
    # Application settings
    APP_NAME: str = "Festora Event Planner"
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # MongoDB settings
    MONGODB_URI: str = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/festora')
    MONGODB_DB: str = os.environ.get('MONGODB_DB', 'festora')
    MONGODB_MIN_POOL_SIZE: int = 5
    MONGODB_MAX_POOL_SIZE: int = 20
    
    # Redis settings (for caching and rate limiting)
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Server settings
    PORT: int = int(os.environ.get('PORT', 5000))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    
    # Groq API settings
    GROQ_API_KEY: Optional[str] = os.environ.get('GROQ_API_KEY')
    
    # Security settings
    BCRYPT_LOG_ROUNDS: int = 12  # Cost factor for password hashing
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False  # Override to True in production
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    SESSION_LIFETIME_HOURS: int = 24
    
    # Rate limiting settings
    RATE_LIMIT_UNAUTHENTICATED: int = 100  # requests per minute
    RATE_LIMIT_AUTHENTICATED: int = 500  # requests per minute
    RATE_LIMIT_AUTH_ENDPOINT: int = 10  # requests per minute
    
    # Caching settings
    CACHE_EVENT_TTL_SECONDS: int = 900  # 15 minutes
    CACHE_AI_RESPONSE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Validation settings
    MAX_REQUEST_SIZE_MB: int = 10
    MAX_FILE_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: list = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'text/csv'
    ]
    
    # Logging settings
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = 'json'  # json or text
    LOG_RETENTION_DAYS: int = 30
    
    # Pagination settings
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    # Performance monitoring
    SLOW_QUERY_THRESHOLD_MS: float = 100.0
    
    # CORS settings
    CORS_ORIGINS: list = ['*']  # Override in production
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validate that all required environment variables are set.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        # Base class has no strictly required vars
        # Override in subclasses for environment-specific requirements
        pass


class DevelopmentConfig(BaseConfig):
    """Development environment configuration with debug mode enabled."""
    
    DEBUG: bool = True
    TESTING: bool = False
    
    # Development-specific settings
    LOG_LEVEL: str = 'DEBUG'
    
    # Relaxed security for local development
    SESSION_COOKIE_SECURE: bool = False
    
    # Development MongoDB - use test database
    MONGODB_DB: str = os.environ.get('MONGODB_DB', 'festora_dev')
    
    # Disable rate limiting in development for easier testing
    RATE_LIMIT_ENABLED: bool = False
    
    # Development CORS - allow all origins
    CORS_ORIGINS: list = ['*']
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validate required environment variables for development.
        
        Development has minimal requirements - most have defaults.
        """
        # No strict requirements for development
        # Groq API key is optional
        pass


class TestingConfig(BaseConfig):
    """Testing environment configuration for automated tests."""
    
    DEBUG: bool = False
    TESTING: bool = True
    
    # Testing-specific settings
    LOG_LEVEL: str = 'WARNING'
    
    # Use separate test database
    MONGODB_DB: str = 'festora_test'
    MONGODB_URI: str = os.environ.get('MONGODB_TEST_URI', 'mongodb://localhost:27017/festora_test')
    
    # Use separate Redis database for tests
    REDIS_URL: str = os.environ.get('REDIS_TEST_URL', 'redis://localhost:6379/1')
    
    # Disable rate limiting in tests
    RATE_LIMIT_ENABLED: bool = False
    
    # Reduced session lifetime for faster test runs
    SESSION_LIFETIME_HOURS: int = 1
    
    # Reduced bcrypt rounds for faster test execution
    BCRYPT_LOG_ROUNDS: int = 4
    
    # Short cache TTLs for testing
    CACHE_EVENT_TTL_SECONDS: int = 10
    CACHE_AI_RESPONSE_TTL_SECONDS: int = 30
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validate required environment variables for testing.
        
        Testing has minimal requirements - uses test defaults.
        """
        # No strict requirements for testing
        pass


class ProductionConfig(BaseConfig):
    """Production environment configuration with strict security settings."""
    
    DEBUG: bool = False
    TESTING: bool = False
    
    # Production-specific settings
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Strict security settings for production
    SESSION_COOKIE_SECURE: bool = True  # HTTPS only
    SESSION_COOKIE_SAMESITE: str = 'Strict'
    
    # Enable rate limiting in production
    RATE_LIMIT_ENABLED: bool = True
    
    # Stricter rate limits for production
    RATE_LIMIT_UNAUTHENTICATED: int = int(os.environ.get('RATE_LIMIT_UNAUTHENTICATED', 100))
    RATE_LIMIT_AUTHENTICATED: int = int(os.environ.get('RATE_LIMIT_AUTHENTICATED', 500))
    RATE_LIMIT_AUTH_ENDPOINT: int = int(os.environ.get('RATE_LIMIT_AUTH_ENDPOINT', 10))
    
    # Production CORS - restrict to specific origins
    CORS_ORIGINS: list = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    
    # Error tracking (Sentry)
    SENTRY_DSN: Optional[str] = os.environ.get('SENTRY_DSN')
    SENTRY_ENVIRONMENT: str = 'production'
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    
    # Feature flags
    FEATURE_AI_COPILOT: bool = os.environ.get('FEATURE_AI_COPILOT', 'true').lower() == 'true'
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validate required environment variables for production.
        
        Production requires all critical configuration to be explicitly set.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = {
            'SECRET_KEY': 'Cryptographic secret key for sessions and tokens',
            'MONGODB_URI': 'MongoDB connection URI',
            'MONGODB_DB': 'MongoDB database name',
            'REDIS_URL': 'Redis connection URL for caching and rate limiting'
        }
        
        missing_vars = []
        for var_name, description in required_vars.items():
            value = os.environ.get(var_name)
            if not value:
                missing_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            error_message = (
                "Missing required environment variables for production:\n"
                + "\n".join(f"  - {var}" for var in missing_vars)
            )
            raise ValueError(error_message)
        
        # Validate SECRET_KEY is not the default development key
        secret_key = os.environ.get('SECRET_KEY', '')
        if len(secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long in production. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        # Warn if Groq API key is not set (optional but recommended)
        if not os.environ.get('GROQ_API_KEY'):
            print("WARNING: GROQ_API_KEY not set. AI copilot features will be disabled.")


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """Configuration factory function to get environment-specific config.
    
    Args:
        environment: Environment name (development, testing, production).
                    If None, reads from ENVIRONMENT or FLASK_ENV environment variable.
                    Defaults to 'development' if not set.
    
    Returns:
        Configuration class instance for the specified environment
    
    Raises:
        ValueError: If required environment variables are missing in production
    
    Example:
        >>> config = get_config()  # Auto-detect from ENVIRONMENT
        >>> config = get_config('production')  # Explicit environment
        >>> print(config.MONGODB_URI)
    """
    if environment is None:
        # Try ENVIRONMENT first, fall back to FLASK_ENV, default to development
        environment = os.environ.get('ENVIRONMENT') or os.environ.get('FLASK_ENV') or 'development'
    
    # Normalize environment name
    environment = environment.lower()
    
    # Get configuration class
    config_class = config_by_name.get(environment, DevelopmentConfig)
    
    # Validate required environment variables for this environment
    config_class.validate_required_vars()
    
    return config_class


def validate_config(environment: str = 'production') -> None:
    """Validate configuration for a specific environment.
    
    Useful for pre-deployment validation to ensure all required
    environment variables are set correctly.
    
    Args:
        environment: Environment name to validate (development, testing, production)
    
    Raises:
        ValueError: If configuration validation fails
    
    Example:
        >>> validate_config('production')  # Validate production config
    """
    try:
        config = get_config(environment)
        print(f"✓ Configuration validation passed for '{environment}' environment")
        print(f"  - MongoDB: {config.MONGODB_DB}")
        print(f"  - Redis: {'Configured' if config.REDIS_URL else 'Not configured'}")
        print(f"  - Debug mode: {config.DEBUG}")
        print(f"  - Rate limiting: {'Enabled' if getattr(config, 'RATE_LIMIT_ENABLED', True) else 'Disabled'}")
        return True
    except ValueError as e:
        print(f"✗ Configuration validation failed for '{environment}' environment:")
        print(f"  {str(e)}")
        raise


if __name__ == '__main__':
    """CLI for validating configuration."""
    import sys
    
    if len(sys.argv) > 1:
        env = sys.argv[1]
    else:
        env = os.environ.get('ENVIRONMENT', 'development')
    
    print(f"Validating configuration for environment: {env}")
    print("-" * 60)
    
    try:
        validate_config(env)
        print("\nConfiguration is valid!")
        sys.exit(0)
    except ValueError as e:
        print(f"\nConfiguration validation failed!")
        sys.exit(1)
