"""Event data models with Pydantic validation.

This module contains comprehensive Pydantic models for events and related entities
including budget items, tasks, timeline items, reminders, guests, vendors, notes,
and diary entries.

All models include:
- Runtime type validation
- Data integrity constraints
- XSS prevention through HTML sanitization
- Automatic serialization/deserialization
"""

import html
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class BudgetItem(BaseModel):
    """Budget line item model with validation.
    
    Represents a budget allocation for a specific event category.
    """
    model_config = ConfigDict(
        json_encoders={float: lambda v: round(v, 2)}
    )
    
    id: str = Field(..., description="Unique budget item identifier")
    category: str = Field(..., min_length=1, max_length=200, description="Budget category name")
    allocated: float = Field(..., ge=0, description="Allocated budget amount (must be >= 0)")
    spent: float = Field(default=0, ge=0, description="Amount spent (must be >= 0)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('category', 'notes')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('spent')
    @classmethod
    def validate_spent_not_negative(cls, v):
        """Ensure spent amount is not negative."""
        if v < 0:
            raise ValueError('Spent amount cannot be negative')
        return v


class EventTask(BaseModel):
    """Task model for event planning with validation.
    
    Represents an actionable task associated with an event.
    """
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()}
    )
    
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    category: str = Field(..., min_length=1, max_length=200, description="Task category")
    dueDate: date = Field(..., description="Task due date")
    priority: str = Field(..., pattern="^(low|medium|high)$", description="Task priority level")
    status: str = Field(..., pattern="^(todo|in-progress|completed)$", description="Task status")
    symbol: Optional[str] = Field(None, max_length=10, description="Emoji symbol for task")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional task notes")
    
    @field_validator('title', 'category', 'notes', 'symbol')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('dueDate')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due date is not too far in the past."""
        from datetime import timedelta
        if v < date.today() - timedelta(days=730):  # 2 years in the past
            raise ValueError('Due date cannot be more than 2 years in the past')
        return v


class TimelineItem(BaseModel):
    """Timeline milestone model with validation.
    
    Represents a key milestone in the event planning timeline.
    """
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()}
    )
    
    id: str = Field(..., description="Unique timeline item identifier")
    phase: str = Field(..., min_length=1, max_length=100, description="Timeline phase name")
    title: str = Field(..., min_length=1, max_length=500, description="Milestone title")
    timeBefore: str = Field(..., min_length=1, max_length=50, description="Time before event")
    dueDate: date = Field(..., description="Milestone due date")
    completed: bool = Field(default=False, description="Completion status")
    
    @field_validator('phase', 'title', 'timeBefore')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v


class Reminder(BaseModel):
    """Reminder model with validation.
    
    Represents a scheduled reminder for event-related tasks.
    """
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        populate_by_name=True
    )
    
    id: str = Field(..., description="Unique reminder identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Reminder title")
    reminder_datetime: datetime = Field(..., description="Reminder date and time", alias="datetime")
    priority: str = Field(..., pattern="^(low|medium|high)$", description="Reminder priority level")
    completed: bool = Field(default=False, description="Completion status")
    
    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v):
        """Sanitize title to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('reminder_datetime')
    @classmethod
    def validate_datetime(cls, v):
        """Ensure reminder datetime is in a reasonable range."""
        from datetime import timedelta
        # Allow reminders up to 5 years in the future
        if v > datetime.now() + timedelta(days=1825):
            raise ValueError('Reminder cannot be more than 5 years in the future')
        return v


class Guest(BaseModel):
    """Guest model with validation.
    
    Represents an invited guest or guest group for the event.
    """
    id: str = Field(..., description="Unique guest identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Guest name")
    attendeesCount: int = Field(default=1, gt=0, le=1000, description="Number of attendees in group")
    rsvp: str = Field(
        default="Pending",
        pattern="^(Pending|Confirmed|Declined)$",
        description="RSVP status"
    )
    contact: Optional[str] = Field(None, max_length=200, description="Contact information")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name', 'contact', 'notes')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v


