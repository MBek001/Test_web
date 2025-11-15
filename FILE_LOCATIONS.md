# Quiz Platform - Complete File Locations & Structure

## Directory Tree with Key Files

```
/home/user/Test_web/
├── quiz_platform/                          # Main Django project
│   ├── __init__.py
│   ├── settings.py                         # Django configuration
│   ├── urls.py                            # Main URL routing
│   ├── asgi.py
│   ├── wsgi.py
│
├── quiz/                                   # Main application
│   ├── __init__.py
│   ├── apps.py
│   ├── tests.py
│   │
│   ├── models.py                          # Database models (7 models)
│   ├── views.py                           # 32 views (661 lines)
│   ├── urls.py                            # 34 URL patterns
│   ├── admin.py                           # Django admin configuration
│   │
│   ├── ai_parser.py                       # AI question parsing (424 lines)
│   ├── file_parsers.py                    # Regex-based parsing (252 lines)
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py               # Creates all 7 models
│   │   ├── 0002_remove_accesscode_is_used_and_more.py
│   │   └── 0003_testsession_test_mode.py # Adds test_mode field
│   │
│   └── templates/
│       ├── quiz/                          # User-facing templates (6 files)
│       │   ├── base.html                 # Base with MathJax + gradients
│       │   ├── login.html                # User login form
│       │   ├── test_list.html            # Tests grid layout
│       │   ├── select_mode.html          # Mode selection (one_by_one/batch_25)
│       │   ├── take_test.html            # Main test interface (dual mode)
│       │   └── test_results.html         # Results & answer review
│       │
│       └── admin_custom/                  # Admin panel templates (11 files)
│           ├── base.html                 # Admin base + navigation
│           ├── login.html                # Admin login
│           ├── register.html             # Admin registration
│           │
│           ├── dashboard.html            # 4-stat overview
│           ├── subjects.html             # Subjects list
│           ├── subject_create.html       # Create subject form
│           ├── subject_detail.html       # Subject management
│           │
│           ├── test_create.html          # Upload test file form
│           ├── test_detail.html          # Test management & questions preview
│           │
│           ├── codes.html                # Access code generation & management
│           ├── results.html              # Results overview & filter
│           └── session_detail.html       # Detailed user answers
│
├── manage.py                              # Django management
├── requirements.txt                       # Python dependencies (7 packages)
├── setup.sh                               # Initial setup script
├── .env.example                          # Environment variables template
├── README.md                             # User documentation
├── FORMULA_GUIDE.md                      # Formula support guide
└── .gitignore

```

---

## Key File Locations (Absolute Paths)

### Core Application Files
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/Test_web/quiz/models.py` | 176 | Database models (Subject, Test, Question, Option, AccessCode, TestSession, UserAnswer) |
| `/home/user/Test_web/quiz/views.py` | 661 | 32 view functions (12 admin + 6 user + helpers) |
| `/home/user/Test_web/quiz/urls.py` | 34 | URL routing (6 user + 12 admin routes) |
| `/home/user/Test_web/quiz/admin.py` | 289 | Django admin configuration (7 model admins) |

### Parsing & Integration
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/Test_web/quiz/ai_parser.py` | 424 | OpenAI GPT-4o-mini parsing + equation extraction |
| `/home/user/Test_web/quiz/file_parsers.py` | 252 | Regex fallback parsing for PDF/DOCX |

### Configuration
| File | Purpose |
|------|---------|
| `/home/user/Test_web/quiz_platform/settings.py` | Django settings (SQLite, apps, middleware) |
| `/home/user/Test_web/quiz_platform/urls.py` | Main project URL router |
| `/home/user/Test_web/requirements.txt` | Dependencies: Django, OpenAI, pdfplumber, python-docx, etc. |
| `/home/user/Test_web/.env.example` | OPENAI_API_KEY template |

