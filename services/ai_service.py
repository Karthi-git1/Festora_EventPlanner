"""
AI Service Module - Handles AI copilot logic and intent processing.

This module extracts complex AI processing logic from the main application
to improve code quality, maintainability, and testability.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone


# ============================================================================
# CONSTANTS
# ============================================================================

PLAN_EVENT_KEYWORDS = [
    "create new event", "create a new event", "plan a new", "create another event",
    "plan a wedding", "plan a birthday", "plan an event", "create an event",
    "plan an anniversary", "plan a celebration", "create a wedding", "create a birthday"
]

COST_ESTIMATION_KEYWORDS = [
    "cost estimation", "estimate the cost", "estimate the budget", "estimate budget",
    "budget breakdown", "cost breakdown", "how much will it cost", "how much would it cost",
    "estimate expenses", "estimated budget", "cost for"
]

VENUE_KEYWORDS = [
    "venue", "hall", "place", "location", "mandap", "resort", "hotel", "reception",
    "where can", "where to", "photographer", "caterer", "search"
]

CITY_KEYWORDS = [
    "madurai", "chennai", "bangalore", "mumbai", "delhi", "hyderabad", "coimbatore",
    "pune", "kolkata", "jaipur", "goa", "kochi", "trichy"
]

ACTION_KEYWORDS = [
    "add", "increase", "update", "create", "allocate", "task", "lakh", "lac", "crore",
    "remind", "budget", "expense", "spent", "to total", "schedule", "book the"
]

WEB_SEARCH_KEYWORDS = [
    "which location", "best venue", "where can i", "wedding hall", "reception venue",
    "search the web", "search for", "places in", "venues in", "photographers in", "caterers in"
]

BUDGET_REDUCTION_KEYWORDS = [
    "reduce", "decrease", "cut", "lower", "subtract", "deduct", "less", "drop", "minimize"
]

TASK_INTENT_KEYWORDS = [
    "add task", "add a task", "add the task", "new task", "remind me to", "book", "schedule"
]

TOTAL_BUDGET_KEYWORDS = [
    "to total", "total budget", "to the total", "overall budget", "to total amount"
]


# ============================================================================
# INTENT DETECTION FUNCTIONS
# ============================================================================

def detect_plan_event_intent(prompt_lower: str) -> bool:
    """
    Detect if user wants to create a new event.
    
    Args:
        prompt_lower: Lowercase user prompt
        
    Returns:
        True if intent detected
    """
    # Direct keyword match
    if any(keyword in prompt_lower for keyword in PLAN_EVENT_KEYWORDS):
        return True
    
    # Complex pattern: "plan/create" + event_type + budget/guests info
    has_action = "plan " in prompt_lower or "create " in prompt_lower
    has_event_type = any(w in prompt_lower for w in ["wedding", "birthday", "party", "reception", "anniversary"])
    has_details = any(w in prompt_lower for w in ["budget", "guests", "lakh", "lac", "people"])
    
    return has_action and has_event_type and has_details


def detect_cost_estimation_intent(prompt_lower: str) -> bool:
    """
    Detect if user wants cost estimation.
    
    Args:
        prompt_lower: Lowercase user prompt
        
    Returns:
        True if intent detected
    """
    if any(w in prompt_lower for w in COST_ESTIMATION_KEYWORDS):
        return True
    
    # Check for "estimate" + "cost/budget/breakdown"
    has_estimate = "estimate" in prompt_lower
    has_cost_term = any(w in prompt_lower for w in ["cost", "budget", "breakdown"])
    
    return has_estimate and has_cost_term


def detect_web_search_intent(prompt_lower: str, has_action_request: bool, is_cost_estimation: bool) -> bool:
    """
    Detect if user wants web research for venues/vendors.
    
    Args:
        prompt_lower: Lowercase user prompt
        has_action_request: Whether an action request was detected
        is_cost_estimation: Whether cost estimation was detected
        
    Returns:
        True if intent detected
    """
    if is_cost_estimation or has_action_request:
        return False
    
    # Direct web search keywords
    if any(w in prompt_lower for w in WEB_SEARCH_KEYWORDS):
        return True
    
    # Check for venue + city combination
    has_venue = any(w in prompt_lower for w in VENUE_KEYWORDS)
    has_city = any(c in prompt_lower for c in CITY_KEYWORDS)
    
    return has_venue and has_city


def detect_task_intent(prompt_lower: str) -> bool:
    """Detect if user wants to add a task."""
    return any(k in prompt_lower for k in TASK_INTENT_KEYWORDS)


def detect_total_budget_intent(prompt_lower: str) -> bool:
    """Detect if user wants to modify total budget."""
    # Direct keyword match
    if any(k in prompt_lower for k in TOTAL_BUDGET_KEYWORDS):
        return True
    
    # Check for lakh/crore + total/budget
    has_amount = any(m in prompt_lower for m in ["lakh", "lac", "crore"])
    has_budget_term = any(b in prompt_lower for b in ["total", "budget", "amount"])
    
    return has_amount and has_budget_term


def detect_budget_reduction(prompt_lower: str) -> bool:
    """Detect if budget should be reduced."""
    return any(w in prompt_lower for w in BUDGET_REDUCTION_KEYWORDS)


# ============================================================================
# DATA EXTRACTION FUNCTIONS
# ============================================================================

def extract_amount(prompt_lower: str) -> float:
    """
    Extract monetary amount from prompt.
    
    Args:
        prompt_lower: Lowercase user prompt
        
    Returns:
        Extracted amount (default 100000 if not found)
    """
    # Extract numbers
    numbers = re.findall(r'(\d+)', prompt_lower.replace(",", ""))
    if not numbers:
        return 100000.0 if any(w in prompt_lower for w in ["lakh", "lac"]) else 50000.0
    
    base_amount = float(numbers[0])
    
    # Apply multipliers
    if "crore" in prompt_lower or "cr" in prompt_lower:
        return base_amount * 10000000
    elif "lakh" in prompt_lower or "lac" in prompt_lower:
        return base_amount * 100000
    elif "thousand" in prompt_lower or "k" in prompt_lower:
        return base_amount * 1000
    
    return base_amount


def extract_guest_count(prompt_lower: str, default: int = 100) -> int:
    """
    Extract guest count from prompt.
    
    Args:
        prompt_lower: Lowercase user prompt
        default: Default count if not found
        
    Returns:
        Extracted guest count
    """
    numbers = re.findall(r'(\d+)', prompt_lower)
    return int(numbers[0]) if numbers else default


def extract_city(prompt_lower: str, event_location: str = "") -> str:
    """
    Extract city name from prompt or event location.
    
    Args:
        prompt_lower: Lowercase user prompt
        event_location: Event location string
        
    Returns:
        Extracted city name (default "Chennai")
    """
    # Check for direct city mention
    for city in CITY_KEYWORDS:
        if city in prompt_lower:
            return city.capitalize()
    
    # Extract from event location
    if event_location:
        parts = [p.strip() for p in event_location.split(",") if p.strip()]
        if parts:
            return parts[-1].capitalize()
    
    return "Chennai"


def extract_due_date(prompt_lower: str, default_date: str) -> str:
    """
    Extract due date from prompt.
    
    Args:
        prompt_lower: Lowercase user prompt
        default_date: Default date if not found
        
    Returns:
        Extracted date in YYYY-MM-DD format
    """
    # Simple date extraction (can be enhanced)
    if "before" in prompt_lower:
        # Could implement more sophisticated date parsing
        pass
    
    return default_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def clean_task_title(user_prompt: str, prompt_lower: str) -> str:
    """
    Clean task title by removing budget-related clauses.
    
    Args:
        user_prompt: Original user prompt
        prompt_lower: Lowercase user prompt
        
    Returns:
        Cleaned task title
    """
    # Remove budget-related clauses
    clean_title = re.sub(
        r'(?i)(?:\band\b|\b&\b|\balso\b)?\s*(?:add|increase)?\s*(?:the\s*)?'
        r'(?:amount\s*)?(?:\d+|a|an|one|two)?\s*(?:lakh|lakhs|lac|lacs|crore|k|\d+)?\s*'
        r'(?:to\s*)?(?:the\s*)?(?:total|overall)?\s*(?:budget)?.*$',
        '', user_prompt
    ).strip()
    
    # Ensure minimum length
    if not clean_title or len(clean_title) < 5:
        return "Important milestone"
    
    # Remove common prefixes
    prefixes = [
        "add a task to ", "add the task to ", "add task to ", 
        "add task: ", "remind me to ", "add the task "
    ]
    for prefix in prefixes:
        if clean_title.lower().startswith(prefix):
            clean_title = clean_title[len(prefix):].strip().capitalize()
            break
    
    return clean_title[:75]


def determine_task_category(prompt_lower: str, categories: List[str]) -> Tuple[str, str]:
    """
    Determine task category and symbol based on prompt.
    
    Args:
        prompt_lower: Lowercase user prompt
        categories: Available event categories
        
    Returns:
        Tuple of (category_name, emoji_symbol)
    """
    if "photo" in prompt_lower or "video" in prompt_lower:
        category = next((c for c in categories if "photo" in c.lower()), "Photography")
        return category, "📸"
    
    if "cater" in prompt_lower or "food" in prompt_lower:
        category = next((c for c in categories if "cater" in c.lower() or "food" in c.lower()), "Catering")
        return category, "🍽️"
    
    if "decor" in prompt_lower or "flower" in prompt_lower or "mandap" in prompt_lower:
        return "Decoration", "🌸"
    
    if "cake" in prompt_lower:
        category = next((c for c in categories if "cake" in c.lower()), "Catering")
        return category, "🍰"
    
    if "venue" in prompt_lower or "hall" in prompt_lower:
        category = next((c for c in categories if "venue" in c.lower()), "Venue")
        return category, "🏛️"
    
    # Default
    default_category = categories[0] if categories else "General"
    return default_category, "✨"


# ============================================================================
# COST ESTIMATION FUNCTIONS
# ============================================================================

def generate_birthday_cost_items(guest_count: int) -> List[Dict[str, Any]]:
    """Generate cost estimation items for birthday party."""
    return [
        {
            "category": "Venue & Clubhouse",
            "estimated": round(guest_count * 200),
            "notes": "Party hall with sound system"
        },
        {
            "category": "Birthday Cake",
            "estimated": 6000,
            "notes": "3-tier themed designer fondant cake"
        },
        {
            "category": "Decorations & Balloons",
            "estimated": round(guest_count * 120),
            "notes": "Balloon garland, backdrop & lighting"
        },
        {
            "category": "Food & Snacks Buffet",
            "estimated": round(guest_count * 280),
            "notes": "Welcome drinks, snacks & dinner buffet"
        },
        {
            "category": "Photography & Candids",
            "estimated": 8000,
            "notes": "3-hour party photo coverage"
        },
        {
            "category": "Entertainment & Games",
            "estimated": 7000,
            "notes": "Magician or games coordinator"
        },
        {
            "category": "Return Gifts & Favors",
            "estimated": round(guest_count * 70),
            "notes": "Custom activity kits for kids"
        }
    ]


def generate_wedding_cost_items(guest_count: int) -> List[Dict[str, Any]]:
    """Generate cost estimation items for wedding."""
    return [
        {
            "category": "Venue & Hall Booking",
            "estimated": round(guest_count * 450),
            "notes": "Grand hall & amenities"
        },
        {
            "category": "Food & Catering Feast",
            "estimated": round(guest_count * 550),
            "notes": "Full day traditional feast"
        },
        {
            "category": "Mandap & Floral Decor",
            "estimated": round(guest_count * 200),
            "notes": "Fresh florals & ambient lighting"
        },
        {
            "category": "Photography & Film",
            "estimated": 40000,
            "notes": "2 photographers + wedding film"
        },
        {
            "category": "Bridal Makeup & Styling",
            "estimated": 15000,
            "notes": "Bridal styling & family touchups"
        },
        {
            "category": "Invitations & Stationery",
            "estimated": round(guest_count * 25),
            "notes": "Digital cards & embossed invites"
        },
        {
            "category": "Return Gifts",
            "estimated": round(guest_count * 40),
            "notes": "Brass diyas & sweet hampers"
        }
    ]


def generate_cost_estimation(
    prompt_lower: str,
    event_type: str,
    guests_count: int,
    currency: str
) -> Dict[str, Any]:
    """
    Generate cost estimation breakdown.
    
    Args:
        prompt_lower: Lowercase user prompt
        event_type: Type of event
        guests_count: Number of guests
        currency: Currency symbol
        
    Returns:
        Cost estimation dictionary
    """
    # Extract guest count from prompt
    est_guests = extract_guest_count(prompt_lower, guests_count or 100)
    
    # Determine event type
    if "birth" in prompt_lower:
        est_type = "Birthday"
        cost_items = generate_birthday_cost_items(est_guests)
    else:
        est_type = event_type or "Celebration"
        cost_items = generate_wedding_cost_items(est_guests)
    
    total_est = sum(item["estimated"] for item in cost_items)
    
    return {
        "title": f"Estimated Cost Breakdown for {est_guests} Guests ({est_type})",
        "items": cost_items,
        "totalEstimated": total_est,
        "currency": currency
    }


# ============================================================================
# SYSTEM PROMPT BUILDER
# ============================================================================

def build_ai_system_prompt(
    event_name: str,
    event_type: str,
    event_date: str,
    event_location: str,
    guests_count: int,
    currency: str,
    total_budget: float,
    total_spent: float,
    remaining_budget: float,
    tasks_count: int,
    pending_count: int,
    completed_count: int,
    categories: List[str],
    current_section: str
) -> str:
    """
    Build AI system prompt with event context.
    
    Args:
        event_name: Name of event
        event_type: Type of event
        event_date: Event date
        event_location: Event location
        guests_count: Number of guests
        currency: Currency symbol
        total_budget: Total budget amount
        total_spent: Total spent amount
        remaining_budget: Remaining budget
        tasks_count: Total number of tasks
        pending_count: Pending tasks count
        completed_count: Completed tasks count
        categories: List of event categories
        current_section: Current section user is viewing
        
    Returns:
        Formatted system prompt string
    """
    return f"""You are Festora, an expert AI Personal Event Organizer for '{event_name}' ({event_type}).
