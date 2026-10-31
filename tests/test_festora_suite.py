"""
FESTORA - AI-Powered Personal Event Organizer
Comprehensive Automated Test Suite for Hack2Skill Evaluation
Covers:
- Code Quality & Clean REST API JSON contracts
- Security (Headers, 404/405/400 JSON handling, Input Sanitization)
- Event Scoped Workspaces (Tasks, Budget, Timeline, Guests, Vendors, Notes, Diary)
- AI Copilot Capabilities (Dual Action, Budget Math, Cost Estimation, Web Research, NLP Creation)
- Resilience & Persistence Fallback
"""

import unittest
import json
import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, event_manager


class FestoraEvaluationTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def setUp(self):
        # Create a clean isolated test event for each test
        self.test_event_data = {
            "name": "Hackathon Royal Celebration",
            "type": "Wedding",
            "date": "2026-11-28",
            "location": "Grand Palace Hall, Chennai",
            "guests": 250,
            "budget": 450000,
            "currency": "₹",
            "duration": "1 Day",
            "theme": "kitty-cozy",
            "pattern": "pattern_kitty.png"
        }
        res = self.client.post("/api/events", json=self.test_event_data)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.test_event = data.get("event")
        self.test_event_id = self.test_event["id"]

    def tearDown(self):
        # Clean up the test event
        if hasattr(self, "test_event_id") and self.test_event_id:
            self.client.delete(f"/api/events/{self.test_event_id}")

    # =========================================================================
    # 1. SECURITY & ERROR HANDLING TESTS
    # =========================================================================
    def test_security_headers_present(self):
        """Security: Verify standard OWASP security headers on all responses"""
        res = self.client.get("/api/events")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(res.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_404_json_error_handling(self):
        """Security & Quality: Missing API endpoints must return structured JSON, not raw HTML"""
        res = self.client.get("/api/nonexistent_route_endpoint")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), 404)
        self.assertIn("error", data)

    def test_400_validation_error(self):
        """Quality: Empty/invalid event creation returns HTTP 400 Bad Request"""
        res = self.client.post("/api/events", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)

    def test_405_method_not_allowed(self):
        """Quality: Unsupported HTTP verbs return 405 Method Not Allowed in clean JSON"""
        res = self.client.delete("/api/events")
        self.assertEqual(res.status_code, 405)
        data = res.get_json()
        self.assertEqual(data.get("status"), 405)

    # =========================================================================
    # 2. EVENT WORKSPACE & LIFECYCLE TESTS
    # =========================================================================
    def test_event_dynamic_category_generation(self):
        """Problem Statement: Wedding event must dynamically generate wedding categories"""
        self.assertIn("categories", self.test_event)
        cats = self.test_event["categories"]
        self.assertTrue(any("Venue" in c for c in cats), "Should generate Venue category")
        self.assertTrue(any("Food" in c or "Catering" in c for c in cats), "Should generate Catering category")
        self.assertTrue(any("Decoration" in c for c in cats), "Should generate Decoration category")

    def test_event_retrieval_and_update(self):
        """Quality: Event details can be retrieved and updated accurately"""
        # Retrieve
        res = self.client.get(f"/api/events/{self.test_event_id}")
        self.assertEqual(res.status_code, 200)
        ev = res.get_json()
        self.assertEqual(ev["name"], "Hackathon Royal Celebration")

        # Update budget and location
        res_up = self.client.put(f"/api/events/{self.test_event_id}", json={
            "budget": 500000,
            "location": "ITC Grand Chola, Chennai"
        })
        self.assertEqual(res_up.status_code, 200)
        up_data = res_up.get_json()
        self.assertEqual(up_data["event"]["budget"], 500000)
        self.assertEqual(up_data["event"]["location"], "ITC Grand Chola, Chennai")

    # =========================================================================
    # 3. TASK MANAGEMENT & ASANA CHECKLIST TESTS
    # =========================================================================
    def test_task_crud_lifecycle(self):
        """Functionality: Create, mark complete, and delete a milestone task"""
        # 1. Create Task
        new_task = {
            "title": "Design Traditional Floral Arch",
            "category": "Decoration",
            "dueDate": "2026-11-20",
            "priority": "high",
            "symbol": "🌸",
            "notes": "South Indian temple style marigold garland"
        }
        res = self.client.post(f"/api/events/{self.test_event_id}/tasks", json=new_task)
        self.assertEqual(res.status_code, 200)
        saved = res.get_json().get("task")
        task_id = saved["id"]
        self.assertEqual(saved["title"], "Design Traditional Floral Arch")
        self.assertEqual(saved["priority"], "high")

        # 2. Update Task Status
        res_up = self.client.put(f"/api/events/{self.test_event_id}/tasks/{task_id}", json={
            "status": "completed"
        })
        self.assertEqual(res_up.status_code, 200)
        self.assertEqual(res_up.get_json()["task"]["status"], "completed")

        # 3. Delete Task
        res_del = self.client.delete(f"/api/events/{self.test_event_id}/tasks/{task_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.get_json().get("success"))

    # =========================================================================
    # 4. BUDGET PLANNER TESTS
    # =========================================================================
    def test_budget_item_crud_lifecycle(self):
        """Functionality: Create and update allocated and spent budget items"""
        # Create budget item
        item = {
            "category": "Photography & Videography",
            "allocated": 45000,
            "spent": 20000,
            "notes": "Includes 2 photographers & drone operator"
        }
        res = self.client.post(f"/api/events/{self.test_event_id}/budget", json=item)
        self.assertEqual(res.status_code, 200)
        saved = res.get_json().get("item")
        item_id = saved["id"]
        self.assertEqual(saved["allocated"], 45000)

        # Update spent
        res_up = self.client.put(f"/api/events/{self.test_event_id}/budget/{item_id}", json={
            "spent": 35000
        })
        self.assertEqual(res_up.status_code, 200)
        self.assertEqual(res_up.get_json()["item"]["spent"], 35000)

        # Delete
        res_del = self.client.delete(f"/api/events/{self.test_event_id}/budget/{item_id}")
        self.assertEqual(res_del.status_code, 200)

    # =========================================================================
    # 5. GUESTS, VENDORS, & KEEPSAKE DIARY TESTS
    # =========================================================================
    def test_guests_and_vendors_management(self):
        """Functionality: Manage RSVP guest lists and vendor contracts"""
        # Guest
        g_res = self.client.post(f"/api/events/{self.test_event_id}/guests", json={
            "name": "Dr. Ramesh & Family",
            "attendeesCount": 4,
            "rsvp": "Confirmed",
            "category": "VIP Family"
        })
        self.assertEqual(g_res.status_code, 200)
        guest_id = g_res.get_json()["guest"]["id"]

        # Vendor
        v_res = self.client.post(f"/api/events/{self.test_event_id}/vendors", json={
            "name": "Royal Feast Catering",
            "category": "Food and Catering",
            "quotedPrice": 120000,
            "advancePaid": 50000,
            "status": "Booked"
        })
        self.assertEqual(v_res.status_code, 200)
        vendor_id = v_res.get_json()["vendor"]["id"]

        # Clean up
        self.client.delete(f"/api/events/{self.test_event_id}/guests/{guest_id}")
        self.client.delete(f"/api/events/{self.test_event_id}/vendors/{vendor_id}")

    def test_diary_keepsake_preservation(self):
        """Functionality: Diary memories save with transparent lined stationery patterns"""
        entry_payload = {
            "title": "First Venue Visit Reflections",
            "date": "2026-11-01",
            "mood": "✨ Inspired",
            "content": "Visited Grand Palace Hall today. The mandap pillar architecture is breathtaking!",
            "pattern": "pattern_kitty.png"
        }
        res = self.client.post(f"/api/events/{self.test_event_id}/diary", json=entry_payload)
        self.assertEqual(res.status_code, 200)
        saved = res.get_json().get("entry")
        self.assertEqual(saved["title"], "First Venue Visit Reflections")
        self.assertEqual(saved["pattern"], "pattern_kitty.png")

        # Clean up entry
        self.client.delete(f"/api/events/{self.test_event_id}/diary/{saved['id']}")

    # =========================================================================
    # 6. AI COPILOT INTELLIGENT PLANNING TESTS
    # =========================================================================
    def test_ai_copilot_dual_action_task_and_budget(self):
        """AI Copilot: Adding a task while increasing total budget in single natural prompt"""
        prompt = "Add task to book mandap flowers and add 1 lakh to total budget"
        res = self.client.post(f"/api/events/{self.test_event_id}/ai/copilot", json={
            "message": prompt,
            "current_section": "tasks"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsNotNone(data.get("executed_action"))
        act = data["executed_action"]
        self.assertEqual(act.get("type"), "task_and_budget_added")
        self.assertEqual(act.get("addedAmount"), 100000.0)
        # Verify event budget was updated in memory/db
        updated_ev = data.get("event")
        self.assertEqual(updated_ev["budget"], 550000.0)

    def test_ai_copilot_budget_reduction_math(self):
        """AI Copilot: Accurately subtracts budget when user says reduce/cut/lower"""
        prompt = "Reduce the total budget by 50000"
        res = self.client.post(f"/api/events/{self.test_event_id}/ai/copilot", json={
            "message": prompt,
            "current_section": "budget"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        act = data.get("executed_action")
        self.assertEqual(act.get("type"), "total_budget_updated")
        self.assertTrue(act.get("isReduction"))
        self.assertIn("reduced", data.get("reply", "").lower())
        # Budget 450000 - 50000 = 400000
        self.assertEqual(act.get("newBudget"), 400000.0)

    def test_ai_copilot_cost_estimation_breakdown(self):
        """AI Copilot: Generates structured cost estimation breakdown for guest counts"""
        prompt = "Provide cost estimation for 150 guests wedding"
        res = self.client.post(f"/api/events/{self.test_event_id}/ai/copilot", json={
            "message": prompt,
            "current_section": "budget"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsNotNone(data.get("cost_estimation"))
        est = data["cost_estimation"]
        self.assertIn("items", est)
        self.assertGreater(len(est["items"]), 3)
        self.assertGreater(est["totalEstimated"], 0)

    def test_ai_copilot_web_research_venues(self):
        """AI Copilot: Researches top wedding halls with capacity & estimated rates"""
        prompt = "Best wedding venues and reception halls in Chennai"
        res = self.client.post(f"/api/events/{self.test_event_id}/ai/copilot", json={
            "message": prompt,
            "current_section": "dashboard"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsNotNone(data.get("venues_research"))
        venues = data["venues_research"]
        self.assertGreaterEqual(len(venues), 1)
        self.assertTrue(any("Chennai" in v["location"] for v in venues))

    def test_ai_copilot_natural_event_creation(self):
        """AI Copilot: Creates complete celebration workspace from single conversation prompt"""
        prompt = "Plan a wedding for Maya & Rohit on 2026-12-15 with 300 guests and 6 lakh budget in Chennai"
        res = self.client.post("/api/events/active/ai/copilot", json={
            "message": prompt,
            "current_section": "dashboard"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        created_ev = data.get("event")
        self.assertIsNotNone(created_ev)
        self.assertEqual(created_ev["type"], "Wedding")
        self.assertIn("Maya", created_ev["name"])
        self.assertEqual(created_ev["budget"], 600000.0)
        self.assertEqual(created_ev["guests"], 300)

        # Clean up created event
        self.client.delete(f"/api/events/{created_ev['id']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

