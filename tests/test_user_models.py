"""Unit tests for user and authentication models.

Tests Pydantic validation rules, security features, password validation,
session management, and data integrity constraints.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from models.user_model import (
    User,
    Session,
    AuthenticationEvent,
    UserRegistrationSchema,
    UserLoginSchema,
    PasswordChangeSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    UserProfileSchema,
    SessionInfoSchema
)


class TestUser:
    """Test User model validation."""
    
    def test_valid_user(self):
        """Test creation of valid user."""
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5",
            created_at=datetime.now()
        )
        assert user.id == "usr-123"
        assert user.email == "test@example.com"
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.is_active is True
        assert user.email_verified is False
    
    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        user = User(
            id="usr-123",
            email="Test@Example.COM",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5"
        )
        assert user.email == "test@example.com"
    
    def test_invalid_email_fails(self):
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="usr-123",
                email="invalid-email",
                password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5"
            )
        assert "email" in str(exc_info.value).lower()
    
    def test_invalid_password_hash_format_fails(self):
        """Test that non-bcrypt password hash fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="usr-123",
                email="test@example.com",
                password_hash="plain_text_password"
            )
        assert "bcrypt" in str(exc_info.value).lower()
    
    def test_is_locked_when_locked_until_set(self):
        """Test is_locked() returns True when account is locked."""
        future_time = datetime.now() + timedelta(minutes=15)
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5",
            locked_until=future_time
        )
        assert user.is_locked() is True
    
    def test_is_locked_false_when_lock_expired(self):
        """Test is_locked() returns False when lock has expired."""
        past_time = datetime.now() - timedelta(minutes=15)
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5",
            locked_until=past_time
        )
        assert user.is_locked() is False
    
    def test_should_lock_account_after_5_failures(self):
        """Test should_lock_account() returns True after 5 failed attempts."""
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5",
            failed_login_attempts=5
        )
        assert user.should_lock_account() is True
    
    def test_should_not_lock_account_before_5_failures(self):
        """Test should_lock_account() returns False before 5 failed attempts."""
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5",
            failed_login_attempts=4
        )
        assert user.should_lock_account() is False
    
    def test_dict_safe_excludes_password_hash(self):
        """Test dict_safe() excludes password_hash from output."""
        user = User(
            id="usr-123",
            email="test@example.com",
            password_hash="$2b$12$KIXvQH5p5K9YvL5rK5L5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5"
        )
        safe_dict = user.dict_safe()
        assert "password_hash" not in safe_dict
        assert "email" in safe_dict
        assert safe_dict["email"] == "test@example.com"


