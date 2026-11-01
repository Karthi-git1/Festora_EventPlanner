"""User and authentication data models with Pydantic validation.

This module contains comprehensive Pydantic models for users, sessions, and
authentication-related entities with security features including:

- Password hashing and validation
- Session management with secure tokens
- Account lockout and security logging
- Comprehensive validation rules
- XSS prevention through HTML sanitization

All models include:
- Runtime type validation
- Data integrity constraints
- Security-focused design
- Automatic serialization/deserialization
"""

import html
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    EmailStr
)


class User(BaseModel):
    """User account model with comprehensive validation.
    
    Represents a user account with authentication credentials and security features.
    Passwords are stored as bcrypt hashes with minimum cost factor of 12.
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address (used for login)")
    password_hash: str = Field(..., description="Bcrypt password hash (cost factor >= 12)")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Account creation timestamp"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last successful login timestamp"
    )
    failed_login_attempts: int = Field(
        default=0,
        ge=0,
        description="Count of consecutive failed login attempts"
    )
    locked_until: Optional[datetime] = Field(
        None,
        description="Account lock expiration timestamp (None if not locked)"
    )
    active_event_id: Optional[str] = Field(
        None,
        description="Currently active/selected event ID"
    )
    is_active: bool = Field(
        default=True,
        description="Account active status (can be disabled)"
    )
    email_verified: bool = Field(
        default=False,
        description="Email verification status"
    )
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        """Sanitize and normalize email address."""
        if v:
            # Convert to lowercase and strip whitespace
            return v.lower().strip()
        return v
    
    @field_validator('password_hash')
    @classmethod
    def validate_password_hash(cls, v):
        """Validate that password hash appears to be a bcrypt hash."""
        if not v:
            raise ValueError('Password hash cannot be empty')
        # Bcrypt hashes start with $2a$, $2b$, or $2y$ followed by cost factor
        if not (v.startswith('$2a$') or v.startswith('$2b$') or v.startswith('$2y$')):
            raise ValueError('Invalid password hash format (must be bcrypt)')
        return v
    
    @model_validator(mode='after')
    def validate_account_status(self):
        """Validate account lock status consistency."""
        # If account is locked, locked_until must be set
        if self.locked_until and self.locked_until < datetime.now():
            # Lock has expired, reset failed attempts
            self.locked_until = None
            self.failed_login_attempts = 0
        return self
    
    def is_locked(self) -> bool:
        """Check if account is currently locked.
        
        Returns:
            True if account is locked and lock has not expired
        """
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now()
    
    def should_lock_account(self) -> bool:
        """Check if account should be locked based on failed attempts.
        
        Account is locked after 5 consecutive failed login attempts.
        
        Returns:
            True if account should be locked
        """
        return self.failed_login_attempts >= 5
    
    def dict_safe(self) -> Dict[str, Any]:
        """Return dictionary representation without sensitive fields.
        
        Returns:
            Dictionary with password_hash excluded
        """
        data = self.model_dump()
        data.pop('password_hash', None)
        return data


class Session(BaseModel):
    """User session model with secure token management.
    
    Represents an authenticated user session with cryptographically secure token
    (256-bit entropy) and automatic expiration (24 hours).
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Associated user identifier")
    token: str = Field(..., description="Cryptographically secure session token (256-bit)")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Session creation timestamp"
    )
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    last_activity: datetime = Field(
        default_factory=datetime.now,
        description="Last activity timestamp for sliding expiration"
    )
    ip_address: Optional[str] = Field(
        None,
        max_length=45,  # IPv6 max length
        description="Client IP address"
    )
    user_agent: Optional[str] = Field(
        None,
        max_length=500,
        description="Client user agent string"
    )
    csrf_token: Optional[str] = Field(
        None,
        description="CSRF token associated with this session"
    )
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        """Validate session token length and format."""
        if not v:
            raise ValueError('Session token cannot be empty')
        # Token should be at least 32 characters for 256-bit entropy
        if len(v) < 32:
            raise ValueError('Session token must be at least 32 characters')
        return v
    
    @field_validator('ip_address')
    @classmethod
    def sanitize_ip_address(cls, v):
        """Sanitize IP address."""
        if v:
            return v.strip()
        return v
    
    @field_validator('user_agent')
    @classmethod
    def sanitize_user_agent(cls, v):
        """Sanitize user agent string to prevent injection."""
        if v:
            return html.escape(v.strip())
        return v
    
    @model_validator(mode='after')
    def validate_expiration(self):
        """Validate that expiration is after creation."""
        if self.expires_at <= self.created_at:
            raise ValueError('Session expiration must be after creation time')
        return self
    
    def is_expired(self) -> bool:
        """Check if session has expired.
        
        Returns:
            True if current time is past expiration
        """
        return datetime.now() > self.expires_at
    
    def is_active(self, max_idle_minutes: int = 30) -> bool:
        """Check if session is active based on last activity.
        
        Args:
            max_idle_minutes: Maximum idle time in minutes
            
        Returns:
            True if session is not expired and not idle
        """
        if self.is_expired():
            return False
        idle_threshold = datetime.now() - timedelta(minutes=max_idle_minutes)
        return self.last_activity > idle_threshold
    
    def update_activity(self) -> None:
        """Update last activity timestamp to current time."""
        self.last_activity = datetime.now()
    
    @classmethod
    def create_new(cls, user_id: str, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None, lifetime_hours: int = 24) -> 'Session':
        """Create a new session with secure token and expiration.
        
        Args:
            user_id: User identifier for the session
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            lifetime_hours: Session lifetime in hours (default 24)
            
        Returns:
            New Session instance with secure token
        """
        session_id = secrets.token_urlsafe(16)
        token = secrets.token_urlsafe(32)  # 256-bit entropy
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now()
        expires_at = now + timedelta(hours=lifetime_hours)
        
        return cls(
            id=session_id,
            user_id=user_id,
            token=token,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            csrf_token=csrf_token
        )


