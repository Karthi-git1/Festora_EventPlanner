"""Models package for Festora application.

This package contains Pydantic data models for events, tasks, budget items,
users, sessions, authentication, and other domain entities with validation schemas.
"""

from .event_model import (
    BudgetItem,
    EventTask,
    TimelineItem,
    Reminder,
    Guest,
    Vendor,
    Note,
    DiaryEntry,
    Event,
    EventCreateSchema,
    EventUpdateSchema
)

from .user_model import (
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

__all__ = [
    # Event models
    'BudgetItem',
    'EventTask',
    'TimelineItem',
    'Reminder',
    'Guest',
    'Vendor',
    'Note',
    'DiaryEntry',
    'Event',
    'EventCreateSchema',
    'EventUpdateSchema',
    # User and authentication models
    'User',
    'Session',
    'AuthenticationEvent',
    'UserRegistrationSchema',
    'UserLoginSchema',
    'PasswordChangeSchema',
    'PasswordResetRequestSchema',
    'PasswordResetSchema',
    'UserProfileSchema',
    'SessionInfoSchema'
]