class Vendor(BaseModel):
    """Vendor model with validation.
    
    Represents a vendor providing services for the event.
    """
    model_config = ConfigDict(
        json_encoders={float: lambda v: round(v, 2)}
    )
    
    id: str = Field(..., description="Unique vendor identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Vendor name")
    category: str = Field(..., min_length=1, max_length=200, description="Vendor category")
    contact: str = Field(..., min_length=1, max_length=200, description="Contact information")
    quotedPrice: float = Field(..., ge=0, description="Quoted price")
    advancePaid: float = Field(default=0, ge=0, description="Advance amount paid")
    status: str = Field(..., min_length=1, max_length=100, description="Vendor booking status")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name', 'category', 'contact', 'status', 'notes')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @model_validator(mode='after')
    def validate_advance(self):
        """Ensure advance paid does not exceed quoted price."""
        if self.advancePaid > self.quotedPrice:
            raise ValueError('Advance paid cannot exceed quoted price')
        return self


class Note(BaseModel):
    """Note model with validation.
    
    Represents a text note associated with the event.
    """
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()}
    )
    
    id: str = Field(..., description="Unique note identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Note title")
    content: str = Field(..., min_length=1, max_length=10000, description="Note content")
    tag: Optional[str] = Field(None, max_length=100, description="Note tag/category")
    createdAt: date = Field(..., description="Note creation date")
    
    @field_validator('title', 'content', 'tag')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v


class DiaryEntry(BaseModel):
    """Diary entry model with validation.
    
    Represents a diary entry for tracking event planning journey.
    """
    model_config = ConfigDict(
        json_encoders={date: lambda v: v.isoformat()},
        populate_by_name=True
    )
    
    id: str = Field(..., description="Unique diary entry identifier")
    entry_date: date = Field(..., description="Entry date", alias="date")
    content: str = Field(..., min_length=1, max_length=10000, description="Entry content")
    mood: Optional[str] = Field(None, max_length=50, description="Mood/emotion tag")
    
    @field_validator('content', 'mood')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v


class Event(BaseModel):
    """Complete event model with all associated data.
    
    Represents a complete event with all related entities including budget,
    tasks, timeline, reminders, guests, vendors, notes, and diary entries.
    """
    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
            float: lambda v: round(v, 2)
        },
        populate_by_name=True
    )
    
    id: str = Field(..., description="Unique event identifier")
    userId: Optional[str] = Field(None, description="User identifier (for multi-user isolation)")
    name: str = Field(..., min_length=1, max_length=200, description="Event name")
    type: str = Field(..., min_length=1, max_length=100, description="Event type")
    event_date: date = Field(..., description="Event date", alias="date")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    guests: int = Field(..., gt=0, le=100000, description="Expected number of guests")
    budget: float = Field(..., gt=0, le=10000000000, description="Total event budget")
    currency: str = Field(default="₹", max_length=10, description="Currency symbol")
    duration: str = Field(default="1 Day", max_length=100, description="Event duration")
    theme: Optional[str] = Field(None, max_length=100, description="Event theme")
    pattern: Optional[str] = Field(None, max_length=200, description="Design pattern file")
    notes: Optional[str] = Field(None, max_length=5000, description="Event notes")
    categories: List[str] = Field(default_factory=list, description="Event categories")
    budgetItems: List[BudgetItem] = Field(default_factory=list, description="Budget line items")
    tasks: List[EventTask] = Field(default_factory=list, description="Event tasks")
    timeline: List[TimelineItem] = Field(default_factory=list, description="Timeline milestones")
    reminders: List[Reminder] = Field(default_factory=list, description="Scheduled reminders")
    guestsList: List[Guest] = Field(default_factory=list, description="Guest list")
    vendors: List[Vendor] = Field(default_factory=list, description="Vendor list")
    notesList: List[Note] = Field(default_factory=list, description="Event notes")
    diaryEntries: List[DiaryEntry] = Field(default_factory=list, description="Diary entries")
    createdAt: datetime = Field(default_factory=datetime.now, description="Event creation timestamp")
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @field_validator('name', 'type', 'location', 'theme', 'pattern', 'notes', 'currency', 'duration')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('categories')
    @classmethod
    def sanitize_categories(cls, v):
        """Sanitize category strings."""
        return [html.escape(cat.strip()) if cat else cat for cat in v]
    
    @field_validator('event_date')
    @classmethod
    def validate_event_date(cls, v):
        """Ensure event date is not too far in the past."""
        from datetime import timedelta
        if v < date.today() - timedelta(days=365):
            raise ValueError('Event date cannot be more than 1 year in the past')
        return v
    
    @field_validator('budget')
    @classmethod
    def validate_budget_positive(cls, v):
        """Ensure budget is positive."""
        if v <= 0:
            raise ValueError('Budget must be greater than zero')
        return v
    
    @field_validator('guests')
    @classmethod
    def validate_guests_positive(cls, v):
        """Ensure guest count is positive."""
        if v <= 0:
            raise ValueError('Guest count must be greater than zero')
        return v