Current section user is looking at: {current_section.upper()}.
Current Event Context:
- Name: {event_name}
- Type: {event_type}
- Date: {event_date}
- Location: {event_location}
- Guests: {guests_count}
- Budget: {currency}{total_budget:,.0f} | Spent: {currency}{total_spent:,.0f} | Remaining: {currency}{remaining_budget:,.0f}
- Tasks: {tasks_count} total ({pending_count} pending, {completed_count} completed)
- Budget Categories: {", ".join(categories)}

COMMUNICATION STYLE (Speak like ChatGPT):
- Deliver expansive, articulate, insightful, and beautifully organized responses like ChatGPT.
- When asked for ideas, recommendations, advice, themes, menus, or tips: use clear markdown with bold section headings (###), organized bullet points (•), aesthetic vibes, practical cost implications, and next steps.
- When executing tasks or budget updates: provide a warm, chic confirmation.

Return ONLY valid JSON with:
1. "reply": Expansive, structured ChatGPT-style markdown reply.
2. "action_type": ("add_task"|"add_budget_item"|"update_expense"|"add_total_budget"|"task_and_budget_added"|"add_guest"|"add_reminder"|"create_event"|"recommendations"|"none")
3. "action_payload": Object containing parameters:
   - For add_task: {{"title": str, "category": str, "dueDate": str, "priority": "high"|"medium"|"low", "symbol": str, "notes": str}}
   - For add_total_budget: {{"addedAmount": number, "isReduction": bool}}
   - For task_and_budget_added: {{"task": {{"title": str, "category": str, "dueDate": str, "priority": str}}, "addedAmount": number}}
   - For add_budget_item: {{"category": str, "allocated": number, "spent": number, "notes": str}}
   - For update_expense: {{"category": str, "expenseDelta": number, "notes": str}}
   - For add_guest: {{"name": str, "attendeesCount": number, "category": str, "rsvp": "Confirmed"|"Pending"}}
   - For add_reminder: {{"title": str, "datetime": str, "priority": "high"|"medium"}}
   - For recommendations: array of {{"title": str, "description": str, "type": "task"|"budget", "payload": object}}
"""
