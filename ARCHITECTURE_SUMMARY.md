# Quiz Platform - Quick Architecture Summary

## One-Line Description
Django 5.0 quiz platform with AI-powered question parsing, MathJax formula support, custom admin panel, and dual-mode test interface (one-by-one or batch-25).

---

## Core Components

### 1. Database Layer (7 Models)
```
Subject → Test → Question → Option
                             ↓
         AccessCode → TestSession ← UserAnswer
                          ↓
                        User
```

- **Subject:** Test categories
- **Test:** Test files with settings (time limit, passing score)
- **Question:** Individual questions
- **Option:** Multiple choice options
- **AccessCode:** 8-char codes, one code for many users
- **TestSession:** User test attempts with scoring
- **UserAnswer:** Individual user answers

### 2. Business Logic

#### File Parsing (ai_parser.py + file_parsers.py)
1. Admin uploads PDF/DOCX
2. AI Parser (GPT-4o-mini) or Regex Parser extracts questions
3. Three answer marking patterns supported:
   - `# at start` (DOCX)
   - `++++ at end` (PDF/DOCX)
   - Separate answer file (any format)
4. MathJax formulas preserved and rendered

#### Test Taking (take_test.py view)
1. User enters access code + name
2. Selects test and mode
3. Two modes:
   - **One-by-One:** Single question per page, finish anytime
   - **Batch_25:** 25 questions at once, timer available
4. Auto-scoring on submission
5. Detailed results with answer review

### 3. User Interface Layers

#### Public Site (User Interface)
- `/` - Login with code + name
- `/tests/` - Test selection grid
- `/test/take/` - Dual-mode test interface
- `/test/results/` - Score + detailed answers

**Design:** Gradient backgrounds, responsive grid layout, MathJax rendering

#### Admin Panel (Custom, No Django Admin)
- `/admin/login/` - Admin login
- `/admin/dashboard/` - Stats overview
- `/admin/subjects/` - Subject management
- `/admin/test/<id>/` - Test management + questions preview
- `/admin/codes/` - Code generation
- `/admin/results/` - Results viewing

**Design:** Navigation bar, card-based layout, data tables

---

## Key Features

### For Admins
- One-time registration (only 1 admin)
- Subject organization
- File upload + auto-parsing
- Question management
- Access code generation (batches, subject restriction, attempt limits)
- Results tracking with detailed answers
- Publish/unpublish tests

### For Users
- Simple access code login
- No password required
- Multiple users per code
- Two test modes
- Timer support (optional)
- Detailed result review
- Pass/fail indicators

### Technical
- MathJax 3.x for formula rendering
- OpenAI GPT-4o-mini with regex fallback
- Multi-user session management
- PDF/DOCX support
- SQLite (development), PostgreSQL ready
- Responsive CSS Grid + Flexbox
- Django 5.0 with custom auth

---

## File Organization

### Python Code (1,845 lines)
```
models.py (176)      - 7 database models
views.py (661)       - 32 views (12 admin + 6 user + helpers)
ai_parser.py (424)   - AI + equation extraction
file_parsers.py (252) - Regex fallback
admin.py (289)       - Django admin config
urls.py (34)         - 18 URL patterns
```

### Templates (1,576 lines)
```
User Templates (936 lines)
- base.html          - Layout + MathJax
- login.html         - Code + name form
- test_list.html     - Test grid
- take_test.html     - Dual-mode interface
- test_results.html  - Results display

Admin Templates (640 lines)
- base.html          - Navigation + layout
- dashboard.html     - Stats
- test_create.html   - File upload
- test_detail.html   - Questions preview
- codes.html         - Code management
- results.html       - Results table
```

---

## Architecture Patterns

### MVC Pattern
- **Models:** 7 database models in models.py
- **Views:** 18 view functions in views.py
- **Templates:** 17 HTML templates in templates/

### Separation of Concerns
- **Parsing:** ai_parser.py (AI), file_parsers.py (regex)
- **Auth:** Custom admin + session-based user auth
- **Templates:** Separate admin_custom/ folder

### Fallback Strategy
- AI parsing → Regex parsing → Manual editing

### Multi-Tenancy
- Multiple users per access code
- Per-user sessions with names
- One-time admin setup

---

## Data Flow Examples

### Admin Upload Test Flow
```
1. Admin: Upload PDF → Test Model
2. System: parse_test_file() called
3. AI Parser: Extract questions & answers
4. Database: Create Questions + Options
5. Admin: Review questions in detail page
6. Admin: Click "Publish"
7. Users: See test in test_list
```

### User Take Test Flow
```
1. User: Enter code + name → login_view
2. Session: access_code_id + user_name stored
3. User: Select test → start_test
4. User: Choose mode (one_by_one or batch_25)
5. Session: test_session_id created
6. User: Take test → take_test (dual rendering)
7. User: Submit → Score calculated
8. User: View results → test_results
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | Django 5.0 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Math Rendering | MathJax 3.x |
| PDF Parsing | pdfplumber + PyPDF2 |
| DOCX Parsing | python-docx |
| AI Integration | OpenAI (gpt-4o-mini) |
| Deployment | Django runserver / Production WSGI |

---

## Configuration Checklist

### Development (Current)
- [x] Django DEBUG = True
- [x] SQLite database
- [x] Development SECRET_KEY
- [x] Media files locally stored
- [x] Optional OPENAI_API_KEY

### Production
- [ ] Change SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL
- [ ] Set up S3/external storage
- [ ] Enable HTTPS
- [ ] Configure OPENAI_API_KEY
- [ ] Set up logging

---

## Quick Start Commands

```bash
# Initial setup
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Access
User login: http://127.0.0.1:8000/
Admin login: http://127.0.0.1:8000/admin/login/

# Create admin (first time)
Auto-redirect to register page
```

---

## Key Insights

### Strengths
- AI-powered parsing for accuracy
- Fallback regex system
- Multi-user per code design
- Dual test modes for flexibility
- Clean admin interface (no Django admin)
- Formula support via MathJax
- Responsive design
- Good separation of concerns

### Design Decisions
- Custom admin panel (better UX than Django admin)
- Session-based user auth (no passwords needed)
- AI parsing with regex fallback (robustness)
- MathJax over other rendering (standard, well-supported)
- Dual test modes (flexibility for different use cases)

---

## Important Files to Know

**If you need to...**
- Add features → modify `/home/user/Test_web/quiz/views.py`
- Change database → edit `/home/user/Test_web/quiz/models.py`
- Update styling → edit template `<style>` blocks
- Change parsing → modify `/home/user/Test_web/quiz/ai_parser.py`
- Add routes → edit `/home/user/Test_web/quiz/urls.py`
- Configure Django → edit `/home/user/Test_web/quiz_platform/settings.py`

---

## Documentation Available

1. **CODEBASE_OVERVIEW.md** - Detailed 20-section overview
2. **FILE_LOCATIONS.md** - File paths and structure
3. **FORMULA_GUIDE.md** - LaTeX/MathJax guide
4. **README.md** - User documentation
5. **This file** - Quick reference

