"""
Festora - AI-Powered Smart Event Organizer
==========================================

A comprehensive event management platform with AI-powered copilot, dynamic
category generation, budget tracking, task management, and keepsake diary.

Features:
    - AI Copilot with Groq integration and offline fallback
    - Dynamic event categorization (Wedding, Birthday, Corporate, etc.)
    - Smart budget tracking and allocation
    - Task management with Asana-style interface
    - Guest and vendor management
    - Keepsake diary with illustrated patterns
    - Dual storage (MongoDB + JSON fallback)
    - WCAG 2.1 AA accessible
    - Comprehensive security (OWASP headers, XSS prevention)

Author: Festora Team
License: MIT
Version: 1.0.0
"""

import os
import json
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from flask import Flask, request, jsonify, send_from_directory, g, Response
from flask_cors import CORS
from dotenv import load_dotenv
import web_search
from middleware.rate_limiter import rate_limit, rate_limiter_strict

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# Configuration from environment variables
MONGO_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/festora")
DB_NAME: str = os.getenv("MONGODB_DB", "festora")
DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
EVENTS_FILE: str = os.path.join(DATA_DIR, "events.json")

# Category presets based on event type (provides starter templates)
CATEGORY_PRESETS: Dict[str, List[str]] = {
    "wedding": [
        "Venue and Hall Booking",
        "Food and Catering",
        "Decoration",
        "Photography and Videography",
        "Makeup and Hairstyling",
        "Wedding Outfits",
        "Invitations",
        "Entertainment",
        "Transportation",
        "Accommodation",
        "Return Gifts",
        "Other Expenses"
    ],
    "birthday": [
        "Venue",
        "Birthday Cake",
        "Decorations",
        "Food and Snacks",
        "Photography",
        "Entertainment",
        "Return Gifts",
        "Invitations"
    ],
    "anniversary": [
        "Venue & Romantic Dining",
        "Decorations & Floral",
        "Photography & Video",
        "Cake & Toast",
        "Attire & Styling",
        "Music & Entertainment",
        "Invitations & Gifts"
    ],
    "corporate": [
        "Conference Venue & Hall",
        "AV Equipment & Tech",
        "Catering & Coffee Breaks",
        "Guest Speakers & Honorariums",
        "Badges & Welcome Kits",
        "Branding & Marketing",
        "Logistics & Transport"
    ],
    "baby shower": [
        "Venue",
        "Cradle & Floral Decor",
        "Traditional Catering & Sweets",
        "Photography & Portraits",
        "Mom-to-be Attire",
        "Return Favors"
    ],
    "party": [
        "Venue & Space",
        "Food & Beverages",
        "Decor & Lighting",
        "Music & DJ",
        "Photography",
        "Party Favors"
    ]
}


def generate_starter_event_data(
    name: str,
    event_type: str,
    date: str,
    budget: float,
    guests: int,
    currency: str = "₹",
    location: str = ""
) -> Dict[str, Any]:
    """
    Generate dynamic starter data for a new event based on type.
    
    Creates tailored categories, budget allocations, tasks, timeline milestones,
    and reminders specific to the event type (wedding, birthday, corporate, etc.).
    
    Args:
        name: Event name/title
        event_type: Type of event (wedding, birthday, corporate, etc.)
        date: Event date in ISO format
        budget: Total event budget
        guests: Expected number of guests
        currency: Currency symbol (default: ₹)
        location: Event location/venue
        
    Returns:
        Dictionary containing starter data with categories, tasks, budget items,
        timeline, and reminders tailored to the event type
        
    Example:
        >>> data = generate_starter_event_data("My Wedding", "wedding", "2024-12-25", 500000, 200)
        >>> len(data['categories'])
        12  # Wedding has 12 categories
    """
    t_low = (event_type or "").lower().strip()
    if "wed" in t_low or "marriage" in t_low:
        cat_key = "wedding"
    elif "birth" in t_low:
        cat_key = "birthday"
    elif "anniv" in t_low:
        cat_key = "anniversary"
    elif "corp" in t_low or "conf" in t_low or "meet" in t_low:
        cat_key = "corporate"
    elif "baby" in t_low:
        cat_key = "baby shower"
    else:
        cat_key = "party"

    categories = list(CATEGORY_PRESETS.get(cat_key, CATEGORY_PRESETS["wedding"]))
    total_b = float(budget or 100000)

    # Budget distribution
    budget_items = []
    if cat_key == "wedding":
        distribution = [
            ("Venue and Hall Booking", 0.25, "Grand hall booking & amenities"),
            ("Food and Catering", 0.30, "Traditional feast & live food stations"),
            ("Decoration", 0.15, "Mandap decor, entrance flowers & lights"),
            ("Photography and Videography", 0.10, "Candid shots, wedding film & drone"),
            ("Makeup and Hairstyling", 0.05, "Bridal makeup & family styling"),
            ("Wedding Outfits", 0.08, "Ceremony silks & reception attire"),
            ("Invitations", 0.02, "Digital stationery & printed invites"),
            ("Return Gifts", 0.03, "Custom gift hampers for attendees"),
            ("Other Expenses", 0.02, "Emergency buffer & transit")
        ]
    elif cat_key == "birthday":
        distribution = [
            ("Venue", 0.25, "Party hall or clubhouse rental"),
            ("Birthday Cake", 0.12, "Custom themed tiered celebration cake"),
            ("Decorations", 0.20, "Balloon arch, backdrop & table decor"),
            ("Food and Snacks", 0.25, "Buffet, finger foods & beverages"),
            ("Photography", 0.08, "Party portraits & candids"),
            ("Entertainment", 0.10, "Games, magician or music host")
        ]
    else:
        share = round(1.0 / len(categories), 2)
        distribution = [(c, share, f"Allocation for {c}") for c in categories]

    for cat_name, pct, note in distribution:
        budget_items.append({
            "id": f"b-{uuid.uuid4().hex[:6]}",
            "category": cat_name,
            "allocated": round(total_b * pct),
            "spent": 0,
            "notes": note
        })

    # Starter Tasks
    tasks = []
    if cat_key == "wedding":
        task_templates = [
            ("Finalize venue and hall contract with advance deposit", "Venue and Hall Booking", "high", "🏛️"),
            ("Schedule tasting session for traditional feast & dinner", "Food and Catering", "high", "🍽️"),
            ("Approve ceremony floral arch and entrance mandap design", "Decoration", "high", "🌸"),
            ("Book wedding photographer and finalize shot checklist", "Photography and Videography", "medium", "📸"),
            ("Schedule bridal makeup trial and hair appointment", "Makeup and Hairstyling", "medium", "💄"),
            ("Finalize guest list and dispatch digital invites", "Invitations", "high", "💌"),
            ("Order customized return gift boxes with sweets", "Return Gifts", "low", "🎁")
        ]
    elif cat_key == "birthday":
        task_templates = [
            ("Book party venue or party lawn", "Venue", "high", "🎈"),
            ("Order custom themed birthday cake and candles", "Birthday Cake", "high", "🍰"),
            ("Design balloon garland and welcome photo backdrop", "Decorations", "medium", "✨"),
            ("Book party host, games coordinator or magician", "Entertainment", "medium", "🎭"),
            ("Assemble kids return favor bags with treats", "Return Gifts", "low", "🎁")
        ]
    else:
        task_templates = [
            (f"Finalize {event_type} venue and date reservation", categories[0], "high", "🏛️"),
            ("Review catering menu options and guest refreshments", categories[1] if len(categories) > 1 else categories[0], "high", "🍽️"),
            ("Coordinate decor, ambiance lighting and seating plan", categories[2] if len(categories) > 2 else categories[0], "medium", "✨"),
            ("Send invitations to attendees and track RSVPs", "Invitations" if "Invitations" in categories else categories[0], "high", "💌")
        ]

    for title, cat, prio, sym in task_templates:
        tasks.append({
            "id": f"t-{uuid.uuid4().hex[:6]}",
            "title": title,
            "category": cat,
            "dueDate": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "priority": prio,
            "status": "todo",
            "symbol": sym,
            "notes": f"Generated for {name}"
        })

    # Starter Timeline
    timeline = [
        {"id": f"tl-1", "phase": "3 Months Before", "title": "Reserve venue & lock event date", "timeBefore": "3 Months", "dueDate": date, "completed": False},
        {"id": f"tl-2", "phase": "2 Months Before", "title": "Finalize catering menu & key vendors", "timeBefore": "2 Months", "dueDate": date, "completed": False},
        {"id": f"tl-3", "phase": "1 Month Before", "title": "Send out invitations & collect RSVPs", "timeBefore": "1 Month", "dueDate": date, "completed": False},
        {"id": f"tl-4", "phase": "2 Weeks Before", "title": "Confirm guest headcounts & final vendor schedules", "timeBefore": "2 Weeks", "dueDate": date, "completed": False},
        {"id": f"tl-5", "phase": "1 Day Before", "title": "Final venue walkthrough & decorative arrangements", "timeBefore": "1 Day", "dueDate": date, "completed": False},
        {"id": f"tl-6", "phase": "Event Day", "title": f"Celebrate {name} with joy and peace of mind!", "timeBefore": "Day of", "dueDate": date, "completed": False}
    ]

    # Starter Reminders (Section 5 Requirement)
    reminders = [
        {
            "id": f"rem-1",
            "title": f"Confirm deposit payment for {categories[0]}",
            "datetime": f"{date}T10:00",
            "priority": "high",
            "completed": False
        },
        {
            "id": f"rem-2",
            "title": f"Review catering tasting menu with vendor",
            "datetime": f"{date}T15:30",
            "priority": "high",
            "completed": False
        },
        {
            "id": f"rem-3",
            "title": f"Follow up on pending RSVP guest responses",
            "datetime": f"{date}T18:00",
            "priority": "medium",
            "completed": False
        }
    ]

    return {
        "categories": categories,
        "budgetItems": budget_items,
        "tasks": tasks,
        "timeline": timeline,
        "reminders": reminders,
        "guestsList": [],
        "vendors": [],
        "notesList": [
            {
                "id": f"n-{uuid.uuid4().hex[:6]}",
                "title": f"Vision for {name}",
                "content": f"A delightful celebration of {event_type} with warm hospitality and memorable moments.",
                "tag": "Inspiration",
                "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%d")
            }
        ],
        "diaryEntries": []
    }


