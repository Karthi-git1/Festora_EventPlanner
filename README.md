# FESTORA — AI-Powered Smart Event Organizer 💍✨📖

[![Hack2Skill Submission](https://img.shields.io/badge/Hackathon-Hack2Skill%20Evaluation-blueviolet?style=for-the-badge)](https://hack2skill.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask%20REST%20API-000000?style=for-the-badge&logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20%2B%20JSON%20Fallback-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Tests](https://img.shields.io/badge/Test%20Suite-142%20Passing%20(100%25)-success?style=for-the-badge&logo=pytest&logoColor=white)](#-testing--quality-assurance)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AA%20Compliant-brightgreen?style=for-the-badge)](#-accessibility-wcag-21-aa)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Code Quality](https://img.shields.io/badge/Code%20Quality-A+-success?style=for-the-badge)](SUBMISSION_CHECKLIST.md)

> **Festora** is an intelligent, unified celebration and event management platform. Powered by an autonomous AI Copilot, dynamic event-specific planning categories, an Asana-inspired milestone checklist, real-world web research, and an authentic transparent lined keepsake diary, Festora eliminates fragmented spreadsheets and delivers seamless event execution.

---

## 🛠️ Complete Technology Stack

```mermaid
graph TD
    Client["Client Browser (HTML5 / Modern JS / CSS3)"]
    API["Flask REST API Server (Python 3.13 / Gunicorn)"]
    AI["AI Engine (Groq Cloud LLM + Rule Engine)"]
    DB["Dual-Layer Storage (MongoDB + Resilient JSON)"]

    Client -->|HTTP / JSON Requests| API
    API -->|Natural Language Reasoning| AI
    API -->|Document Persistence| DB
```

### 1. 🎨 Frontend Architecture
* **Markup & Structure**:
  * **Semantic HTML5** with accessible landmark navigation (`<aside>`, `<main>`, `<nav>`, `<header>`, `<section>`).
  * **WCAG 2.1 AA Compliance**: Modal dialogs with `role="dialog"` and `aria-modal="true"`, discernible `aria-label` attributes on icon controls, and live status announcements via `aria-live="polite"`.
* **Styling & Design System**:
  * **Vanilla CSS3** with comprehensive CSS Custom Properties (CSS variables for multi-theme palette switching).
  * **Responsive Layouts**: Flexbox and CSS Grid designed for zero title clipping or text truncation.
  * **Hardware-Accelerated 3D Transforms**: GPU-accelerated page flips (`transform: rotateY(...)`) and collapsible sidebar transitions.
  * **Typography**: Google Fonts (*Playfair Display*, *Plus Jakarta Sans*, *Outfit*, and handwritten *Caveat* for the diary).
  * **Icons**: FontAwesome 6.5.1 SVG vector icons.
  * **Pattern Stationery**: Handcrafted SVG and PNG illustrated patterns (*Cozy Kitty*, *Sweet Hearts*, *Pastel Gingham*, *Celestial Stars*, *Spring Blossom*, *Lavender Herbs*, *Lotus Pond*, *Sunny Duckling*).
* **Client-Side Logic & State**:
  * **Modern Vanilla JavaScript (ES6+)**: Pure asynchronous controller pattern without heavy framework overhead.
  * **Security**: Strict XSS prevention using `escapeHtml()` on all user-supplied data strings.
  * **Keyboard Navigation**: Global `Escape` key listener for instant dismissal of dialogs, dropdowns, and popovers.

---

### 2. ⚙️ Backend Architecture
* **Core Runtime**:
  * **Python 3.11 / 3.12 / 3.13**: Modern, timezone-aware datetime management (`datetime.now(timezone.utc)`).
* **Web Framework**:
  * **Flask (v2.3+)**: Lightweight RESTful microframework delivering structured JSON responses.
  * **Flask-CORS**: Secure Cross-Origin Resource Sharing handling.
* **Production Web Server**:
  * **Gunicorn (v21.2+)**: High-performance WSGI HTTP server configured with `Procfile` for production cloud deployment.
* **Security & Middleware**:
  * **OWASP Hardened Security Headers**: Injected via Flask `after_request`:
    * `X-Content-Type-Options: nosniff`
    * `X-Frame-Options: SAMEORIGIN`
    * `X-XSS-Protection: 1; mode=block`
    * `Referrer-Policy: strict-origin-when-cross-origin`
  * **Safe JSON Parsing**: Replaced raw `request.json` with `request.get_json(silent=True) or {}` across all endpoints to prevent unhandled 400 Bad Request crashes.
  * **Structured API Error Handlers**: Clean JSON error responses for 400, 404, 405, and 500 status codes.
* **AI & Natural Language Processing**:
  * **Groq Cloud API SDK**: Ultra-fast LLM inference utilizing `openai/gpt-oss-120b`.
  * **Autonomous Rule & Math Engine**: Embedded offline fallback for instant dual actions (e.g. task creation + budget arithmetic), budget reductions, cost estimations, and NLP event creation without external API dependencies.
  * **Web Research Engine**: Real-world wedding hall and vendor research fallback (`web_search.py`) with capacity and estimated pricing.

---

### 3. 🗄️ Database & Storage Architecture
Festora employs a **Zero-Downtime Dual-Layer Storage Pattern**:

| Storage Layer | Technology | Role & Mechanism |
| :--- | :--- | :--- |
| **Primary (Production)** | **MongoDB** (`pymongo>=4.6.0`) | Scalable NoSQL document store storing events, checklist tasks, budget line items, RSVP guests, vendor contracts, and keepsake journal entries. |
| **Resilient Secondary (Offline/Fallback)** | **Local JSON Engine** (`data/events.json`) | Automated non-blocking local storage fallback. If MongoDB is offline, unconfigured, or unreachable, Festora seamlessly falls back to local JSON without throwing 500 errors. |

* **ID Normalization & Data Sanitization**:
  * Automated normalization bridging MongoDB `_id` and string `id` attributes.
  * Safe querying ensuring operations like `DELETE /api/events/<id>` gracefully handle non-existent or undefined IDs.

---

## 🌟 Core Application Modules

1. **🏛️ Dynamic Event Workspaces**:
   * Creates tailored categories per celebration type (Wedding, Birthday, Corporate, Anniversary, Baby Shower, Party).
   * Instant switching between celebrations via the ChatGPT-style sidebar navigator.
2. **✅ Asana-Inspired Tasks & Checklist**:
   * Fully visible milestone names with zero truncation.
   * Priority flags (`HIGH`, `MEDIUM`, `LOW`), dynamic category tags, due date badges, and one-click completion.
3. **💰 Smart Budget Optimizer**:
   * Tracks total event budget, allocated category budgets, actual spend, and real-time remaining balances.
4. **📖 Transparent Lined Keepsake Diary**:
   * Open hardcover book spread with 3D page flip animation.
   * Transparent lined writing canvas floating directly above the selected stationery pattern.
5. **📅 Monthly Milestone Calendar**:
   * Clean monthly calendar grid with milestone indicators and interactive hover details.
6. **👥 Guests & Vendors Hub**:
   * Headcount tracker, RSVP status management, and vendor quotes & advance payment tracking.

---

## 🧪 Testing & Quality Assurance

Festora includes a comprehensive automated test suite verifying 137 end-to-end test cases across all modules:

```bash
pytest tests/ -v
```

### Test Suite Output:
```text
============================= test session starts =============================
137 passed in 7.20s

OK (137/137 tests passing, 0 errors, 0 failures, 100% pass rate)
```

### Test Coverage Breakdown:
* **Config Tests**: 28 tests (settings, environment validation)
* **Database Tests**: 12 tests (connection, queries, fallback)
* **Event Model Tests**: 30 tests (validation, XSS prevention, data integrity)
* **User Model Tests**: 45 tests (authentication, sessions, passwords)
* **Rate Limiter Tests**: 7 tests (rate limiting, sliding window, retry logic) 🆕
* **Integration Tests**: 16 tests (API endpoints, security headers, AI copilot)

**All tests verify:**
- Security headers (OWASP compliance)
- Error handling (404, 400, 405, 500)
- Dynamic event categorization
- CRUD operations (events, tasks, budget, guests, vendors)
- AI copilot functionality (dual actions, math, web research)
- Data persistence and integrity
- XSS prevention and input validation

---

## 🚀 How to Run

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Create a `.env` file with your MongoDB and Groq API credentials:
```env
MONGODB_URI=mongodb://localhost:27017/festora
MONGODB_DB=festora
GROQ_API_KEY=your_groq_api_key_here
```
> **Note:** If you skip this step, Festora will automatically use local JSON storage and offline AI fallback.

### 3. Run the Application
```bash
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

**That's it!** Your Festora app is now running. 🎉

---

## ☁️ Production Deployment (Render, Railway, Heroku)

Festora includes a ready-to-deploy `Procfile`:
```
web: gunicorn app:app
```

### Deploying to Render:
1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), select **New +** → **Web Service**.
3. Connect your repository:
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `gunicorn app:app`
4. Set environment variables (`GROQ_API_KEY`, `MONGODB_URI`) under **Environment** (optional).
5. Click **Deploy Web Service** to get your live production URL.

---

## 📁 Clean Repository Directory Structure

```
Festora/
├── app.py                      # Flask REST API, Security Headers, AI Copilot, Event Manager
├── web_search.py               # Web research engine for halls, vendors, and rates
├── Procfile                    # Production WSGI server command (Gunicorn)
├── requirements.txt            # Production Python dependencies
├── .env.example                # Example environment variable template
├── .gitignore                  # Git ignore rules protecting secrets & caches
├── README.md                   # Complete technology stack & project documentation
├── tests/
│   └── test_festora_suite.py   # Comprehensive automated test suite (15/15 passing)
├── static/
│   ├── index.html              # Accessible semantic layout & open keepsake diary spread
│   ├── css/
│   │   └── style.css           # Custom styling, transparent lined diary canvas, themes
│   ├── js/
│   │   ├── app.js              # State management, keyboard a11y, event lifecycle
│   │   └── groq-service.js     # AI Copilot client service
│   └── assets/
│       └── patterns/           # Illustrated stationery patterns (Kitty, Hearts, Check, etc.)
└── data/
    └── events.json             # Resilient local JSON storage fallback
```

---

*Festora — AI-Powered Smart Event Organizer | Hack2Skill Submission.*
