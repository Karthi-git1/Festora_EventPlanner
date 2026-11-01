"""Unit tests for event data models.

Tests Pydantic validation rules, XSS prevention, and data integrity constraints.
"""

import pytest
from datetime import date, datetime, timedelta
from pydantic import ValidationError
from models.event_model import (
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


class TestBudgetItem:
    """Test BudgetItem model validation."""
    
    def test_valid_budget_item(self):
        """Test creation of valid budget item."""
        item = BudgetItem(
            id="b-123",
            category="Venue",
            allocated=50000,
            spent=10000,
            notes="Main hall booking"
        )
        assert item.id == "b-123"
        assert item.category == "Venue"
        assert item.allocated == 50000
        assert item.spent == 10000
    
    def test_negative_allocated_fails(self):
        """Test that negative allocated amount fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            BudgetItem(
                id="b-123",
                category="Venue",
                allocated=-1000,
                spent=0
            )
        assert "allocated" in str(exc_info.value)
    
    def test_negative_spent_fails(self):
        """Test that negative spent amount fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            BudgetItem(
                id="b-123",
                category="Venue",
                allocated=50000,
                spent=-100
            )
        assert "spent" in str(exc_info.value)
    
    def test_xss_prevention_in_category(self):
        """Test that XSS attempts in category are escaped."""
        item = BudgetItem(
            id="b-123",
            category="<script>alert('xss')</script>Venue",
            allocated=50000,
            spent=0
        )
        assert "<script>" not in item.category
        assert "&lt;script&gt;" in item.category
    
    def test_xss_prevention_in_notes(self):
        """Test that XSS attempts in notes are escaped."""
        item = BudgetItem(
            id="b-123",
            category="Venue",
            allocated=50000,
            spent=0,
            notes="<img src=x onerror=alert('xss')>"
        )
        assert "<img" not in item.notes
        assert "&lt;img" in item.notes


class TestEventTask:
    """Test EventTask model validation."""
    
    def test_valid_task(self):
        """Test creation of valid task."""
        task = EventTask(
            id="t-123",
            title="Book venue",
            category="Venue",
            dueDate=date.today() + timedelta(days=30),
            priority="high",
            status="todo",
            symbol="🏛️",
            notes="Contact venue by phone"
        )
        assert task.title == "Book venue"
        assert task.priority == "high"
        assert task.status == "todo"
    
    def test_invalid_priority_fails(self):
        """Test that invalid priority value fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            EventTask(
                id="t-123",
                title="Book venue",
                category="Venue",
                dueDate=date.today(),
                priority="urgent",  # Invalid: must be low/medium/high
                status="todo"
            )
        assert "priority" in str(exc_info.value)
    
    def test_invalid_status_fails(self):
        """Test that invalid status value fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            EventTask(
                id="t-123",
                title="Book venue",
                category="Venue",
                dueDate=date.today(),
                priority="high",
                status="pending"  # Invalid: must be todo/in-progress/completed
            )
        assert "status" in str(exc_info.value)
    
    def test_too_old_due_date_fails(self):
        """Test that due dates too far in the past fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            EventTask(
                id="t-123",
                title="Book venue",
                category="Venue",
                dueDate=date.today() - timedelta(days=800),  # More than 2 years ago
                priority="high",
                status="todo"
            )
        assert "Due date cannot be more than 2 years in the past" in str(exc_info.value)
    
    def test_xss_prevention_in_title(self):
        """Test that XSS attempts in title are escaped."""
        task = EventTask(
            id="t-123",
            title="<script>alert('xss')</script>Book venue",
            category="Venue",
            dueDate=date.today(),
            priority="high",
            status="todo"
        )
        assert "<script>" not in task.title
        assert "&lt;script&gt;" in task.title


class TestReminder:
    """Test Reminder model validation."""
    
    def test_valid_reminder(self):
        """Test creation of valid reminder."""
        reminder = Reminder(
            id="rem-123",
            title="Call venue",
            reminder_datetime=datetime.now() + timedelta(days=7),
            priority="high",
            completed=False
        )
        assert reminder.title == "Call venue"
        assert reminder.priority == "high"
        assert not reminder.completed
    
    def test_invalid_priority_fails(self):
        """Test that invalid priority value fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Reminder(
                id="rem-123",
                title="Call venue",
                reminder_datetime=datetime.now(),
                priority="critical",  # Invalid
                completed=False
            )
        assert "priority" in str(exc_info.value)
    
    def test_too_far_future_fails(self):
        """Test that reminders too far in the future fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            Reminder(
                id="rem-123",
                title="Call venue",
                reminder_datetime=datetime.now() + timedelta(days=2000),  # More than 5 years
                priority="high",
                completed=False
            )
        assert "cannot be more than 5 years in the future" in str(exc_info.value)


class TestGuest:
    """Test Guest model validation."""
    
    def test_valid_guest(self):
        """Test creation of valid guest."""
        guest = Guest(
            id="g-123",
            name="John Smith",
            attendeesCount=2,
            rsvp="Confirmed",
            contact="john@example.com",
            notes="Vegetarian meal"
        )
        assert guest.name == "John Smith"
        assert guest.attendeesCount == 2
        assert guest.rsvp == "Confirmed"
    
    def test_invalid_rsvp_fails(self):
        """Test that invalid RSVP status fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Guest(
                id="g-123",
                name="John Smith",
                attendeesCount=2,
                rsvp="Maybe"  # Invalid: must be Pending/Confirmed/Declined
            )
        assert "rsvp" in str(exc_info.value)
    
    def test_zero_attendees_fails(self):
        """Test that zero or negative attendees fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Guest(
                id="g-123",
                name="John Smith",
                attendeesCount=0
            )
        assert "attendeesCount" in str(exc_info.value)
    
    def test_too_many_attendees_fails(self):
        """Test that too many attendees fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Guest(
                id="g-123",
                name="John Smith",
                attendeesCount=1500  # Exceeds 1000 limit
            )
        assert "attendeesCount" in str(exc_info.value)


class TestVendor:
    """Test Vendor model validation."""
    
    def test_valid_vendor(self):
        """Test creation of valid vendor."""
        vendor = Vendor(
            id="v-123",
            name="Grand Palace",
            category="Venue",
            contact="555-1234",
            quotedPrice=100000,
            advancePaid=25000,
            status="Confirmed"
        )
        assert vendor.name == "Grand Palace"
        assert vendor.quotedPrice == 100000
        assert vendor.advancePaid == 25000
    
    def test_advance_exceeding_quoted_price_fails(self):
        """Test that advance paid exceeding quoted price fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Vendor(
                id="v-123",
                name="Grand Palace",
                category="Venue",
                contact="555-1234",
                quotedPrice=100000,
                advancePaid=150000,  # Exceeds quoted price
                status="Confirmed"
            )
        assert "cannot exceed quoted price" in str(exc_info.value)
    
    def test_negative_price_fails(self):
        """Test that negative quoted price fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Vendor(
                id="v-123",
                name="Grand Palace",
                category="Venue",
                contact="555-1234",
                quotedPrice=-1000,
                advancePaid=0,
                status="Confirmed"
            )
        assert "quotedPrice" in str(exc_info.value)


class TestEvent:
    """Test Event model validation."""
    
    def test_valid_event(self):
        """Test creation of valid event."""
        event = Event(
            id="evt-123",
            userId="user-456",
            name="Wedding Celebration",
            type="Wedding",
            date=date.today() + timedelta(days=90),  # Using alias
            location="Grand Hall",
            guests=200,
            budget=500000,
            currency="₹",
            duration="1 Day"
        )
        assert event.name == "Wedding Celebration"
        assert event.guests == 200
        assert event.budget == 500000
    
    def test_negative_budget_fails(self):
        """Test that negative or zero budget fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Event(
                id="evt-123",
                name="Wedding",
                type="Wedding",
                date=date.today(),  # Using alias
                guests=100,
                budget=-1000  # Invalid
            )
        assert "budget" in str(exc_info.value).lower()
    
    def test_zero_guests_fails(self):
        """Test that zero guests fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Event(
                id="evt-123",
                name="Wedding",
                type="Wedding",
                date=date.today(),  # Using alias
                guests=0,  # Invalid
                budget=100000
            )
        assert "guests" in str(exc_info.value).lower()
    
    def test_too_old_event_date_fails(self):
        """Test that event dates too far in the past fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            Event(
                id="evt-123",
                name="Wedding",
                type="Wedding",
                date=date.today() - timedelta(days=400),  # More than 1 year ago, using alias
                guests=100,
                budget=100000
            )
        assert "cannot be more than 1 year in the past" in str(exc_info.value)
    
    def test_xss_prevention_in_name(self):
        """Test that XSS attempts in event name are escaped."""
        event = Event(
            id="evt-123",
            name="<script>alert('xss')</script>Wedding",
            type="Wedding",
            date=date.today(),  # Using alias
            guests=100,
            budget=100000
        )
        assert "<script>" not in event.name
        assert "&lt;script&gt;" in event.name
    
    def test_event_with_nested_models(self):
        """Test event with nested budget items and tasks."""
        event = Event(
            id="evt-123",
            name="Wedding",
            type="Wedding",
            date=date.today() + timedelta(days=90),  # Using alias
            guests=100,
            budget=500000,
            budgetItems=[
                BudgetItem(id="b-1", category="Venue", allocated=200000, spent=50000)
            ],
            tasks=[
                EventTask(
                    id="t-1",
                    title="Book venue",
                    category="Venue",
                    dueDate=date.today() + timedelta(days=60),
                    priority="high",
                    status="todo"
                )
            ]
        )
        assert len(event.budgetItems) == 1
        assert len(event.tasks) == 1
        assert event.budgetItems[0].category == "Venue"
        assert event.tasks[0].priority == "high"


class TestEventCreateSchema:
    """Test EventCreateSchema validation."""
    
    def test_valid_create_schema(self):
        """Test valid event creation data."""
        schema = EventCreateSchema(
            name="Birthday Party",
            type="Birthday",
            date=date.today() + timedelta(days=30),  # Using alias
            location="Home",
            guests=50,
            budget=50000
        )
        assert schema.name == "Birthday Party"
        assert schema.type == "Birthday"
    
    def test_missing_required_field_fails(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreateSchema(
                name="Birthday Party",
                # Missing type, date, guests, budget
            )
        assert "type" in str(exc_info.value) or "date" in str(exc_info.value) or "event_date" in str(exc_info.value)


class TestEventUpdateSchema:
    """Test EventUpdateSchema validation."""
    
    def test_valid_update_schema(self):
        """Test valid partial update data."""
        schema = EventUpdateSchema(
            name="Updated Name",
            guests=150
        )
        assert schema.name == "Updated Name"
        assert schema.guests == 150
        assert schema.event_date is None  # Not provided
    
    def test_all_fields_optional(self):
        """Test that all fields are optional in update schema."""
        schema = EventUpdateSchema()
        assert schema.name is None
        assert schema.type is None
        assert schema.event_date is None