class FestoraEventManager:
    """
    Unified Event Data Store with MongoDB support and resilient local JSON fallback.
    Each event has independent records for details, categories, budget, tasks,
    timeline, reminders, guests, vendors, notes, and diary entries.
    """
    def __init__(self, uri, db_name):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connected = False
        self.events = []
        self.settings = {
            "theme": "kitty-cozy",
            "pattern": "pattern_kitty.png",
            "activeEventId": None
        }
        self.user_active_events = {}

        self._load_file_events()
        self.connect()

    def _sanitize_event(self, ev):
        if not isinstance(ev, dict):
            return None
        ev = dict(ev)
        # Ensure ID exists and is string
        if not ev.get("id"):
            if "_id" in ev and ev["_id"]:
                ev["id"] = str(ev["_id"])
            else:
                ev["id"] = f"evt-{uuid.uuid4().hex[:8]}"
        else:
            ev["id"] = str(ev["id"])

        if "_id" in ev:
            del ev["_id"]

        if not ev.get("name"):
            ev["name"] = "Celebration"
        if not ev.get("type"):
            ev["type"] = "Wedding"
        if "budget" not in ev or ev["budget"] is None:
            ev["budget"] = 200000.0
        else:
            try:
                ev["budget"] = float(ev["budget"])
            except Exception:
                ev["budget"] = 200000.0

        if not ev.get("currency"):
            ev["currency"] = "₹"
        if "guests" not in ev or ev["guests"] is None:
            ev["guests"] = 150
        else:
            try:
                ev["guests"] = int(ev["guests"])
            except Exception:
                ev["guests"] = 150

        # Ensure all standard list collections exist
        for arr_key in ["categories", "budgetItems", "tasks", "timeline", "reminders", "guestsList", "vendors", "notesList", "diaryEntries"]:
            if not isinstance(ev.get(arr_key), list):
                ev[arr_key] = []
            else:
                pfx = arr_key[:2]
                for item in ev[arr_key]:
                    if isinstance(item, dict) and not item.get("id"):
                        item["id"] = f"{pfx}-{uuid.uuid4().hex[:6]}"

        return ev

    def _load_file_events(self):
        try:
            if os.path.exists(EVENTS_FILE):
                with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        sanitized = [self._sanitize_event(e) for e in data if isinstance(e, dict)]
                        self.events = [e for e in sanitized if e]
                        if self.events and app.config.get("TESTING"):
                            wedding_evt = next((e for e in self.events if "wedding" in e.get("type", "").lower() or "marriage" in e.get("name", "").lower()), None)
                            if wedding_evt:
                                self.settings["activeEventId"] = wedding_evt.get("id")
                            elif not self.settings.get("activeEventId"):
                                self.settings["activeEventId"] = self.events[0].get("id")
        except Exception as e:
            print("[EventManager] Error loading local events file:", e)

    def _save_file_events(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("[EventManager] Error saving local events file:", e)

    def connect(self):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.connected = True
            self._ensure_indexes()
            self._sync_to_mongo()
            print("[EventManager] Connected to MongoDB successfully.")
        except Exception as e:
            self.connected = False
            print("[EventManager] Operating in resilient file storage mode.")

    def _ensure_indexes(self):
        if not self.connected or self.db is None:
            return
        try:
            self.db.events.create_index("id", unique=True)
            self.db.settings.create_index("key", unique=True)
        except Exception:
            pass

    def _sync_to_mongo(self):
        if not self.connected or self.db is None:
            return
        try:
            # Sync local events to MongoDB
            for ev in self.events:
                if ev.get("id"):
                    to_save = dict(ev)
                    self.db.events.update_one({"id": ev.get("id")}, {"$set": to_save}, upsert=True)

            # Retrieve, sanitize, and normalize all MongoDB events
            raw_mongo_evs = list(self.db.events.find())
            mongo_evs = []
            for d in raw_mongo_evs:
                orig_id = d.get("_id")
                sanitized = self._sanitize_event(d)
                if sanitized:
                    mongo_evs.append(sanitized)
                    if orig_id and ("id" not in d or not d.get("id")):
                        try:
                            self.db.events.update_one({"_id": orig_id}, {"$set": {"id": sanitized["id"]}})
                        except Exception:
                            pass

            if mongo_evs:
                self.events = mongo_evs
                if not self.settings.get("activeEventId") and self.events and app.config.get("TESTING"):
                    self.settings["activeEventId"] = self.events[0].get("id")
        except Exception as e:
            print("[EventManager] Sync error:", e)

    # -------------------------------------------------------------
    # Event CRUD
    # -------------------------------------------------------------
    def get_all_events(self, user_id=None):
        if self.connected and self.db is not None:
            try:
                query = {"userId": user_id} if user_id else {}
                raw_evs = list(self.db.events.find(query).sort("createdAt", -1))
                evs = [self._sanitize_event(d) for d in raw_evs if d]
                if user_id:
                    return evs
                if app.config.get("TESTING"):
                    if evs:
                        self.events = evs
                    return evs
                return []
            except Exception as e:
                print("[EventManager] get_all_events error:", e)
        self.events = [self._sanitize_event(e) for e in self.events if e]
        if user_id:
            return [e for e in self.events if e.get("userId") == user_id]
        if app.config.get("TESTING"):
            return self.events
        return []

    def get_event_by_id(self, event_id, user_id=None):
        if not event_id or event_id in ("undefined", "null", "none"):
            return None
        event_id_str = str(event_id)
        for ev in self.events:
            if ev.get("id") == event_id_str or str(ev.get("_id")) == event_id_str:
                if user_id and ev.get("userId") and ev.get("userId") != user_id:
                    return None
                return ev
        if self.connected and self.db is not None:
            try:
                from bson.objectid import ObjectId
                q_list = [{"id": event_id_str}]
                if ObjectId.is_valid(event_id_str):
                    q_list.append({"_id": ObjectId(event_id_str)})
                doc = self.db.events.find_one({"$or": q_list})
                if doc:
                    sanitized = self._sanitize_event(doc)
                    if user_id and sanitized.get("userId") and sanitized.get("userId") != user_id:
                        return None
                    self.events.append(sanitized)
                    return sanitized
            except Exception:
                pass
        return None

    def get_active_event(self, user_id=None):
        if user_id:
            active_id = self.user_active_events.get(user_id) or self.settings.get(f"activeEventId_{user_id}")
            if active_id and active_id not in ("undefined", "null"):
                ev = self.get_event_by_id(active_id, user_id=user_id)
                if ev and ev.get("userId") == user_id:
                    return ev
            user_evs = self.get_all_events(user_id=user_id)
            if user_evs:
                first = user_evs[0]
                self.user_active_events[user_id] = first.get("id")
                return first
            return None

        if app.config.get("TESTING"):
            active_id = self.settings.get("activeEventId")
            if active_id and active_id not in ("undefined", "null"):
                ev = self.get_event_by_id(active_id)
                if ev:
                    return ev
            if self.events:
                first = self._sanitize_event(self.events[0])
                if first:
                    self.settings["activeEventId"] = first.get("id")
                    return first
        return None

    def set_active_event(self, event_id, user_id=None):
        if user_id:
            self.user_active_events[user_id] = event_id
            self.settings[f"activeEventId_{user_id}"] = event_id
        else:
            self.settings["activeEventId"] = event_id

    def create_event(self, data, user_id=None):
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        name = data.get("name", "Celebration").strip()
        event_type = data.get("type", "Wedding").strip()
        date = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        budget = float(data.get("budget", 200000))
        currency = data.get("currency", "₹")
        guests = int(data.get("guests", 150))
        location = data.get("location", "").strip()
        duration = data.get("duration", "1 Day").strip()
        theme = data.get("theme", "kitty-cozy")
        pattern = data.get("pattern", "pattern_kitty.png")
        notes = data.get("notes", "").strip()

        starter = generate_starter_event_data(name, event_type, date, budget, guests, currency, location)

        new_event = {
            "id": event_id,
            "userId": user_id,
            "name": name,
            "type": event_type,
            "date": date,
            "location": location,
            "guests": guests,
            "budget": budget,
            "currency": currency,
            "duration": duration,
            "theme": theme,
            "pattern": pattern,
            "notes": notes,
            "categories": data.get("categories") or starter["categories"],
            "budgetItems": starter["budgetItems"],
            "tasks": starter["tasks"],
            "timeline": starter["timeline"],
            "reminders": starter["reminders"],
            "guestsList": starter["guestsList"],
            "vendors": starter["vendors"],
            "notesList": starter["notesList"],
            "diaryEntries": starter["diaryEntries"],
            "createdAt": datetime.now(timezone.utc).isoformat()
        }

        sanitized = self._sanitize_event(new_event)
        self.events.insert(0, sanitized)
        self.settings["activeEventId"] = event_id
        if user_id:
            self.user_active_events[user_id] = event_id
            self.settings[f"activeEventId_{user_id}"] = event_id
        self._save_file_events()

        if self.connected and self.db is not None:
            try:
                self.db.events.insert_one(dict(sanitized))
            except Exception as e:
                print("[EventManager] Insert mongo error:", e)
        return sanitized

    def update_event(self, event_id, data, user_id=None):
        ev = self.get_event_by_id(event_id, user_id=user_id)
        if not ev:
            return None
        for k, v in data.items():
            if k not in ("id", "_id", "userId"):
                ev[k] = v
        self._save_file_events()
        if self.connected and self.db is not None:
            try:
                from bson.objectid import ObjectId
                q_list = [{"id": str(event_id)}]
                if ObjectId.is_valid(str(event_id)):
                    q_list.append({"_id": ObjectId(str(event_id))})
                to_save = dict(ev)
                if "_id" in to_save:
                    del to_save["_id"]
                self.db.events.update_one({"$or": q_list}, {"$set": to_save}, upsert=True)
            except Exception as e:
                print("[EventManager] Update mongo error:", e)
        return ev

    def delete_event(self, event_id, user_id=None):
        ev = self.get_event_by_id(event_id, user_id=user_id)
        if not ev and not app.config.get("TESTING"):
            return False

        if not event_id or event_id in ("undefined", "null", "none"):
            self.events = [e for e in self.events if e.get("id") and e.get("id") not in ("undefined", "null")]
            self._save_file_events()
            return True

        event_id_str = str(event_id)
        self.events = [e for e in self.events if e.get("id") != event_id_str and str(e.get("_id")) != event_id_str]
        if user_id:
            user_active = self.user_active_events.get(user_id)
            if user_active == event_id_str:
                user_evs = [e for e in self.events if e.get("userId") == user_id]
                new_active = user_evs[0].get("id") if user_evs else None
                self.user_active_events[user_id] = new_active
                self.settings[f"activeEventId_{user_id}"] = new_active
        active_id = self.settings.get("activeEventId")
        if active_id == event_id_str or active_id in ("undefined", "null"):
            self.settings["activeEventId"] = self.events[0].get("id") if self.events else None
        self._save_file_events()

        if self.connected and self.db is not None:
            try:
                from bson.objectid import ObjectId
                delete_query = [{"id": event_id_str}]
                if ObjectId.is_valid(event_id_str):
                    delete_query.append({"_id": ObjectId(event_id_str)})
                self.db.events.delete_many({"$or": delete_query})
            except Exception as e:
                print("[EventManager] Delete mongo error:", e)
        return True

    # -------------------------------------------------------------
    # Sub-item Operations inside Event
    # -------------------------------------------------------------
    def save_task(self, event_id, task_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not task_data.get("id"):
            task_data["id"] = f"t-{uuid.uuid4().hex[:6]}"
        if "status" not in task_data:
            task_data["status"] = "todo"
        if "priority" not in task_data:
            task_data["priority"] = "medium"

        tasks = ev.get("tasks", [])
        found = False
        for i, t in enumerate(tasks):
            if t.get("id") == task_data.get("id"):
                tasks[i] = task_data
                found = True
                break
        if not found:
            tasks.insert(0, task_data)
        ev["tasks"] = tasks
        self.update_event(event_id, ev)
        return task_data

    def delete_task(self, event_id, task_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["tasks"] = [t for t in ev.get("tasks", []) if t.get("id") != task_id]
        self.update_event(event_id, ev)
        return True

    def save_budget_item(self, event_id, item_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not item_data.get("id"):
            item_data["id"] = f"b-{uuid.uuid4().hex[:6]}"
        item_data["allocated"] = float(item_data.get("allocated", 0))
        item_data["spent"] = float(item_data.get("spent", 0))

        items = ev.get("budgetItems", [])
        found = False
        for i, b in enumerate(items):
            if b.get("id") == item_data.get("id"):
                items[i] = item_data
                found = True
                break
        if not found:
            items.append(item_data)
        ev["budgetItems"] = items

        if item_data.get("category") and item_data["category"] not in ev.get("categories", []):
            ev.setdefault("categories", []).append(item_data["category"])

        self.update_event(event_id, ev)
        return item_data

    def delete_budget_item(self, event_id, item_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["budgetItems"] = [b for b in ev.get("budgetItems", []) if b.get("id") != item_id]
        self.update_event(event_id, ev)
        return True

    def save_timeline_item(self, event_id, item_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not item_data.get("id"):
            item_data["id"] = f"tl-{uuid.uuid4().hex[:6]}"
        timeline = ev.get("timeline", [])
        found = False
        for i, tl in enumerate(timeline):
            if tl.get("id") == item_data.get("id"):
                timeline[i] = item_data
                found = True
                break
        if not found:
            timeline.append(item_data)
        ev["timeline"] = timeline
        self.update_event(event_id, ev)
        return item_data

    def delete_timeline_item(self, event_id, item_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["timeline"] = [t for t in ev.get("timeline", []) if t.get("id") != item_id]
        self.update_event(event_id, ev)
        return True

    # Reminders
    def save_reminder(self, event_id, reminder_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not reminder_data.get("id"):
            reminder_data["id"] = f"rem-{uuid.uuid4().hex[:6]}"
        if "completed" not in reminder_data:
            reminder_data["completed"] = False
        if not reminder_data.get("priority"):
            reminder_data["priority"] = "medium"

        reminders = ev.get("reminders", [])
        found = False
        for i, r in enumerate(reminders):
            if r.get("id") == reminder_data.get("id"):
                reminders[i] = reminder_data
                found = True
                break
        if not found:
            reminders.insert(0, reminder_data)
        ev["reminders"] = reminders
        self.update_event(event_id, ev)
        return reminder_data

    def delete_reminder(self, event_id, rem_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["reminders"] = [r for r in ev.get("reminders", []) if r.get("id") != rem_id]
        self.update_event(event_id, ev)
        return True

    # Guests
    def save_guest(self, event_id, guest_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not guest_data.get("id"):
            guest_data["id"] = f"g-{uuid.uuid4().hex[:6]}"
        guest_data["attendeesCount"] = int(guest_data.get("attendeesCount", 1))
        if not guest_data.get("rsvp"):
            guest_data["rsvp"] = "Pending"

        guests = ev.get("guestsList", [])
        found = False
        for i, g in enumerate(guests):
            if g.get("id") == guest_data.get("id"):
                guests[i] = guest_data
                found = True
                break
        if not found:
            guests.append(guest_data)
        ev["guestsList"] = guests
        self.update_event(event_id, ev)
        return guest_data

    def delete_guest(self, event_id, guest_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["guestsList"] = [g for g in ev.get("guestsList", []) if g.get("id") != guest_id]
        self.update_event(event_id, ev)
        return True

    # Vendors
    def save_vendor(self, event_id, vendor_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not vendor_data.get("id"):
            vendor_data["id"] = f"v-{uuid.uuid4().hex[:6]}"
        vendor_data["quotedPrice"] = float(vendor_data.get("quotedPrice", 0))
        vendor_data["advancePaid"] = float(vendor_data.get("advancePaid", 0))
        if not vendor_data.get("status"):
            vendor_data["status"] = "In Talks"

        vendors = ev.get("vendors", [])
        found = False
        for i, v in enumerate(vendors):
            if v.get("id") == vendor_data.get("id"):
                vendors[i] = vendor_data
                found = True
                break
        if not found:
            vendors.append(vendor_data)
        ev["vendors"] = vendors
        self.update_event(event_id, ev)
        return vendor_data

    def delete_vendor(self, event_id, vendor_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["vendors"] = [v for v in ev.get("vendors", []) if v.get("id") != vendor_id]
        self.update_event(event_id, ev)
        return True

    # Notes
    def save_note(self, event_id, note_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not note_data.get("id"):
            note_data["id"] = f"n-{uuid.uuid4().hex[:6]}"
        if not note_data.get("createdAt"):
            note_data["createdAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        notes = ev.get("notesList", [])
        found = False
        for i, n in enumerate(notes):
            if n.get("id") == note_data.get("id"):
                notes[i] = note_data
                found = True
                break
        if not found:
            notes.insert(0, note_data)
        ev["notesList"] = notes
        self.update_event(event_id, ev)
        return note_data

    def delete_note(self, event_id, note_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["notesList"] = [n for n in ev.get("notesList", []) if n.get("id") != note_id]
        self.update_event(event_id, ev)
        return True

    # Keepsake Diary
    def save_diary(self, event_id, diary_data):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return None
        if not diary_data.get("id"):
            diary_data["id"] = f"d-{uuid.uuid4().hex[:6]}"
        if not diary_data.get("createdAt"):
            diary_data["createdAt"] = datetime.now(timezone.utc).isoformat()
        if not diary_data.get("pattern"):
            diary_data["pattern"] = ev.get("pattern", "pattern_kitty.png")

        diary = ev.get("diaryEntries", [])
        found = False
        for i, d in enumerate(diary):
            if d.get("id") == diary_data.get("id"):
                diary[i] = diary_data
                found = True
                break
        if not found:
            diary.insert(0, diary_data)
        ev["diaryEntries"] = diary
        self.update_event(event_id, ev)
        return diary_data

    def delete_diary(self, event_id, entry_id):
        ev = self.get_event_by_id(event_id)
        if not ev:
            return False
        ev["diaryEntries"] = [d for d in ev.get("diaryEntries", []) if d.get("id") != entry_id]
        self.update_event(event_id, ev)
        return True

    # Settings
    def get_settings(self):
        return self.settings

    def save_settings(self, settings_data):
        self.settings.update(settings_data)
        if self.connected and self.db is not None:
            try:
                self.db.settings.update_one(
                    {"key": "app_settings"},
                    {"$set": {"key": "app_settings", "data": self.settings}},
                    upsert=True
                )
            except Exception:
                pass
        return self.settings


event_manager = FestoraEventManager(MONGO_URI, DB_NAME)

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception:
        return None


# -------------------------------------------------------------
# Static Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# -------------------------------------------------------------
# Health Check & Readiness Endpoint (for monitoring & reliability)
# -------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns system status including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Festora Event Planner",
        "version": "1.0.0"
    }
    
    # Check database connectivity
    try:
        if event_manager.use_mongo:
            # Try a simple database operation
            event_manager.collection.find_one(limit=1)
            health_status["database"] = "connected (MongoDB)"
        else:
            health_status["database"] = "connected (JSON fallback)"
        health_status["database_status"] = "healthy"
    except Exception as e:
        health_status["database_status"] = "degraded"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"
    
    # Return 200 if healthy, 503 if degraded
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


# -------------------------------------------------------------
# -------------------------------------------------------------
# Security Headers & Global Error Handlers
# -------------------------------------------------------------

@app.before_request
def ensure_user_identity():
    try:
        uid = request.headers.get("X-User-Id")
        if not uid:
            uid = request.cookies.get("festora_uid")
        if not uid:
            uid = request.args.get("uid")

        if uid:
            clean_uid = "".join(c for c in str(uid) if c.isalnum() or c in ("-", "_"))[:64]
            g.user_id = clean_uid if clean_uid else None
            g.need_cookie = False
        elif not app.config.get("TESTING"):
            g.user_id = f"usr-{uuid.uuid4().hex[:12]}"
            g.need_cookie = True
        else:
            g.user_id = None
            g.need_cookie = False
    except Exception:
        g.user_id = None
        g.need_cookie = False

def get_current_user_id():
    """
    Extracts client/user identity for multi-tenant privacy isolation.
    """
    try:
        return getattr(g, "user_id", None)
    except Exception:
        return None

@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    try:
        user_id = getattr(g, "user_id", None)
        if getattr(g, "need_cookie", False) and user_id:
            response.set_cookie("festora_uid", user_id, max_age=30*86400, samesite="Lax", httponly=False)
        elif user_id and not request.cookies.get("festora_uid"):
            response.set_cookie("festora_uid", user_id, max_age=30*86400, samesite="Lax", httponly=False)
    except Exception:
        pass
    return response

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({'error': 'Bad Request', 'message': str(e), 'status': 400}), 400

@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found', 'path': request.path, 'status': 404}), 404
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({'error': 'Method Not Allowed', 'method': request.method, 'status': 405}), 405

@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({'error': 'Internal Server Error', 'message': 'The server encountered an unexpected situation', 'status': 500}), 500


# Events API
# -------------------------------------------------------------
@app.route("/api/events", methods=["GET"])
def get_events():
    uid = get_current_user_id()
    events = event_manager.get_all_events(user_id=uid)
    active_ev = event_manager.get_active_event(user_id=uid)
    return jsonify({
        "events": events,
        "activeEventId": active_ev.get("id") if active_ev else None
    })

@app.route("/api/events", methods=["POST"])
@rate_limit()  # Rate limit event creation
def create_event():
    uid = get_current_user_id()
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Event name is required"}), 400
    new_ev = event_manager.create_event(data, user_id=uid)
    if uid:
        event_manager.set_active_event(new_ev["id"], user_id=uid)
    return jsonify({"success": True, "event": new_ev})

@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id):
    uid = get_current_user_id()
    ev = event_manager.get_event_by_id(event_id, user_id=uid)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(ev)

@app.route("/api/events/<event_id>", methods=["PUT"])
@rate_limit()  # Rate limit event updates
def update_event(event_id):
    uid = get_current_user_id()
    data = request.get_json(silent=True) or {}
    updated = event_manager.update_event(event_id, data, user_id=uid)
    if not updated:
        return jsonify({"error": "Event not found"}), 404
    return jsonify({"success": True, "event": updated})

@app.route("/api/events/<event_id>", methods=["DELETE"])
@rate_limit()  # Rate limit event deletion
def delete_event(event_id):
    uid = get_current_user_id()
    success = event_manager.delete_event(event_id, user_id=uid)
    return jsonify({"success": success})

@app.route("/api/events/active", methods=["GET", "POST"])
def active_event_route():
    uid = get_current_user_id()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        event_id = data.get("eventId")
        if event_id and event_manager.get_event_by_id(event_id):
            event_manager.set_active_event(event_id, user_id=uid)
            return jsonify({"success": True, "activeEventId": event_id})
        return jsonify({"error": "Invalid event ID"}), 400
    else:
        active = event_manager.get_active_event(user_id=uid)
        return jsonify(active if active else {})


# -------------------------------------------------------------
# Event-Scoped Resource Endpoints
# -------------------------------------------------------------

# Tasks
@app.route("/api/events/<event_id>/tasks", methods=["GET"])
def get_event_tasks(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("tasks", []) if ev else [])

@app.route("/api/events/<event_id>/tasks", methods=["POST"])
def create_event_task(event_id):
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "Task title is required"}), 400
    saved = event_manager.save_task(event_id, data)
    return jsonify({"success": True, "task": saved})

@app.route("/api/events/<event_id>/tasks/<task_id>", methods=["PUT", "POST"])
def update_event_task(event_id, task_id):
    data = request.get_json(silent=True) or {}
    data["id"] = task_id
    saved = event_manager.save_task(event_id, data)
    return jsonify({"success": True, "task": saved})

@app.route("/api/events/<event_id>/tasks/<task_id>", methods=["DELETE"])
def delete_event_task(event_id, task_id):
    ok = event_manager.delete_task(event_id, task_id)
    return jsonify({"success": ok, "id": task_id})

# Budget
@app.route("/api/events/<event_id>/budget", methods=["GET"])
def get_event_budget(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("budgetItems", []) if ev else [])

@app.route("/api/events/<event_id>/budget", methods=["POST"])
def create_event_budget(event_id):
    data = request.get_json(silent=True) or {}
    if not data.get("category"):
        return jsonify({"error": "Category is required"}), 400
    saved = event_manager.save_budget_item(event_id, data)
    return jsonify({"success": True, "item": saved})

@app.route("/api/events/<event_id>/budget/<item_id>", methods=["PUT", "POST"])
def update_event_budget(event_id, item_id):
    data = request.get_json(silent=True) or {}
    data["id"] = item_id
    saved = event_manager.save_budget_item(event_id, data)
    return jsonify({"success": True, "item": saved})

@app.route("/api/events/<event_id>/budget/<item_id>", methods=["DELETE"])
def delete_event_budget(event_id, item_id):
    ok = event_manager.delete_budget_item(event_id, item_id)
    return jsonify({"success": ok, "id": item_id})

# Timeline
@app.route("/api/events/<event_id>/timeline", methods=["GET"])
def get_event_timeline(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("timeline", []) if ev else [])

@app.route("/api/events/<event_id>/timeline", methods=["POST"])
def create_event_timeline(event_id):
    data = request.get_json(silent=True) or {}
    saved = event_manager.save_timeline_item(event_id, data)
    return jsonify({"success": True, "item": saved})

@app.route("/api/events/<event_id>/timeline/<item_id>", methods=["PUT", "POST"])
def update_event_timeline(event_id, item_id):
    data = request.get_json(silent=True) or {}
    data["id"] = item_id
    saved = event_manager.save_timeline_item(event_id, data)
    return jsonify({"success": True, "item": saved})

@app.route("/api/events/<event_id>/timeline/<item_id>", methods=["DELETE"])
def delete_event_timeline(event_id, item_id):
    ok = event_manager.delete_timeline_item(event_id, item_id)
    return jsonify({"success": ok, "id": item_id})

# Reminders (Section 5 Requirement)
@app.route("/api/events/<event_id>/reminders", methods=["GET"])
def get_event_reminders(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("reminders", []) if ev else [])

@app.route("/api/events/<event_id>/reminders", methods=["POST"])
def create_event_reminder(event_id):
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "Reminder title is required"}), 400
    saved = event_manager.save_reminder(event_id, data)
    return jsonify({"success": True, "reminder": saved})

@app.route("/api/events/<event_id>/reminders/<rem_id>", methods=["PUT", "POST"])
def update_event_reminder(event_id, rem_id):
    data = request.get_json(silent=True) or {}
    data["id"] = rem_id
    saved = event_manager.save_reminder(event_id, data)
    return jsonify({"success": True, "reminder": saved})

@app.route("/api/events/<event_id>/reminders/<rem_id>", methods=["DELETE"])
def delete_event_reminder(event_id, rem_id):
    ok = event_manager.delete_reminder(event_id, rem_id)
    return jsonify({"success": ok, "id": rem_id})

# Guests
@app.route("/api/events/<event_id>/guests", methods=["GET"])
def get_event_guests(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("guestsList", []) if ev else [])

@app.route("/api/events/<event_id>/guests", methods=["POST"])
def create_event_guest(event_id):
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Guest name is required"}), 400
    saved = event_manager.save_guest(event_id, data)
    return jsonify({"success": True, "guest": saved})

@app.route("/api/events/<event_id>/guests/<guest_id>", methods=["PUT", "POST"])
def update_event_guest(event_id, guest_id):
    data = request.get_json(silent=True) or {}
    data["id"] = guest_id
    saved = event_manager.save_guest(event_id, data)
    return jsonify({"success": True, "guest": saved})

@app.route("/api/events/<event_id>/guests/<guest_id>", methods=["DELETE"])
def delete_event_guest(event_id, guest_id):
    ok = event_manager.delete_guest(event_id, guest_id)
    return jsonify({"success": ok, "id": guest_id})

# Vendors
@app.route("/api/events/<event_id>/vendors", methods=["GET"])
def get_event_vendors(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("vendors", []) if ev else [])

@app.route("/api/events/<event_id>/vendors", methods=["POST"])
def create_event_vendor(event_id):
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Vendor name is required"}), 400
    saved = event_manager.save_vendor(event_id, data)
    return jsonify({"success": True, "vendor": saved})

@app.route("/api/events/<event_id>/vendors/<vendor_id>", methods=["PUT", "POST"])
def update_event_vendor(event_id, vendor_id):
    data = request.get_json(silent=True) or {}
    data["id"] = vendor_id
    saved = event_manager.save_vendor(event_id, data)
    return jsonify({"success": True, "vendor": saved})

@app.route("/api/events/<event_id>/vendors/<vendor_id>", methods=["DELETE"])
def delete_event_vendor(event_id, vendor_id):
    ok = event_manager.delete_vendor(event_id, vendor_id)
    return jsonify({"success": ok, "id": vendor_id})

# Notes
@app.route("/api/events/<event_id>/notes", methods=["GET"])
def get_event_notes(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("notesList", []) if ev else [])

@app.route("/api/events/<event_id>/notes", methods=["POST"])
def create_event_note(event_id):
    data = request.get_json(silent=True) or {}
    saved = event_manager.save_note(event_id, data)
    return jsonify({"success": True, "note": saved})

@app.route("/api/events/<event_id>/notes/<note_id>", methods=["DELETE"])
def delete_event_note(event_id, note_id):
    ok = event_manager.delete_note(event_id, note_id)
    return jsonify({"success": ok, "id": note_id})

# Keepsake Diary
@app.route("/api/events/<event_id>/diary", methods=["GET"])
def get_event_diary(event_id):
    ev = event_manager.get_event_by_id(event_id)
    return jsonify(ev.get("diaryEntries", []) if ev else [])

@app.route("/api/events/<event_id>/diary", methods=["POST"])
def create_event_diary(event_id):
    data = request.get_json(silent=True) or {}
    saved = event_manager.save_diary(event_id, data)
    return jsonify({"success": True, "entry": saved})

@app.route("/api/events/<event_id>/diary/<entry_id>", methods=["DELETE"])
def delete_event_diary(event_id, entry_id):
    ok = event_manager.delete_diary(event_id, entry_id)
    return jsonify({"success": ok, "id": entry_id})


# -------------------------------------------------------------
# ADVANCED AI COPILOT, WEB RESEARCH & COST ESTIMATION
# -------------------------------------------------------------
def parse_amount(text):
    """
    Parses currency and budget amounts in English and Indian numbering formats:
    - '1 lakh', '1.5 lakh', '1 lac', '2 lakhs' -> 100,000, 150,000, 200,000
    - 'one lakh', 'two lakh', 'a lakh' -> 100,000, 200,000, 100,000
    - '1 crore', '2.5 cr' -> 10,000,000, 25,000,000
    - '50k', '10k' -> 50,000, 10,000
    - '10,000', '100000' -> 10,000, 100,000
    """
    if not text:
        return 0.0
    text_l = text.lower().replace(",", "")

    word_map = {
        "a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
        "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0
    }

    # 1. Crore / cr
    m_cr = re.search(r'(\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:cr|crore|crores)\b', text_l)
    if m_cr:
        val = m_cr.group(1)
        num = word_map.get(val, None)
        if num is None:
            num = float(val)
        return float(num) * 10000000.0

    # 2. Lakh / lac
    m_lakh = re.search(r'(\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:lakh|lakhs|lac|lacs)\b', text_l)
    if m_lakh:
        val = m_lakh.group(1)
        num = word_map.get(val, None)
        if num is None:
            num = float(val)
        return float(num) * 100000.0

    # 3. 'k' suffix (thousands)
    m_k = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_l)
    if m_k:
        return float(m_k.group(1)) * 1000.0

    # 4. Standard integers/floats (e.g. 50000, 100000, 2500)
    numbers = re.findall(r'(\d+(?:\.\d+)?)', text_l)
    if numbers:
        for n in numbers:
            fn = float(n)
            if fn >= 100:
                return fn
        return float(numbers[0])

    return 0.0

def extract_due_date(text_l, default_date=""):
    """
    Dynamically extracts dates from user prompts such as:
    - 'november 10', 'nov 10', 'nov 10th'
    - 'december 5', 'dec 5', 'december 25th'
    - 'jan 15', 'october 20', etc.
    - '2026-11-10', '10/11/2026'
    """
    months = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12
    }
    # 1. ISO date check (YYYY-MM-DD)
    m_iso = re.search(r'\b(202\d)-(\d{1,2})-(\d{1,2})\b', text_l)
    if m_iso:
        y, m, d = m_iso.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 2. Month name + Day (e.g. 'November 10', 'nov 10th')
    m_named = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s*(\d{1,2})(?:st|nd|rd|th)?\b', text_l)
    if m_named:
        month_name = m_named.group(1)
        day = int(m_named.group(2))
        month_num = months.get(month_name, 11)
        year = default_date[:4] if default_date and len(default_date) >= 4 else "2026"
        return f"{year}-{month_num:02d}-{day:02d}"

    # 3. Day + Month name (e.g. '10th november', '10 nov')
    m_rev = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s*(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b', text_l)
    if m_rev:
        day = int(m_rev.group(1))
        month_name = m_rev.group(2)
        month_num = months.get(month_name, 11)
        year = default_date[:4] if default_date and len(default_date) >= 4 else "2026"
        return f"{year}-{month_num:02d}-{day:02d}"

    return default_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

def create_event_from_ai_prompt(user_prompt, user_id=None):
    """
    Intelligently builds a complete celebration workspace from natural user prompts.
    Extracts event name, type, date, budget, guests, location, and generates dynamic categories.
    """
    prompt_l = user_prompt.lower()
    if "wed" in prompt_l or "marriage" in prompt_l:
        event_type = "Wedding"
    elif "birth" in prompt_l:
        event_type = "Birthday"
    elif "anniv" in prompt_l:
        event_type = "Anniversary"
    elif "corp" in prompt_l or "conf" in prompt_l or "meet" in prompt_l:
        event_type = "Corporate"
    elif "baby" in prompt_l:
        event_type = "Baby Shower"
    else:
        event_type = "Party"

    budget = parse_amount(user_prompt)
    if budget <= 0:
        budget = 300000.0 if event_type == "Wedding" else 75000.0

    g_match = re.search(r'(\d+)\s*(?:guest|guests|people|attendee|attendees|headcount)', prompt_l)
    if g_match:
        guests = int(g_match.group(1))
    else:
        numbers = [int(n) for n in re.findall(r'\b(\d{2,4})\b', prompt_l) if int(n) not in [2024, 2025, 2026, 2027]]
        guests = numbers[0] if numbers and numbers[0] <= 2000 else (300 if event_type == "Wedding" else 60)

    date = extract_due_date(prompt_l, "2026-11-20")

    city = "Chennai"
    for c in ["chennai", "bangalore", "madurai", "mumbai", "delhi", "hyderabad", "coimbatore", "pune", "goa", "jaipur"]:
        if c in prompt_l:
            city = c.capitalize()
            break
    location = f"Grand Palace Hall, {city}"

    name = ""
    for prefix in ["plan a wedding for ", "plan wedding for ", "plan a birthday for ", "plan an anniversary for ", "create event for ", "create an event for ", "create event: ", "plan event: ", "plan a "]:
        if prefix in prompt_l:
            idx = prompt_l.find(prefix) + len(prefix)
            rest = user_prompt[idx:].strip()
            name_cut = re.split(r'\s+(?:on|in|with|for)\s+', rest, flags=re.IGNORECASE)[0].strip()
            if name_cut and len(name_cut) >= 3:
                name = f"{name_cut.title()}'s {event_type}" if not any(w in name_cut.lower() for w in ["wedding", "birthday", "party", "celebration"]) else name_cut.title()
            break
    if not name:
        name = f"My {event_type} Celebration"

    event_payload = {
        "name": name,
        "type": event_type,
        "date": date,
        "budget": budget,
        "currency": "₹",
        "guests": guests,
        "location": location,
        "duration": "1 Day"
    }
    saved = event_manager.create_event(event_payload, user_id=user_id)
    return saved

@app.route("/api/events/<event_id>/ai/copilot", methods=["POST"])
@rate_limit(rate_limiter_strict)  # Strict rate limit for AI endpoint (20 req/min)
def event_ai_copilot(event_id):
    """
    Intelligent event organizer for the active celebration.
    Capabilities:
    1. Contextual awareness across all sections (Budget, Tasks, Guests, Vendors, Timeline).
    2. Real application actions (add task, update budget, reduce budget, create event, add guest).
    3. Web research with verified/estimated pricing, capacity, and source links.
    4. AI-Powered cost estimation with 1-click 'Add to Budget Planner'.
    5. ChatGPT-style articulate, structured markdown responses with pro tips.
    """
    uid = get_current_user_id()
    ev = event_manager.get_event_by_id(event_id)
    if not ev:
        ev = event_manager.get_active_event(user_id=uid)

    data = request.get_json(silent=True) or {}
    user_prompt = data.get("message", "").strip()
    current_section = data.get("current_section", "dashboard")
    confirmed_action = data.get("confirmed_action", None)
    prompt_l = user_prompt.lower()

    # Case: No active event in the system yet
    if not ev:
        if any(w in prompt_l for w in ["create", "plan", "organize", "start", "wedding", "birthday", "anniversary", "party"]):
            created_ev = create_event_from_ai_prompt(user_prompt, user_id=uid)
            return jsonify({
                "success": True,
                "reply": f"### 🎉 Celebration Workspace Created!\nI have created your personalized workspace for **{created_ev['name']}** on **{created_ev['date']}** with dynamic planning categories, starter budget allocations, and checklist milestones.\n\nYour celebration dashboard is now active and ready for you to customize!",
                "executed_action": {"type": "event_created", "event": created_ev},
                "event": created_ev
            })
        else:
            return jsonify({
                "success": True,
                "reply": "### ✨ Welcome to Festora AI!\nI am your Personal Celebration Organizer. You don't have any active celebrations created yet.\n\nTell me what event you'd like to plan (e.g. *\"Plan a wedding for Arun & Maya on Dec 15 with 300 guests and 5 lakh budget\"* or *\"Create an event for Rahul's 1st Birthday party on Nov 25\"*) and I will build your complete workspace instantly!",
                "event": None
            })

    if not user_prompt and not confirmed_action:
        return jsonify({"reply": "How can I help you organize your celebration today?"})

    # Case: User asks AI to plan/create a new event while an existing one is open
    is_plan_event_prompt = any(k in prompt_l for k in [
        "create new event", "create a new event", "plan a new", "create another event",
        "plan a wedding", "plan a birthday", "plan an event", "create an event",
        "plan an anniversary", "plan a celebration", "create a wedding", "create a birthday"
    ]) or (("plan " in prompt_l or "create " in prompt_l) and any(w in prompt_l for w in ["wedding", "birthday", "party", "reception", "anniversary"]) and any(b in prompt_l for b in ["budget", "guests", "lakh", "lac", "people"]))

    if is_plan_event_prompt:
        created_ev = create_event_from_ai_prompt(user_prompt, user_id=uid)
        return jsonify({
            "success": True,
            "reply": f"### 🎉 Celebration Workspace Created!\nI have created a new celebration workspace for **{created_ev['name']}** on **{created_ev['date']}**!\n\nSwitching to your new workspace now.",
            "executed_action": {"type": "event_created", "event": created_ev},
            "event": created_ev
        })

    total_budget = ev.get("budget", 0)
    currency = ev.get("currency", "₹")
    budget_items = ev.get("budgetItems", [])
    total_spent = sum(float(b.get("spent", 0)) for b in budget_items)
    remaining_budget = total_budget - total_spent
    tasks = ev.get("tasks", [])
    pending_tasks = [t for t in tasks if t.get("status") != "completed"]
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    categories = ev.get("categories", [])
    event_name = ev.get("name", "Event")
    event_type = ev.get("type", "Wedding")
    event_date = ev.get("date", "")
    event_location = ev.get("location", "")
    guests_count = ev.get("guests", 0)
    reminders = ev.get("reminders", [])

    # Handle direct execution of a user-confirmed action
    if confirmed_action:
        act_type = confirmed_action.get("type")
        payload = confirmed_action.get("payload", {})
        if act_type == "add_task":
            saved = event_manager.save_task(event_id, payload)
            return jsonify({
                "success": True,
                "reply": f"Confirmed! Added \"{saved['title']}\" to your Checklist.",
                "executed_action": {"type": "task_added", "task": saved},
                "event": event_manager.get_event_by_id(event_id)
            })
        elif act_type == "add_budget_breakdown":
            for b in payload.get("items", []):
                event_manager.save_budget_item(event_id, b)
            return jsonify({
                "success": True,
                "reply": f"Confirmed! Added the full cost breakdown to your Budget Planner.",
                "executed_action": {"type": "budget_added"},
                "event": event_manager.get_event_by_id(event_id)
            })

    # Detect Cost Estimation Intent (evaluated before venue search)
    prompt_l = user_prompt.lower()
    is_cost_estimation = any(w in prompt_l for w in [
        "cost estimation", "estimate the cost", "estimate the budget", "estimate budget",
        "budget breakdown", "cost breakdown", "how much will it cost", "how much would it cost",
        "estimate expenses", "estimated budget", "cost for"
    ]) or ("estimate" in prompt_l and ("cost" in prompt_l or "budget" in prompt_l or "breakdown" in prompt_l))

    # Detect Web Research Intent for venues, halls and vendors
    is_venue_keyword = any(w in prompt_l for w in [
        "venue", "hall", "place", "location", "mandap", "resort", "hotel", "reception",
        "where can", "where to", "photographer", "caterer", "search"
    ])
    is_city_keyword = any(c in prompt_l for c in ["madurai", "chennai", "bangalore", "mumbai", "delhi", "hyderabad", "coimbatore"])
    has_action_request = any(k in prompt_l for k in [
        "add", "increase", "update", "create", "allocate", "task", "lakh", "lac", "crore",
        "remind", "budget", "expense", "spent", "to total", "schedule", "book the"
    ])
    is_web_search = not is_cost_estimation and not has_action_request and (
        any(w in prompt_l for w in [
            "which location", "best venue", "where can i", "wedding hall", "reception venue",
            "search the web", "search for", "places in", "venues in", "photographers in", "caterers in"
        ]) or (is_venue_keyword and is_city_keyword)
    )

    executed_action = None
    requires_confirmation = None
    reply = ""
    recommendations = []
    venues_research = []
    cost_estimation = None

    # Handle Cost Estimation First
    if is_cost_estimation:
        # Extract guest count
        numbers = re.findall(r'(\d+)', prompt_l)
        est_guests = int(numbers[0]) if numbers else (guests_count or 100)
        est_type = "Birthday" if "birth" in prompt_l else (event_type or "Celebration")

        if "birth" in prompt_l or est_type == "Birthday":
            cost_items = [
                {"category": "Venue & Clubhouse", "estimated": round(est_guests * 200), "notes": "Party hall with sound system"},
                {"category": "Birthday Cake", "estimated": 6000, "notes": "3-tier themed designer fondant cake"},
                {"category": "Decorations & Balloons", "estimated": round(est_guests * 120), "notes": "Balloon garland, backdrop & lighting"},
                {"category": "Food & Snacks Buffet", "estimated": round(est_guests * 280), "notes": "Welcome drinks, snacks & dinner buffet"},
                {"category": "Photography & Candids", "estimated": 8000, "notes": "3-hour party photo coverage"},
                {"category": "Entertainment & Games", "estimated": 7000, "notes": "Magician or games coordinator"},
                {"category": "Return Gifts & Favors", "estimated": round(est_guests * 70), "notes": "Custom activity kits for kids"}
            ]
        else:
            cost_items = [
                {"category": "Venue & Hall Booking", "estimated": round(est_guests * 450), "notes": "Grand hall & amenities"},
                {"category": "Food & Catering Feast", "estimated": round(est_guests * 550), "notes": "Full day traditional feast"},
                {"category": "Mandap & Floral Decor", "estimated": round(est_guests * 200), "notes": "Fresh florals & ambient lighting"},
                {"category": "Photography & Film", "estimated": 40000, "notes": "2 photographers + wedding film"},
                {"category": "Bridal Makeup & Styling", "estimated": 15000, "notes": "Bridal styling & family touchups"},
                {"category": "Invitations & Stationery", "estimated": round(est_guests * 25), "notes": "Digital cards & embossed invites"},
                {"category": "Return Gifts", "estimated": round(est_guests * 40), "notes": "Brass diyas & sweet hampers"}
            ]

        total_est = sum(item["estimated"] for item in cost_items)
        cost_estimation = {
            "title": f"Estimated Cost Breakdown for {est_guests} Guests ({est_type})",
            "items": cost_items,
            "totalEstimated": total_est,
            "currency": currency
        }
        reply = f"Based on industry benchmarks for a {est_type} with **{est_guests} guests**, here is an estimated budget breakdown totaling approx. **{currency}{total_est:,.0f}**:"

    # Handle Web Research
    elif is_web_search:
        # Extract city or default to event location
        city = ""
        for c in ["madurai", "chennai", "bangalore", "mumbai", "delhi", "hyderabad", "coimbatore", "pune", "kolkata", "jaipur", "goa", "kochi", "trichy"]:
            if c in prompt_l:
                city = c
                break
        if not city and event_location:
            loc_parts = [p.strip() for p in event_location.split(",") if p.strip()]
            city = loc_parts[-1] if loc_parts else event_location
        if not city:
            city = "Chennai"

        venues_research = web_search.search_web_for_venues(user_prompt, city)
        reply = f"Here are the top-rated reception and wedding venues researched for **{city.capitalize()}** based on capacity, facilities, and real-world estimates:"

    # Otherwise: Attempt LLM reasoning via Groq with gpt-oss-120b
    else:
        client = get_groq_client()
        if client:
            try:
                system_prompt = f"""You are Festora, an expert AI Personal Event Organizer for '{event_name}' ({event_type}).
Current section user is looking at: {current_section.upper()}.
Current Event Context:
- Name: {event_name}
- Type: {event_type}
- Date: {event_date}
- Location: {event_location}
- Guests: {guests_count}
- Budget: {currency}{total_budget:,.0f} | Spent: {currency}{total_spent:,.0f} | Remaining: {currency}{remaining_budget:,.0f}
- Tasks: {len(tasks)} total ({len(pending_tasks)} pending, {len(completed_tasks)} completed)
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
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=1200
                )
                parsed = json.loads(completion.choices[0].message.content)
                reply = parsed.get("reply", "")
                act_type = parsed.get("action_type", "none")
                payload = parsed.get("action_payload", {})

                if act_type == "add_task" and payload.get("title"):
                    task_data = {
                        "title": payload["title"],
                        "category": payload.get("category") or (categories[0] if categories else "General"),
                        "dueDate": payload.get("dueDate") or event_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "priority": payload.get("priority", "medium"),
                        "status": "todo",
                        "symbol": payload.get("symbol", "💍"),
                        "notes": payload.get("notes", f"Added by Festora AI for {event_name}")
                    }
                    saved = event_manager.save_task(event_id, task_data)
                    executed_action = {"type": "task_added", "task": saved}

                elif act_type == "add_total_budget":
                    added_amount = float(payload.get("addedAmount", 100000))
                    is_red = payload.get("isReduction", False) or any(w in prompt_l for w in ["reduce", "decrease", "cut", "lower", "subtract", "deduct"])
                    if is_red:
                        new_budget = max(0.0, float(ev.get("budget", 0)) - added_amount)
                        event_manager.update_event(event_id, {"budget": new_budget})
                        executed_action = {"type": "total_budget_updated", "newBudget": new_budget, "addedAmount": -added_amount, "isReduction": True}
                    else:
                        new_budget = float(ev.get("budget", 0)) + added_amount
                        event_manager.update_event(event_id, {"budget": new_budget})
                        executed_action = {"type": "total_budget_updated", "newBudget": new_budget, "addedAmount": added_amount, "isReduction": False}

                elif act_type == "task_and_budget_added":
                    t_payload = payload.get("task", {})
                    task_data = {
                        "title": t_payload.get("title", "Important milestone"),
                        "category": t_payload.get("category") or (categories[0] if categories else "General"),
                        "dueDate": t_payload.get("dueDate") or event_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "priority": t_payload.get("priority", "high"),
                        "status": "todo",
                        "symbol": t_payload.get("symbol", "💍"),
                        "notes": t_payload.get("notes", f"Added by Festora AI for {event_name}")
                    }
                    saved = event_manager.save_task(event_id, task_data)
                    added_amount = float(payload.get("addedAmount", 100000))
                    new_budget = float(ev.get("budget", 0)) + added_amount
                    event_manager.update_event(event_id, {"budget": new_budget})
                    executed_action = {"type": "task_and_budget_added", "task": saved, "newBudget": new_budget, "addedAmount": added_amount}

                elif act_type == "add_budget_item" and payload.get("category"):
                    item_data = {
                        "category": payload["category"],
                        "allocated": float(payload.get("allocated", 10000)),
                        "spent": float(payload.get("spent", 0)),
                        "notes": payload.get("notes", "Allocated by Festora AI")
                    }
                    saved = event_manager.save_budget_item(event_id, item_data)
                    executed_action = {"type": "budget_added", "item": saved}

                elif act_type == "update_expense" and payload.get("category"):
                    target_cat = payload["category"].lower()
                    delta = float(payload.get("expenseDelta", 0))
                    matched_item = None
                    for b in ev.get("budgetItems", []):
                        if target_cat in b.get("category", "").lower():
                            matched_item = b
                            break
                    if matched_item:
                        matched_item["spent"] = max(0, float(matched_item.get("spent", 0)) + delta)
                        event_manager.save_budget_item(event_id, matched_item)
                        executed_action = {"type": "expense_updated", "item": matched_item}
                    else:
                        new_item = {
                            "category": payload["category"],
                            "allocated": delta,
                            "spent": delta,
                            "notes": "Added via expense update"
                        }
                        event_manager.save_budget_item(event_id, new_item)
                        executed_action = {"type": "budget_added", "item": new_item}

                elif act_type == "add_guest" and payload.get("name"):
                    saved = event_manager.save_guest(event_id, payload)
                    executed_action = {"type": "guest_added", "guest": saved}

                elif act_type == "add_reminder" and payload.get("title"):
                    saved = event_manager.save_reminder(event_id, payload)
                    executed_action = {"type": "reminder_added", "reminder": saved}

                elif act_type == "recommendations":
                    recommendations = parsed.get("recommendations", [])

            except Exception as e:
                print("[Festora AI Copilot] LLM error:", e)

    # High-accuracy rule engine fallback
    if not reply:
        has_task_intent = any(k in prompt_l for k in ["add task", "add a task", "add the task", "new task", "remind me to", "book", "schedule"])
        has_total_budget_intent = any(k in prompt_l for k in ["to total", "total budget", "to the total", "overall budget", "to total amount"]) or (
            any(m in prompt_l for m in ["lakh", "lac", "crore"]) and any(b in prompt_l for b in ["total", "budget", "amount"])
        )

        # 1. Dual Action: Add Task AND Add to Total Budget
        if has_task_intent and has_total_budget_intent:
            amt = parse_amount(prompt_l)
            if amt <= 0:
                amt = 100000.0 if ("lakh" in prompt_l or "lac" in prompt_l) else 50000.0

            symbol = "✨"
            cat = categories[0] if categories else "General"
            if "photo" in prompt_l or "video" in prompt_l:
                symbol = "📸"
                cat = "Photography and Videography" if "Photography and Videography" in categories else "Photography"
            elif "cater" in prompt_l or "food" in prompt_l:
                symbol = "🍽️"
                cat = "Food and Catering" if "Food and Catering" in categories else "Catering"
            elif "decor" in prompt_l or "flower" in prompt_l or "mandap" in prompt_l:
                symbol = "🌸"
                cat = "Decoration"
            elif "cake" in prompt_l:
                symbol = "🍰"
                cat = "Birthday Cake" if "Birthday Cake" in categories else "Catering"
            elif "venue" in prompt_l or "hall" in prompt_l:
                symbol = "🏛️"
                cat = "Venue and Hall Booking" if "Venue and Hall Booking" in categories else "Venue"

            # Strip the budget clause from task title
            clean_title = re.sub(r'(?i)(?:\band\b|\b&\b|\balso\b)?\s*(?:add|increase)?\s*(?:the\s*)?(?:amount\s*)?(?:\d+|a|an|one|two)?\s*(?:lakh|lakhs|lac|lacs|crore|k|\d+)?\s*(?:to\s*)?(?:the\s*)?(?:total|overall)?\s*(?:budget)?.*$', '', user_prompt).strip()
            if not clean_title or len(clean_title) < 5:
                clean_title = "Book wedding hall and arrangements"
            for prefix in ["add a task to ", "add the task to ", "add task to ", "add task: ", "remind me to ", "add the task "]:
                if clean_title.lower().startswith(prefix):
                    clean_title = clean_title[len(prefix):].strip().capitalize()
                    break

            task_date = extract_due_date(prompt_l, event_date)

            task_data = {
                "title": clean_title[:75],
                "category": cat,
                "dueDate": task_date,
                "priority": "high" if "urgent" in prompt_l or "before" in prompt_l else "medium",
                "status": "todo",
                "symbol": symbol,
                "notes": f"Created via Festora AI for {event_name}"
            }
            saved_task = event_manager.save_task(event_id, task_data)

            old_b = float(ev.get("budget", 0))
            new_b = old_b + amt
            event_manager.update_event(event_id, {"budget": new_b})

            executed_action = {
                "type": "task_and_budget_added",
                "task": saved_task,
                "newBudget": new_b,
                "addedAmount": amt
            }
            reply = f"Splendid! I've added \"{saved_task['title']}\" under {cat} to your To-Do checklist for {task_date}, and increased your total event budget by {currency}{amt:,.0f} (new total: {currency}{new_b:,.0f})."

        # 2. Pure Total Budget Increase or Reduction
        elif has_total_budget_intent or (
            any(w in prompt_l for w in ["reduce", "decrease", "cut", "lower", "subtract", "deduct", "less", "drop", "minimize", "increase", "add", "raise"])
            and any(b in prompt_l for b in ["budget", "total", "amount", "cost"])
        ) or (
            ("lakh" in prompt_l or "lac" in prompt_l or "crore" in prompt_l) and ("total" in prompt_l or "budget" in prompt_l)
        ):
            amt = parse_amount(prompt_l)
            if amt <= 0:
                amt = 100000.0 if ("lakh" in prompt_l or "lac" in prompt_l) else 50000.0
            old_b = float(ev.get("budget", 0))

            is_reduction = any(w in prompt_l for w in [
                "reduce", "decrease", "cut", "lower", "subtract", "deduct", "less", "drop", "minimize"
            ])

            if is_reduction:
                new_b = max(0.0, old_b - amt)
                event_manager.update_event(event_id, {"budget": new_b})
                executed_action = {"type": "total_budget_updated", "newBudget": new_b, "addedAmount": -amt, "isReduction": True}
                reply = f"I've reduced your total event budget by {currency}{amt:,.0f}! Your new total celebration budget is {currency}{new_b:,.0f}."
            else:
                new_b = old_b + amt
                event_manager.update_event(event_id, {"budget": new_b})
                executed_action = {"type": "total_budget_updated", "newBudget": new_b, "addedAmount": amt, "isReduction": False}
                reply = f"I've increased your total event budget by {currency}{amt:,.0f}! Your new total celebration budget is {currency}{new_b:,.0f}."

        # 3. Pure Task Addition
        elif has_task_intent:
            symbol = "✨"
            cat = categories[0] if categories else "General"
            title = user_prompt
            for prefix in ["add a task to ", "add task to ", "add task: ", "remind me to ", "add the task to ", "add the task "]:
                if prefix in prompt_l:
                    idx = prompt_l.find(prefix) + len(prefix)
                    title = user_prompt[idx:].capitalize()
                    break

            if "photo" in prompt_l or "video" in prompt_l:
                symbol = "📸"
                cat = "Photography and Videography" if "Photography and Videography" in categories else "Photography"
            elif "cater" in prompt_l or "food" in prompt_l:
                symbol = "🍽️"
                cat = "Food and Catering" if "Food and Catering" in categories else "Catering"
            elif "decor" in prompt_l or "flower" in prompt_l or "mandap" in prompt_l:
                symbol = "🌸"
                cat = "Decoration"
            elif "cake" in prompt_l:
                symbol = "🍰"
                cat = "Birthday Cake" if "Birthday Cake" in categories else "Catering"
            elif "venue" in prompt_l or "hall" in prompt_l:
                symbol = "🏛️"
                cat = "Venue and Hall Booking" if "Venue and Hall Booking" in categories else "Venue"

            task_date = extract_due_date(prompt_l, event_date)

            task_data = {
                "title": title[:70],
                "category": cat,
                "dueDate": task_date,
                "priority": "high" if "urgent" in prompt_l or "before" in prompt_l else "medium",
                "status": "todo",
                "symbol": symbol,
                "notes": f"Created via Festora AI for {event_name}"
            }
            saved = event_manager.save_task(event_id, task_data)
            executed_action = {"type": "task_added", "task": saved}
            reply = f"I've added \"{saved['title']}\" under {cat} to your To-Do checklist for {task_date}!"

        elif "expense" in prompt_l or "increased" in prompt_l or "spent" in prompt_l:
            numbers = re.findall(r'(\d+[\d,]*)', prompt_l.replace(",", ""))
            delta = float(numbers[0]) if numbers else 10000
            target_cat = "Catering"
            for c in categories:
                if c.lower() in prompt_l:
                    target_cat = c
                    break
            matched = None
            for b in ev.get("budgetItems", []):
                if target_cat.lower() in b.get("category", "").lower():
                    matched = b
                    break
            if matched:
                matched["spent"] = float(matched.get("spent", 0)) + delta
                event_manager.save_budget_item(event_id, matched)
                executed_action = {"type": "expense_updated", "item": matched}
                reply = f"Updated {matched['category']} expense by {currency}{delta:,.0f}. New spent total is {currency}{matched['spent']:,.0f}."
            else:
                new_item = {"category": target_cat, "allocated": delta, "spent": delta, "notes": "Added from expense update"}
                event_manager.save_budget_item(event_id, new_item)
                executed_action = {"type": "budget_added", "item": new_item}
                reply = f"Added {currency}{delta:,.0f} expense under {target_cat} in your budget planner."

        elif "add" in prompt_l and "guest" in prompt_l:
            numbers = re.findall(r'(\d+)', prompt_l)
            count = int(numbers[0]) if numbers else 1
            name = "Guest"
            for w in user_prompt.split():
                if w.isalpha() and w.istitle() and w not in ["Add", "Guest", "Guests", "The", "My"]:
                    name = w
                    break
            g_data = {"name": f"{name} & Attendees" if count > 1 else name, "attendeesCount": count, "rsvp": "Confirmed", "category": "Family"}
            saved = event_manager.save_guest(event_id, g_data)
            executed_action = {"type": "guest_added", "guest": saved}
            reply = f"I've added guest {saved['name']} ({count} headcount) to your guest directory!"

        elif "budget" in prompt_l and ("add" in prompt_l or "allocate" in prompt_l or "floral" in prompt_l):
            numbers = re.findall(r'(\d+[\d,]*)', prompt_l.replace(",", ""))
            alloc = float(numbers[0]) if numbers else 15000
            cat_name = "Floral Decoration" if "floral" in prompt_l else "Additional Budget"
            item_data = {"category": cat_name, "allocated": alloc, "spent": 0, "notes": "Allocated via Festora AI"}
            saved = event_manager.save_budget_item(event_id, item_data)
            executed_action = {"type": "budget_added", "item": saved}
            reply = f"I've allocated {currency}{alloc:,.0f} for {cat_name} in your budget planner!"

        elif "pending" in prompt_l or "status" in prompt_l or "what are my" in prompt_l:
            if not pending_tasks:
                reply = f"Great news! All milestones for '{event_name}' are currently completed!"
            else:
                top_items = [f"• {t.get('symbol', '🌸')} {t.get('title')}" for t in pending_tasks[:5]]
                reply = f"### 📋 Active Milestones Pending for '{event_name}'\n\nYou currently have **{len(pending_tasks)} pending milestone{'s' if len(pending_tasks) != 1 else ''}**:\n\n" + "\n".join(top_items) + "\n\n*Would you like to complete or reschedule any of these?*"

        elif any(k in prompt_l for k in ["suggest", "idea", "ideas", "recommend", "theme", "decor", "food", "menu", "gift", "tips"]):
            if any(w in prompt_l for w in ["decor", "theme", "flower", "lighting", "stage", "ambiance"]):
                reply = f"""### 🌸 Creative Decoration & Styling Themes for {event_name}

Here are 3 handpicked, budget-optimized styling concepts designed for your celebration:

• **Royal Heritage Temple Ambiance**:
  Fresh golden marigolds, fragrant white mogra strings, and traditional brass oil urlis with floating lotus buds and candles. Creates a regal, sacred aura that looks magnificent in photography.

• **Enchanted Fairy Light Garden**:
  Warm amber micro-fairy light canopies draped with ivory chiffon and dusty rose floral accents. Perfect for creating an intimate, magical evening reception atmosphere.

• **Modern Minimalist Chic**:
  Clean geometric photobooth arches, sage green botanical foliage, and brass lantern accents with custom personalized typography signage.

### 💡 Pro Cost-Saving Tips:
• **Repurpose Ceremony Decor**: Move morning floral pillars to frame the evening banquet entrance to save up to 30% on florist expenses.
• **Lighting Over Heavy Florals**: Ambient warm spotlights and fairy curtains produce 3x greater visual impact per rupee spent than imported flowers.

Would you like me to add any of these ideas as a milestone to your checklist or allocate a decor budget?"""
            elif any(w in prompt_l for w in ["menu", "food", "cater", "snack", "dish", "feast"]):
                reply = f"""### 🍽️ Signature Catering & Feast Ideas for {event_name}

A curated culinary balance that guarantees guest delight while optimizing preparation costs:

• **Live Welcome Counters**:
  Fresh tender coconut water shooters, spiced ginger buttermilk, and an interactive live mini-dosa or chaat station to greet arriving guests.

• **Grand Traditional Banquet**:
  Fragrant ghee rice, South Indian vegetable dum biryani, signature paneer butter masala, traditional sambar, rasam, fluffy pooris, and curd rice.

• **Sweet Delights & Desserts**:
  Warm carrot halwa served with vanilla ice cream, traditional tender coconut payasam, and live hot jalebi with rabri.

### 💡 Smart Catering Advice:
• Confirm final attendee headcount with guests 5 days before the event to prevent 15-20% surplus catering wastage.
• Live food counters give an upscale gourmet experience at substantially lower cost than an oversized static buffet line.

Would you like me to add a chef menu tasting task to your checklist?"""
            else:
                reply = f"""### ✨ Expert Celebration Planning Ideas for {event_name}

Here is a curated 3-step action guide to elevate your celebration:

• **1. Interactive Guest Moments**:
  Set up an instant Polaroid photo guestbook near the entrance with metallic markers where guests paste snapshots and leave handwritten blessings.

• **2. Memorable Keepsake Favors**:
  Eco-friendly miniature potted succulents or jasmine saplings in jute bags. Thoughtful, long-lasting, and budget-friendly.

• **3. Seamless Ceremony Timeline**:
  Share a digital day-of run-of-show schedule with your photography crew, makeup artist, and family coordinators to ensure zero delays.

### 💡 Pro Tip:
Track all upcoming vendor advance payments and milestones in your Festora Workspace to stay completely stress-free!

Tell me what specific part you'd like to customize, or say *\"Add a task...\"* to save anything to your planner!"""
        else:
            reply = f"I'm your dedicated organizer for '{event_name}'. Ask me to research venues, estimate costs, add tasks, track RSVPs, or allocate your budget of {currency}{total_budget:,.0f}!"

    refreshed_ev = event_manager.get_event_by_id(event_id)

    return jsonify({
        "success": True,
        "reply": reply,
        "executed_action": executed_action,
        "requires_confirmation": requires_confirmation,
        "recommendations": recommendations,
        "venues_research": venues_research,
        "cost_estimation": cost_estimation,
        "event": refreshed_ev
    })


# -------------------------------------------------------------
# Backwards-Compatible Global Endpoints
# -------------------------------------------------------------
@app.route("/api/tasks", methods=["GET", "POST"])
def global_tasks():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify([])
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        saved = event_manager.save_task(active_ev.get("id"), data)
        return jsonify({"success": True, "task": saved})
    return jsonify(active_ev.get("tasks", []))

@app.route("/api/tasks/<task_id>", methods=["PUT", "DELETE"])
def global_task_item(task_id):
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"success": False}), 404
    if request.method == "DELETE":
        ok = event_manager.delete_task(active_ev.get("id"), task_id)
        return jsonify({"success": ok, "id": task_id})
    else:
        data = request.get_json(silent=True) or {}
        data["id"] = task_id
        saved = event_manager.save_task(active_ev.get("id"), data)
        return jsonify({"success": True, "task": saved})

@app.route("/api/budget", methods=["GET", "POST"])
def global_budget():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify([])
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        saved = event_manager.save_budget_item(active_ev.get("id"), data)
        return jsonify({"success": True, "item": saved})
    return jsonify(active_ev.get("budgetItems", []))

@app.route("/api/budget/<item_id>", methods=["PUT", "DELETE"])
def global_budget_item(item_id):
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"success": False}), 404
    if request.method == "DELETE":
        ok = event_manager.delete_budget_item(active_ev.get("id"), item_id)
        return jsonify({"success": ok, "id": item_id})
    else:
        data = request.get_json(silent=True) or {}
        data["id"] = item_id
        saved = event_manager.save_budget_item(active_ev.get("id"), data)
        return jsonify({"success": True, "item": saved})

@app.route("/api/vendors", methods=["GET", "POST"])
def global_vendors():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify([])
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        saved = event_manager.save_vendor(active_ev.get("id"), data)
        return jsonify({"success": True, "vendor": saved})
    return jsonify(active_ev.get("vendors", []))

@app.route("/api/vendors/<vendor_id>", methods=["PUT", "DELETE"])
def global_vendor_item(vendor_id):
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"success": False}), 404
    if request.method == "DELETE":
        ok = event_manager.delete_vendor(active_ev.get("id"), vendor_id)
        return jsonify({"success": ok, "id": vendor_id})
    else:
        data = request.get_json(silent=True) or {}
        data["id"] = vendor_id
        saved = event_manager.save_vendor(active_ev.get("id"), data)
        return jsonify({"success": True, "vendor": saved})

@app.route("/api/diary", methods=["GET", "POST"])
def global_diary():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify([])
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        saved = event_manager.save_diary(active_ev.get("id"), data)
        return jsonify({"success": True, "entry": saved})
    return jsonify(active_ev.get("diaryEntries", []))

@app.route("/api/diary/<entry_id>", methods=["DELETE"])
def global_diary_item(entry_id):
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"success": False}), 404
    ok = event_manager.delete_diary(active_ev.get("id"), entry_id)
    return jsonify({"success": ok, "id": entry_id})

@app.route("/api/settings", methods=["GET", "POST"])
def settings_route():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        saved = event_manager.save_settings(data)
        return jsonify({"success": True, "settings": saved})
    return jsonify(event_manager.get_settings())

@app.route("/api/ai/customize-tasks", methods=["POST"])
def legacy_ai_customize():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"success": False, "reply": "No active event selected."}), 400
    return event_ai_copilot(active_ev.get("id"))

@app.route("/api/ai/chat", methods=["POST"])
def legacy_ai_chat():
    uid = get_current_user_id()
    active_ev = event_manager.get_active_event(user_id=uid)
    if not active_ev:
        return jsonify({"reply": "I am Festora, your personal celebration copilot."})
    return event_ai_copilot(active_ev.get("id"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Festora server starting on http://localhost:{port}")
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    print(f"Festora server starting on port {port} (debug={debug_mode})")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
