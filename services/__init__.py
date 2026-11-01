"""Services package for Festora application.

This package contains domain service classes including event management,
validation, caching, AI integration, and notification services.

Modules:
    - validation_service: Input validation and XSS prevention
    - cache_service: Caching utilities for performance
    - ai_service: AI copilot intent detection and processing (NEW!)
"""

from services.validation_service import ValidationService
from services.cache_service import CacheService

__all__ = ['ValidationService', 'CacheService']