class EventCreateSchema(BaseModel):
    """Validation schema for event creation requests.
    
    Simplified schema for creating new events with required fields only.
    """
    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat(),
            float: lambda v: round(v, 2)
        },
        populate_by_name=True
    )
    
    name: str = Field(..., min_length=1, max_length=200, description="Event name")
    type: str = Field(..., min_length=1, max_length=100, description="Event type")
    event_date: date = Field(..., description="Event date", alias="date")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    guests: int = Field(..., gt=0, le=100000, description="Expected number of guests")
    budget: float = Field(..., gt=0, le=10000000000, description="Total event budget")
    currency: str = Field(default="₹", max_length=10, description="Currency symbol")
    duration: str = Field(default="1 Day", max_length=100, description="Event duration")
    theme: Optional[str] = Field(None, max_length=100, description="Event theme")
    pattern: Optional[str] = Field(None, max_length=200, description="Design pattern file")
    notes: Optional[str] = Field(None, max_length=5000, description="Event notes")
    
    @field_validator('name', 'type', 'location', 'theme', 'pattern', 'notes', 'currency', 'duration')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('event_date')
    @classmethod
    def validate_future_date(cls, v):
        """Ensure event date is not too far in the past."""
        from datetime import timedelta
        if v < date.today() - timedelta(days=365):
            raise ValueError('Event date cannot be more than 1 year in the past')
        return v


class EventUpdateSchema(BaseModel):
    """Validation schema for event update requests.
    
    All fields are optional to support partial updates.
    """
    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat() if v else None,
            float: lambda v: round(v, 2) if v else None
        },
        populate_by_name=True
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Event name")
    type: Optional[str] = Field(None, min_length=1, max_length=100, description="Event type")
    event_date: Optional[date] = Field(None, description="Event date", alias="date")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    guests: Optional[int] = Field(None, gt=0, le=100000, description="Expected number of guests")
    budget: Optional[float] = Field(None, gt=0, le=10000000000, description="Total event budget")
    currency: Optional[str] = Field(None, max_length=10, description="Currency symbol")
    duration: Optional[str] = Field(None, max_length=100, description="Event duration")
    theme: Optional[str] = Field(None, max_length=100, description="Event theme")
    pattern: Optional[str] = Field(None, max_length=200, description="Design pattern file")
    notes: Optional[str] = Field(None, max_length=5000, description="Event notes")
    categories: Optional[List[str]] = Field(None, description="Event categories")
    
    @field_validator('name', 'type', 'location', 'theme', 'pattern', 'notes', 'currency', 'duration')
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent XSS attacks."""
        if v:
            return html.escape(v.strip())
        return v
    
    @field_validator('categories')
    @classmethod
    def sanitize_categories(cls, v):
        """Sanitize category strings."""
        if v:
            return [html.escape(cat.strip()) if cat else cat for cat in v]
        return v
    
    @field_validator('event_date')
    @classmethod
    def validate_date(cls, v):
        """Validate event date if provided."""
        if v:
            from datetime import timedelta
            if v < date.today() - timedelta(days=365):
                raise ValueError('Event date cannot be more than 1 year in the past')
        return v