class AuthenticationEvent(BaseModel):
    """Authentication event logging model.
    
    Represents a security event related to authentication for audit trail.
    All authentication attempts (success and failure) should be logged.
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(
        ...,
        pattern="^(login_success|login_failure|logout|password_change|account_locked|session_expired)$",
        description="Type of authentication event"
    )
    user_id: Optional[str] = Field(
        None,
        description="Associated user identifier (None for failed login with unknown user)"
    )
    email: Optional[str] = Field(
        None,
        description="Email used in authentication attempt"
    )
    ip_address: str = Field(..., max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(
        None,
        max_length=500,
        description="Client user agent string"
    )
    success: bool = Field(..., description="Whether the authentication attempt succeeded")
    failure_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for failure (if applicable)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
    session_id: Optional[str] = Field(
        None,
        description="Associated session ID (if applicable)"
    )
    
    @field_validator('ip_address')
    @classmethod
    def sanitize_ip(cls, v):
        """Sanitize IP address."""
        if v:
            return v.strip()
        return v
    
    @field_validator('user_agent', 'failure_reason')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent injection."""
        if v:
            return html.escape(v.strip())
        return v


class UserRegistrationSchema(BaseModel):
    """Validation schema for user registration requests.
    
    Used to validate new user registration data before account creation.
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)"
    )
    password_confirm: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password confirmation (must match password)"
    )
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        """Sanitize and normalize email address."""
        if v:
            return v.lower().strip()
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements.
        
        Password must contain:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self


class UserLoginSchema(BaseModel):
    """Validation schema for user login requests.
    
    Used to validate login credentials before authentication.
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")
    remember_me: bool = Field(
        default=False,
        description="Whether to extend session lifetime"
    )
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        """Sanitize and normalize email address."""
        if v:
            return v.lower().strip()
        return v


class PasswordChangeSchema(BaseModel):
    """Validation schema for password change requests.
    
    Used to validate password change data for authenticated users.
    """
    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)"
    )
    new_password_confirm: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password confirmation"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate new password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Validate that new password and confirmation match."""
        if self.new_password != self.new_password_confirm:
            raise ValueError('New passwords do not match')
        return self
    
    @model_validator(mode='after')
    def validate_password_changed(self):
        """Validate that new password is different from current password."""
        if self.current_password == self.new_password:
            raise ValueError('New password must be different from current password')
        return self


class PasswordResetRequestSchema(BaseModel):
    """Validation schema for password reset requests.
    
    Used when a user requests a password reset (forgot password).
    """
    email: EmailStr = Field(..., description="User email address for password reset")
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        """Sanitize and normalize email address."""
        if v:
            return v.lower().strip()
        return v


class PasswordResetSchema(BaseModel):
    """Validation schema for completing password reset.
    
    Used when a user completes password reset with token from email.
    """
    reset_token: str = Field(
        ...,
        min_length=32,
        description="Password reset token from email"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters)"
    )
    new_password_confirm: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password confirmation"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate new password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Validate that new password and confirmation match."""
        if self.new_password != self.new_password_confirm:
            raise ValueError('New passwords do not match')
        return self


class UserProfileSchema(BaseModel):
    """Validation schema for user profile information.
    
    Used for displaying and updating user profile data (excludes sensitive fields).
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    id: str = Field(..., description="User identifier")
    email: EmailStr = Field(..., description="User email address")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    active_event_id: Optional[str] = Field(None, description="Currently active event ID")
    email_verified: bool = Field(..., description="Email verification status")


class SessionInfoSchema(BaseModel):
    """Validation schema for session information.
    
    Used for displaying session information to users (excludes sensitive tokens).
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
