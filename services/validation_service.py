"""Input validation and sanitization service for security.

This module provides comprehensive input validation to prevent:
- XSS attacks (via HTML sanitization)
- NoSQL injection (via query validation)
- File upload vulnerabilities
- SSRF attacks (via URL validation)

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

import html
import re
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator, ValidationError


# Pydantic validation schemas
class EventCreateSchema(BaseModel):
    """Validation schema for event creation."""
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., min_length=1, max_length=100)
    date: date
    location: Optional[str] = Field(None, max_length=500)
    guests: int = Field(..., gt=0, le=10000)
    budget: float = Field(..., gt=0, le=1000000000)
    currency: str = Field(default="₹", max_length=10)
    duration: str = Field(default="1 Day", max_length=100)
    theme: Optional[str] = Field(None, max_length=100)
    pattern: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=5000)
    
    @validator('name', 'type', 'location', 'theme', 'notes', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS."""
        if v:
            return html.escape(str(v).strip())
        return v


class TaskSchema(BaseModel):
    """Validation schema for tasks."""
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., max_length=100)
    dueDate: date
    priority: str = Field(pattern="^(low|medium|high)$")
    status: str = Field(default="todo", pattern="^(todo|in-progress|completed)$")
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('title', 'notes', pre=True)
    def sanitize_strings(cls, v):
        if v:
            return html.escape(str(v).strip())
        return v


class BudgetItemSchema(BaseModel):
    """Validation schema for budget items."""
    category: str = Field(..., min_length=1, max_length=100)
    allocated: float = Field(..., ge=0, le=1000000000)
    spent: float = Field(default=0.0, ge=0, le=1000000000)
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('notes', pre=True)
    def sanitize_strings(cls, v):
        if v:
            return html.escape(str(v).strip())
        return v