class TestSession:
    """Test Session model validation."""
    
    def test_valid_session(self):
        """Test creation of valid session."""
        now = datetime.now()
        expires = now + timedelta(hours=24)
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,  # 32 character token
            created_at=now,
            expires_at=expires,
            last_activity=now
        )
        assert session.id == "sess-123"
        assert session.user_id == "usr-456"
        assert len(session.token) == 32
    
    def test_short_token_fails(self):
        """Test that token shorter than 32 characters fails validation."""
        now = datetime.now()
        expires = now + timedelta(hours=24)
        with pytest.raises(ValidationError) as exc_info:
            Session(
                id="sess-123",
                user_id="usr-456",
                token="short",  # Too short
                created_at=now,
                expires_at=expires
            )
        assert "token" in str(exc_info.value).lower()
        assert "32" in str(exc_info.value)
    
    def test_expiration_before_creation_fails(self):
        """Test that expiration before creation fails validation."""
        now = datetime.now()
        past = now - timedelta(hours=1)
        with pytest.raises(ValidationError) as exc_info:
            Session(
                id="sess-123",
                user_id="usr-456",
                token="a" * 32,
                created_at=now,
                expires_at=past  # Before creation
            )
        assert "expiration" in str(exc_info.value).lower()
    
    def test_is_expired_true_when_past_expiration(self):
        """Test is_expired() returns True when session has expired."""
        now = datetime.now()
        past_expiration = now - timedelta(hours=1)
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=25),
            expires_at=past_expiration
        )
        assert session.is_expired() is True
    
    def test_is_expired_false_when_not_expired(self):
        """Test is_expired() returns False when session is still valid."""
        now = datetime.now()
        future_expiration = now + timedelta(hours=1)
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=1),
            expires_at=future_expiration
        )
        assert session.is_expired() is False
    
    def test_is_active_false_when_expired(self):
        """Test is_active() returns False when session has expired."""
        now = datetime.now()
        past_expiration = now - timedelta(hours=1)
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=25),
            expires_at=past_expiration,
            last_activity=now - timedelta(hours=2)
        )
        assert session.is_active() is False
    
    def test_is_active_false_when_idle_too_long(self):
        """Test is_active() returns False when idle beyond threshold."""
        now = datetime.now()
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=22),
            last_activity=now - timedelta(minutes=45)  # 45 minutes idle
        )
        assert session.is_active(max_idle_minutes=30) is False
    
    def test_is_active_true_when_recent_activity(self):
        """Test is_active() returns True when recently active."""
        now = datetime.now()
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=23),
            last_activity=now - timedelta(minutes=10)  # 10 minutes ago
        )
        assert session.is_active(max_idle_minutes=30) is True
    
    def test_update_activity_updates_timestamp(self):
        """Test update_activity() updates last_activity timestamp."""
        now = datetime.now()
        old_activity = now - timedelta(hours=1)
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=22),
            last_activity=old_activity
        )
        session.update_activity()
        assert session.last_activity > old_activity
    
    def test_create_new_generates_secure_session(self):
        """Test create_new() generates secure session with proper tokens."""
        session = Session.create_new(
            user_id="usr-456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        assert session.user_id == "usr-456"
        assert len(session.token) >= 32
        assert len(session.csrf_token) >= 32
        assert session.ip_address == "192.168.1.1"
        assert session.expires_at > datetime.now()
    
    def test_xss_prevention_in_user_agent(self):
        """Test that XSS attempts in user agent are escaped."""
        now = datetime.now()
        session = Session(
            id="sess-123",
            user_id="usr-456",
            token="a" * 32,
            created_at=now,
            expires_at=now + timedelta(hours=24),
            user_agent="<script>alert('xss')</script>Mozilla"
        )
        assert "<script>" not in session.user_agent
        assert "&lt;script&gt;" in session.user_agent


class TestAuthenticationEvent:
    """Test AuthenticationEvent model validation."""
    
    def test_valid_authentication_event(self):
        """Test creation of valid authentication event."""
        event = AuthenticationEvent(
            id="evt-123",
            event_type="login_success",
            user_id="usr-456",
            email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
            timestamp=datetime.now()
        )
        assert event.event_type == "login_success"
        assert event.success is True
    
    def test_invalid_event_type_fails(self):
        """Test that invalid event type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            AuthenticationEvent(
                id="evt-123",
                event_type="invalid_event",
                ip_address="192.168.1.1",
                success=False
            )
        assert "event_type" in str(exc_info.value).lower()
    
    def test_xss_prevention_in_failure_reason(self):
        """Test that XSS attempts in failure reason are escaped."""
        event = AuthenticationEvent(
            id="evt-123",
            event_type="login_failure",
            ip_address="192.168.1.1",
            success=False,
            failure_reason="<script>alert('xss')</script>Invalid credentials"
        )
        assert "<script>" not in event.failure_reason
        assert "&lt;script&gt;" in event.failure_reason


class TestUserRegistrationSchema:
    """Test UserRegistrationSchema validation."""
    
    def test_valid_registration(self):
        """Test valid user registration data."""
        schema = UserRegistrationSchema(
            email="newuser@example.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!"
        )
        assert schema.email == "newuser@example.com"
    
    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        schema = UserRegistrationSchema(
            email="NewUser@Example.COM",
            password="SecurePass123!",
            password_confirm="SecurePass123!"
        )
        assert schema.email == "newuser@example.com"
    
    def test_password_too_short_fails(self):
        """Test that password shorter than 8 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="Short1!",
                password_confirm="Short1!"
            )
        assert "8 characters" in str(exc_info.value)
    
    def test_password_missing_uppercase_fails(self):
        """Test that password without uppercase letter fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="lowercase123!",
                password_confirm="lowercase123!"
            )
        assert "uppercase" in str(exc_info.value).lower()
    
    def test_password_missing_lowercase_fails(self):
        """Test that password without lowercase letter fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="UPPERCASE123!",
                password_confirm="UPPERCASE123!"
            )
        assert "lowercase" in str(exc_info.value).lower()
    
    def test_password_missing_digit_fails(self):
        """Test that password without digit fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="NoDigitsHere!",
                password_confirm="NoDigitsHere!"
            )
        assert "digit" in str(exc_info.value).lower()
    
    def test_password_missing_special_char_fails(self):
        """Test that password without special character fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="NoSpecial123",
                password_confirm="NoSpecial123"
            )
        assert "special character" in str(exc_info.value).lower()
    
    def test_passwords_mismatch_fails(self):
        """Test that mismatched passwords fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationSchema(
                email="test@example.com",
                password="SecurePass123!",
                password_confirm="DifferentPass123!"
            )
        assert "do not match" in str(exc_info.value).lower()


class TestUserLoginSchema:
    """Test UserLoginSchema validation."""
    
    def test_valid_login(self):
        """Test valid login data."""
        schema = UserLoginSchema(
            email="user@example.com",
            password="SecurePass123!",
            remember_me=True
        )
        assert schema.email == "user@example.com"
        assert schema.remember_me is True
    
    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        schema = UserLoginSchema(
            email="User@Example.COM",
            password="SecurePass123!"
        )
        assert schema.email == "user@example.com"
    
    def test_remember_me_defaults_to_false(self):
        """Test that remember_me defaults to False."""
        schema = UserLoginSchema(
            email="user@example.com",
            password="SecurePass123!"
        )
        assert schema.remember_me is False


class TestPasswordChangeSchema:
    """Test PasswordChangeSchema validation."""
    
    def test_valid_password_change(self):
        """Test valid password change data."""
        schema = PasswordChangeSchema(
            current_password="OldSecure123!",
            new_password="NewSecure456!",
            new_password_confirm="NewSecure456!"
        )
        assert schema.current_password == "OldSecure123!"
        assert schema.new_password == "NewSecure456!"
    
    def test_new_password_validation(self):
        """Test that new password is validated for strength."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeSchema(
                current_password="OldSecure123!",
                new_password="weak",
                new_password_confirm="weak"
            )
        assert "8 characters" in str(exc_info.value)
    
    def test_new_passwords_mismatch_fails(self):
        """Test that mismatched new passwords fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeSchema(
                current_password="OldSecure123!",
                new_password="NewSecure456!",
                new_password_confirm="DifferentPass789!"
            )
        assert "do not match" in str(exc_info.value).lower()
    
    def test_same_password_fails(self):
        """Test that using same password as current fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeSchema(
                current_password="SameSecure123!",
                new_password="SameSecure123!",
                new_password_confirm="SameSecure123!"
            )
        assert "different" in str(exc_info.value).lower()