### Templates - User Interface
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/Test_web/quiz/templates/quiz/base.html` | 175 | MathJax setup, gradient design, base layout |
| `/home/user/Test_web/quiz/templates/quiz/login.html` | 75 | Access code + name login form |
| `/home/user/Test_web/quiz/templates/quiz/test_list.html` | 142 | Responsive test grid (auto-fill minmax 350px) |
| `/home/user/Test_web/quiz/templates/quiz/select_mode.html` | ~40 | Mode selection (one_by_one/batch_25) |
| `/home/user/Test_web/quiz/templates/quiz/take_test.html` | 297 | Dual-mode test interface with timer |
| `/home/user/Test_web/quiz/templates/quiz/test_results.html` | 207 | Results page with answer review |

### Templates - Admin Panel
| File | Purpose |
|------|---------|
| `/home/user/Test_web/quiz/templates/admin_custom/base.html` | Navigation bar + layout |
| `/home/user/Test_web/quiz/templates/admin_custom/login.html` | Admin login (no Django admin) |
| `/home/user/Test_web/quiz/templates/admin_custom/register.html` | One-time admin registration |
| `/home/user/Test_web/quiz/templates/admin_custom/dashboard.html` | 4 stat cards + quick actions |
| `/home/user/Test_web/quiz/templates/admin_custom/subjects.html` | Subject listing |
| `/home/user/Test_web/quiz/templates/admin_custom/subject_create.html` | Subject creation form |
| `/home/user/Test_web/quiz/templates/admin_custom/subject_detail.html` | Subject editing + tests |
| `/home/user/Test_web/quiz/templates/admin_custom/test_create.html` | File upload form + parsing options |
| `/home/user/Test_web/quiz/templates/admin_custom/test_detail.html` | Test management + questions preview |
| `/home/user/Test_web/quiz/templates/admin_custom/codes.html` | Code generation + management |
| `/home/user/Test_web/quiz/templates/admin_custom/results.html` | Results table + filtering |
| `/home/user/Test_web/quiz/templates/admin_custom/session_detail.html` | Detailed user answers |

### Documentation
| File | Purpose |
|------|---------|
| `/home/user/Test_web/README.md` | User guide, installation, workflows |
| `/home/user/Test_web/FORMULA_GUIDE.md` | LaTeX/MathJax formula support guide |

### Database Migrations
| File | Purpose |
|------|---------|
| `/home/user/Test_web/quiz/migrations/0001_initial.py` | Creates all 7 database models |
| `/home/user/Test_web/quiz/migrations/0002_remove_accesscode_is_used_and_more.py` | Schema updates |
| `/home/user/Test_web/quiz/migrations/0003_testsession_test_mode.py` | Adds test_mode field |

---

## Template Line Counts Summary

### User Templates
- base.html: 175 lines (MathJax, gradients, responsive)
- login.html: 75 lines
- test_list.html: 142 lines (responsive grid)
- select_mode.html: ~40 lines
- take_test.html: 297 lines (timer, dual modes, MathJax)
- test_results.html: 207 lines (results display)

**Total User Templates:** ~936 lines

### Admin Templates
- base.html: 71 lines (navigation, styling)
- login.html: 44 lines
- register.html: ~45 lines
- dashboard.html: 62 lines
- subjects.html: ~50 lines
- subject_create.html: ~25 lines
- subject_detail.html: ~60 lines
- test_create.html: 65 lines (dynamic form)
- test_detail.html: 89 lines
- codes.html: 81 lines
- results.html: 68 lines
- session_detail.html: ~40 lines

**Total Admin Templates:** ~640 lines

---

## Code Statistics

### Python Files
- models.py: 176 lines
- views.py: 661 lines
- urls.py: 34 lines
- admin.py: 289 lines
- ai_parser.py: 424 lines
- file_parsers.py: 252 lines
- Other files: 9 lines

**Total Python:** 1,845 lines

### Templates (HTML)
- User templates: ~936 lines
- Admin templates: ~640 lines

**Total Templates:** ~1,576 lines

**Grand Total:** ~3,421 lines of code

---

## Database Schema (7 Models)

### Relationships Diagram
```
Subject (1)
    ├── (1→N) Test
    │           ├── (1→N) Question
    │           │           ├── (1→N) Option
    │           │           │           └── (N→1) TestSession
    │           │           └── (N→1) TestSession
    │           │
    │           └── (1→N) TestSession
    │
    └── (1→N) AccessCode

AccessCode (1)
    └── (1→N) TestSession

TestSession (1)
    ├── (1→N) UserAnswer
    └── (N→1) User (Django)

UserAnswer (N)
    ├── (N→1) Question
    ├── (N→1) Option
    └── (N→1) TestSession

User (Django built-in)
    ├── (1→N) AccessCode (created_by)
    └── (1→N) TestSession (via access code)
```

---

## API Integration Points

### OpenAI Integration
- **File:** `/home/user/Test_web/quiz/ai_parser.py`
- **Model:** gpt-4o-mini
- **Temperature:** 0.1 (low for consistency)
- **Response Format:** JSON
- **Method:** `_parse_with_openai()`
- **Fallback:** Regex parsing if API fails

### File Parsing Libraries
- **pdfplumber:** Advanced PDF text extraction
- **PyPDF2:** Fallback PDF extraction
- **python-docx:** Word document parsing with equation support

### Mathematical Rendering
- **Library:** MathJax 3.x
- **CDN:** cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
- **Inline Delimiters:** $...$, \\(...\\)
- **Display Delimiters:** $$...$$, \\[...\\]

---

## Configuration & Environment

### Environment Variables
- **OPENAI_API_KEY:** Required for AI parsing (optional, falls back to regex)

### Django Settings
- **DEBUG:** True (change for production)
- **DATABASE:** SQLite (change for production)
- **SECRET_KEY:** Default insecure (change for production)
- **ALLOWED_HOSTS:** Empty (configure for production)

### Media Files
- **Upload Directory:** `/home/user/Test_web/media/test_files/`
- **Supported Formats:** .pdf, .docx, .doc

---

## Quick Access Guide

### To Edit Core Logic
- Parse files: `/home/user/Test_web/quiz/ai_parser.py`
- Manage views: `/home/user/Test_web/quiz/views.py`
- Database: `/home/user/Test_web/quiz/models.py`

### To Edit User Interface
- User layout: `/home/user/Test_web/quiz/templates/quiz/base.html`
- Test interface: `/home/user/Test_web/quiz/templates/quiz/take_test.html`
- Admin base: `/home/user/Test_web/quiz/templates/admin_custom/base.html`

### To Edit Routing
- Main routes: `/home/user/Test_web/quiz/urls.py`

### To Edit Styling
- Inline CSS in each template file (base.html, take_test.html, etc.)

### To Configure
- Django: `/home/user/Test_web/quiz_platform/settings.py`
- Environment: Create `.env` from `.env.example`