class ValidationService:
    """Centralized validation and sanitization service."""
    
    # Dangerous MongoDB operators that should be blocked
    DANGEROUS_MONGO_OPERATORS = {
        '$where', '$function', '$accumulator', '$expr',
        'mapReduce', 'group', '$eval'
    }
    
    # Allowed file MIME types
    ALLOWED_FILE_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'text/csv'
    }
    
    # Maximum file size (10MB in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent XSS attacks.
        
        Args:
            value: Raw string input
            
        Returns:
            HTML-escaped string safe for storage and display
            
        Requirement: 3.2 (Sanitize all string inputs to prevent XSS)
        """
        if not value:
            return ""
        return html.escape(str(value).strip())
    
    @staticmethod
    def validate_event_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize event creation/update data.
        
        Args:
            data: Raw event data from request
            
        Returns:
            Validated and sanitized event data
            
        Raises:
            ValidationError: If data fails validation
            
        Requirement: 3.1 (Validate all inputs against defined schemas)
        """
        try:
            # Validate using Pydantic schema
            validated = EventCreateSchema(**data)
            return validated.dict()
        except ValidationError as e:
            raise ValueError(f"Event validation failed: {e.errors()}")
    
    @staticmethod
    def validate_task_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize task data.
        
        Args:
            data: Raw task data from request
            
        Returns:
            Validated and sanitized task data
            
        Raises:
            ValidationError: If data fails validation
        """
        try:
            validated = TaskSchema(**data)
            return validated.dict()
        except ValidationError as e:
            raise ValueError(f"Task validation failed: {e.errors()}")
    
    @staticmethod
    def validate_budget_item(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize budget item data.
        
        Args:
            data: Raw budget item data
            
        Returns:
            Validated and sanitized budget data
            
        Raises:
            ValidationError: If data fails validation
        """
        try:
            validated = BudgetItemSchema(**data)
            return validated.dict()
        except ValidationError as e:
            raise ValueError(f"Budget validation failed: {e.errors()}")
    
    @classmethod
    def validate_mongodb_query(cls, query: Dict[str, Any]) -> Dict[str, Any]:
        """Validate MongoDB query to prevent NoSQL injection.
        
        Args:
            query: MongoDB query parameters
            
        Returns:
            Sanitized query safe for database execution
            
        Raises:
            ValueError: If query contains malicious operators
            
        Requirement: 3.3 (Validate MongoDB query parameters to prevent NoSQL injection)
        """
        # Check for dangerous operators
        query_str = str(query).lower()
        for dangerous_op in cls.DANGEROUS_MONGO_OPERATORS:
            if dangerous_op in query_str:
                raise ValueError(
                    f"Query contains dangerous operator '{dangerous_op}' "
                    f"which is not allowed for security reasons"
                )
        
        # Recursively check nested queries
        def check_nested(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('$') and key in cls.DANGEROUS_MONGO_OPERATORS:
                        raise ValueError(f"Dangerous operator '{key}' not allowed")
                    check_nested(value)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    check_nested(item)
        
        check_nested(query)
        return query
    
    @classmethod
    def validate_file_upload(
        cls,
        file_data: Any,
        filename: str,
        file_size: int
    ) -> bool:
        """Validate uploaded file type and size.
        
        Args:
            file_data: Uploaded file object
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            True if file passes validation
            
        Raises:
            ValueError: If file fails validation
            
        Requirements: 3.4, 3.5 (Validate file types and sizes)
        """
        # Validate file size (Requirement 3.5)
        if file_size > cls.MAX_FILE_SIZE:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum allowed "
                f"({cls.MAX_FILE_SIZE} bytes / 10MB)"
            )
        
        # Validate file extension (basic check)
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.csv'}
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            raise ValueError(
                f"File type '{file_ext}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Note: In production, also validate MIME type from file headers
        # using a library like python-magic for better security
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and sanitize URLs to prevent SSRF attacks.
        
        Args:
            url: User-provided URL
            
        Returns:
            Sanitized URL if valid
            
        Raises:
            ValueError: If URL is malicious or invalid
            
        Requirement: 3.6 (Validate and sanitize URLs to prevent SSRF)
        """
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Check for valid HTTP/HTTPS scheme
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must use HTTP or HTTPS protocol")
        
        # Block common internal/private IP ranges to prevent SSRF
        blocked_patterns = [
            r'localhost',
            r'127\.\d+\.\d+\.\d+',  # 127.x.x.x
            r'10\.\d+\.\d+\.\d+',   # 10.x.x.x (private)
            r'172\.(1[6-9]|2\d|3[01])\.\d+\.\d+',  # 172.16.x.x - 172.31.x.x
            r'192\.168\.\d+\.\d+',  # 192.168.x.x (private)
            r'169\.254\.\d+\.\d+',  # 169.254.x.x (link-local)
            r'0\.0\.0\.0',
            r'\[::\]',  # IPv6 localhost
            r'\[::1\]',  # IPv6 localhost
        ]
        
        url_lower = url.lower()
        for pattern in blocked_patterns:
            if re.search(pattern, url_lower):
                raise ValueError(
                    f"URL targets internal/private network which is not allowed"
                )
        
        return url
    
    @staticmethod
    def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple:
        """Validate pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            max_page_size: Maximum allowed page size
            
        Returns:
            Tuple of (validated_page, validated_page_size)
            
        Raises:
            ValueError: If pagination parameters are invalid
        """
        if page < 1:
            raise ValueError("Page number must be >= 1")
        
        if page_size < 1:
            raise ValueError("Page size must be >= 1")
        
        if page_size > max_page_size:
            raise ValueError(f"Page size cannot exceed {max_page_size}")
        
        return (page, page_size)


# Convenience function for quick validation
def validate_request_data(data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
    """Validate request data using specified schema type.
    
    Args:
        data: Request data to validate
        schema_type: Type of schema ('event', 'task', 'budget')
        
    Returns:
        Validated data
        
    Raises:
        ValueError: If validation fails or unknown schema type
    """
    validator_service = ValidationService()
    
    if schema_type == 'event':
        return validator_service.validate_event_data(data)
    elif schema_type == 'task':
        return validator_service.validate_task_data(data)
    elif schema_type == 'budget':
        return validator_service.validate_budget_item(data)
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")