class TestPasswordResetRequestSchema:
    """Test PasswordResetRequestSchema validation."""
    
    def test_valid_reset_request(self):
        """Test valid password reset request."""
        schema = PasswordResetRequestSchema(
            email="user@example.com"
        )
        assert schema.email == "user@example.com"
    
    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        schema = PasswordResetRequestSchema(
            email="User@Example.COM"
        )
        assert schema.email == "user@example.com"


class TestPasswordResetSchema:
    """Test PasswordResetSchema validation."""
    
    def test_valid_password_reset(self):
        """Test valid password reset data."""
        schema = PasswordResetSchema(
            reset_token="a" * 32,
            new_password="NewSecure123!",
            new_password_confirm="NewSecure123!"
        )
        assert len(schema.reset_token) == 32
        assert schema.new_password == "NewSecure123!"
    
    def test_short_reset_token_fails(self):
        """Test that reset token shorter than 32 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetSchema(
                reset_token="short",
                new_password="NewSecure123!",
                new_password_confirm="NewSecure123!"
            )
        assert "reset_token" in str(exc_info.value).lower()
    
    def test_new_password_validation(self):
        """Test that new password is validated for strength."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetSchema(
                reset_token="a" * 32,
                new_password="weak",
                new_password_confirm="weak"
            )
        assert "8 characters" in str(exc_info.value)


class TestUserProfileSchema:
    """Test UserProfileSchema validation."""
    
    def test_valid_profile(self):
        """Test valid user profile data."""
        schema = UserProfileSchema(
            id="usr-123",
            email="user@example.com",
            created_at=datetime.now(),
            last_login=datetime.now(),
            active_event_id="evt-456",
            email_verified=True
        )
        assert schema.id == "usr-123"
        assert schema.email == "user@example.com"
        assert schema.email_verified is True


class TestSessionInfoSchema:
    """Test SessionInfoSchema validation."""
    
    def test_valid_session_info(self):
        """Test valid session info data."""
        now = datetime.now()
        schema = SessionInfoSchema(
            id="sess-123",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            last_activity=now,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        assert schema.id == "sess-123"
        assert schema.ip_address == "192.168.1.1"
