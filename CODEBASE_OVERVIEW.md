# Quiz Platform - Comprehensive Codebase Overview

## Project Summary
Django-based online quiz/testing platform with custom admin panel, AI-powered question parsing, formula support (MathJax), and multi-user test session management. Built with Django 5.0, supports PDF/DOCX file uploads with automatic parsing.

**Total Code Lines:** 1,845 lines (Python)
**Key Technologies:** Django 5.0, OpenAI API, pdfplumber, python-docx, PyPDF2, MathJax 3.x

---

## 1. PROJECT STRUCTURE

```
/home/user/Test_web/
├── quiz_platform/          # Main Django project configuration
│   ├── settings.py        # Django settings (SQLite, Apps, Middleware)
│   ├── urls.py            # Main URL router
│   ├── asgi.py           # ASGI configuration
│   ├── wsgi.py           # WSGI configuration
│   └── __init__.py
├── quiz/                   # Main Django app
│   ├── models.py          # 7 database models (176 lines)
│   ├── views.py           # 32 views for admin + user (661 lines)
│   ├── urls.py            # 34 URL patterns
│   ├── admin.py           # Django admin registration (289 lines)
│   ├── ai_parser.py       # AI-powered parsing (424 lines)
│   ├── file_parsers.py    # Fallback regex parsing (252 lines)
│   ├── apps.py           # App configuration
│   ├── migrations/        # Database migrations (3 migrations)
│   └── templates/         # HTML templates
│       ├── quiz/         # User-facing templates (5 files)
│       └── admin_custom/ # Admin panel templates (10 files)
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── setup.sh             # Initial setup script
├── README.md            # User documentation
├── FORMULA_GUIDE.md     # Formula support documentation
└── .env.example         # Environment variables template
```

---

## 2. DATABASE MODELS (models.py - 176 lines)

### Core Models:

**Subject** (Test Categories)
- name: CharField(max_length=200)
- description: TextField
- created_at: DateTimeField(auto_now_add=True)
- Meta: ordering by name

**Test** (Individual Tests)
- subject: ForeignKey(Subject)
- title, description: CharField/TextField
- question_file: FileField(upload_to='test_files/')
- answer_file: FileField (optional, for separate answer files)
- answer_marking: CharField (hash_start, plus_end, separate_file)
- is_published, is_parsed: BooleanField
- time_limit: IntegerField (minutes, 0 = unlimited)
- passing_score: IntegerField (percentage)
- created_at, updated_at: DateTimeField
- Relations: has many Questions

**Question** (Individual Questions)
- test: ForeignKey(Test)
- text: TextField
- order: IntegerField
- created_at: DateTimeField
- Relations: has many Options

**Option** (Multiple Choice Options)
- question: ForeignKey(Question)
- text: TextField
- is_correct: BooleanField
- order: IntegerField

**AccessCode** (One Code for Many Users)
- code: CharField(unique=True, auto-generated 8-char)
- subject: ForeignKey(Subject, optional)
- max_attempts_per_user: IntegerField (0 = unlimited)
- expires_at: DateTimeField (optional)
- is_active: BooleanField
- first_used_at: DateTimeField
- created_by: ForeignKey(User)
- Methods: is_valid(), get_users()

**TestSession** (User Test Attempts)
- access_code: ForeignKey(AccessCode)
- test: ForeignKey(Test)
- user_name: CharField (supports multiple users per code)
- test_mode: CharField ('one_by_one' or 'batch_25')
- started_at, completed_at: DateTimeField
- is_completed: BooleanField
- score, correct_answers, total_questions: FloatField/IntegerField
- Method: calculate_score()

**UserAnswer** (Individual User Answers)
- session: ForeignKey(TestSession)
- question: ForeignKey(Question)
- selected_option: ForeignKey(Option, optional)
- is_correct: BooleanField
- answered_at: DateTimeField

---

## 3. KEY VIEWS (views.py - 661 lines)

### Admin Views:
1. **admin_register** - One-time admin registration (only allows 1 admin)
2. **admin_login** - Admin authentication
3. **admin_logout** - Logout
4. **admin_dashboard** - Statistics and overview
5. **admin_subjects** - List all subjects
6. **admin_subject_create** - Create new subject
7. **admin_subject_detail** - View/edit subject details
8. **admin_test_create** - Upload and create test file
9. **admin_test_detail** - View/manage test, publish, reparse
10. **admin_codes** - Generate and manage access codes
11. **admin_results** - View all test sessions
12. **admin_session_detail** - View detailed user answers

### User Views:
1. **login_view** - User login with access code (supports multiple users per code)
2. **test_list** - List available tests for user
3. **start_test** - Select test mode (one_by_one or batch_25)
4. **take_test** - Main test interface (dual mode support)
5. **test_results** - View results and detailed answers
6. **logout_view** - User logout

### Helper Functions:
- **is_staff(user)** - Check if user is admin
- **parse_test_file(test)** - AI-powered file parsing

---

## 4. AI PARSER (ai_parser.py - 424 lines)

**AIQuestionParser Class:**

**File Extraction:**
- extract_text_from_file(file_path) - Routes to PDF/DOCX handlers
- _extract_from_pdf(file_path) - Uses pdfplumber + fallback PyPDF2
- _extract_from_docx(file_path) - Extracts with equation support

**Equation Handling:**
- _extract_equation_from_run(run) - Extracts math from Word runs
- _extract_equations_from_paragraph(paragraph) - Paragraph-level equation extraction
- Marks complex equations as [FORMULA]
- Preserves LaTeX notation

**Main Parsing:**
- parse_with_ai(file_path, answer_marking, answer_file_path)
  - Uses OpenAI GPT-4o-mini if API key available
  - Fallback to regex parsing if API fails
  - Model: gpt-4o-mini, temperature: 0.1

**Regex Fallback Methods:**
- _parse_hash_format(text) - # marker for correct answers
- _parse_plus_format(text) - ++++ marker for correct answers
- _parse_questions_only(text) - Questions only (for separate answer file)
- _parse_answers(answer_text) - Parse answer file
- _merge_answers(questions, answers) - Combine question + answer data

**Output Format (JSON):**
```json
{
  "questions": [
    {
      "order": 1,
      "text": "Question with [FORMULA] if present",
      "options": [
        {"text": "Option A", "is_correct": false, "order": 0},
        {"text": "Option B", "is_correct": true, "order": 1}
      ]
    }
  ]
}
```

---

## 5. FILE PARSERS (file_parsers.py - 252 lines)

**QuestionParser Class (Legacy/Fallback):**
- parse_docx(file_path, answer_marking)
- parse_pdf(file_path, answer_marking)
- parse_answers_file(file_path, file_extension)
- merge_questions_with_answers(questions, answers)

Handles three answer marking formats:
1. # at start
2. ++++ at end
3. Separate answer file (1.B, 2.C format)

---

## 6. ADMIN CONFIGURATION (admin.py - 289 lines)

**Registered Models:**
1. SubjectAdmin
   - list_display: name, description, test_count, created_at
   - search_fields: name, description

2. TestAdmin
   - list_display: title, subject, is_parsed, is_published, question_count
   - list_filter: subject, is_published, is_parsed, answer_marking
   - Actions: parse_files, publish_tests, unpublish_tests
   - Fieldsets: Basic Info, Files, Settings, Status

3. QuestionAdmin
   - list_display: short_text, test, order, option_count
   - search_fields: text

4. OptionAdmin
   - list_display: short_text, question, is_correct, order

5. AccessCodeAdmin
   - list_display: code, user_count, subject, is_active, usage_count
   - Actions: generate_codes, deactivate_codes

6. TestSessionAdmin (read-only)
   - list_display: user_name, access_code, test, score, correct_answers
   - No add permission

7. UserAnswerAdmin (read-only)
   - list_display: get_user_name, question_text, selected_option, is_correct
   - No add permission

---

## 7. URL ROUTING (urls.py - 34 lines)

### User URLs:
- `/` → login_view
- `/tests/` → test_list
- `/test/<int:test_id>/start/` → start_test
- `/test/take/` → take_test
- `/test/results/<int:session_id>/` → test_results
- `/logout/` → logout_view

### Admin URLs:
- `/admin/` → admin_dashboard
- `/admin/register/` → admin_register
- `/admin/login/` → admin_login
- `/admin/logout/` → admin_logout
- `/admin/subjects/` → admin_subjects
- `/admin/subjects/create/` → admin_subject_create
- `/admin/subjects/<int:subject_id>/` → admin_subject_detail
- `/admin/subjects/<int:subject_id>/test/create/` → admin_test_create
- `/admin/test/<int:test_id>/` → admin_test_detail
- `/admin/codes/` → admin_codes
- `/admin/results/` → admin_results
- `/admin/session/<int:session_id>/` → admin_session_detail

---

## 8. TEMPLATES STRUCTURE (21 HTML files)

### User Templates (quiz/):
1. **base.html** - Base template with MathJax CDN
   - Includes MathJax 3.x for formula rendering
   - Responsive design with gradient background
   - Message display system
   - Mobile-aware viewport

2. **login.html** - User login form
   - Access code and name input
   - Responsive form layout

3. **test_list.html** - Available tests for user
   - Grid layout (responsive, auto-fill minmax(350px, 1fr))
   - Tests grouped by subject
   - Attempt counter
   - Subject descriptions

4. **select_mode.html** - Test mode selection
   - One-by-one: Single question per page
   - Batch_25: All 25 questions at once

5. **take_test.html** - Main test interface
   - Dual mode rendering (one_by_one vs batch_25)
   - Timer with danger/warning states
   - Progress indicators
   - MathJax formula rendering
   - Radio button options with hover effects

6. **test_results.html** - Results and detailed review
   - Pass/fail gradient headers
   - Score display (large 72px)
   - Statistics cards
   - Question-by-question review
   - Shows correct answers for wrong responses

### Admin Templates (admin_custom/):
1. **base.html** - Admin base template
   - Navigation bar with gradient background
   - Stats grid (4-column responsive)
   - Card-based layout
   - Table styling with hover effects

2. **login.html** - Admin login page
   - Centered login box
   - Gradient background
   - Minimal design

3. **register.html** - One-time admin registration
   - Only available if no admin exists
   - Password confirmation
   - Validation messages

4. **dashboard.html** - Admin overview
   - 4 stat cards: Subjects, Tests, Codes, Sessions
   - Quick action buttons
   - Recent sessions table

5. **subjects.html** - Subjects list
   - Table with test counts
   - Create/edit actions

6. **subject_create.html** - Create subject form
   - Name and description fields

7. **subject_detail.html** - Subject management
   - Edit subject info
   - Tests list for subject
   - Delete option

8. **test_create.html** - Upload test file
   - File upload (PDF/DOCX)
   - Answer marking pattern selection
   - Time limit and passing score inputs
   - Dynamic answer file field (shown only for "separate_file" option)

9. **test_detail.html** - Test management
   - Settings editor
   - Publish/unpublish buttons
   - Questions preview (with visual markers for correct)
   - Reparse button
   - Delete danger zone

10. **codes.html** - Access codes management
    - Code generation form (count, subject, max attempts)
    - All codes table
    - User count and session count

11. **results.html** - Results overview
    - Subject filter
    - Sessions table with scores
    - Pass/fail badges
    - View details links

12. **session_detail.html** - Individual session review
    - User info and test details
    - Question-by-question breakdown
    - Selected vs correct answers

---

## 9. FORMULA SUPPORT IMPLEMENTATION

### MathJax Integration:
- **Version:** 3.x (CDN: cdn.jsdelivr.net/npm/mathjax@3)
- **Configuration in base.html:**
  ```javascript
  MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']]
    }
  }
  ```

### LaTeX Support:
- **Inline:** `$formula$` or `\\(formula\\)`
- **Display:** `$$formula$$` or `\\[formula\\]`
- **Examples:**
  - Matrices: `$$\\begin{bmatrix} 2 & 4 \\\\ -1 & 3 \\end{bmatrix}$$`
  - Fractions: `$\\frac{a}{b}$`
  - Equations: `$ax^2 + bx + c = 0$`

### Extraction from Files:
- DOCX: Parses Word equation editor content
- PDF: Limited extraction, marks complex formulas as [FORMULA]
- AI Parser: Converts mathematical notation to LaTeX format

---

## 10. MOBILE RESPONSIVENESS IMPLEMENTATION

### Base Styling:
```css
/* Responsive container */
.container { max-width: 1200px; margin: 0 auto; }

/* Mobile-first approach */
* { box-sizing: border-box; }
body { padding: 20px; }

/* Responsive grids */
.test-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

/* Flexbox layouts */
.test-info { display: flex; gap: 30px; flex-wrap: wrap; }
.button-group { display: flex; gap: 15px; justify-content: center; }
```

### Viewport Configuration:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Responsive Features:
1. **Test Grid:** Auto-fills with 350px minimum width items
2. **Form Layout:** Grid with responsive columns (1fr, 1fr or 1fr 2fr 1fr)
3. **Timer Widget:** Fixed positioning adjusts for mobile
4. **Buttons:** Full-width on mobile, flex group on desktop
5. **Tables:** Full width, scrollable on small screens
6. **Header:** Flexbox space-between, wraps on mobile

### Breakpoints (CSS):
- No explicit media queries (uses auto-fit/minmax for natural responsiveness)
- Fixed positioning (timer) works across all viewports
- Padding: 20-30px adaptable

---

## 11. AUTHENTICATION & SECURITY

### Admin Authentication:
- **One-time registration:** Only 1 admin account allowed
- **Custom login page:** No Django admin site
- **Session-based:** Django sessions middleware
- **Decorators:** @login_required, @user_passes_test(is_staff)

### User Authentication:
- **Access Code based:** 8-character unique codes
- **Session storage:** access_code_id, user_name in session
- **No password:** Simple access code + name
- **Multi-user support:** Many users can use same code

### Settings (settings.py):
- DEBUG = True (⚠️ change for production)
- SECRET_KEY = insecure (⚠️ change for production)
- ALLOWED_HOSTS = [] (empty, set for production)
- Database: SQLite (suitable for development/testing)
- LOGIN_URL = '/admin/login/'

---

## 12. FILE UPLOAD & PROCESSING

### Supported Formats:
- PDF files (.pdf)
- Word documents (.docx, .doc)
- Upload location: media/test_files/

### Upload Flow:
1. Admin uploads file via test_create form
2. File saved to FileField (test.question_file)
3. parse_test_file(test) called automatically
4. AI parser extracts questions or regex fallback used
5. Questions and options created in database
6. is_parsed flag set to True

### Answer Marking Patterns:
1. **hash_start:** `# Correct answer`
   - Separator: `====`
   - Question separator: `++++`

2. **plus_end:** `Correct answer ++++`
   - Question format: `1. Question text?`
   - Option format: `A) Option text`

3. **separate_file:** Answers in separate file
   - Format: `1. B`, `2. C`, etc.
   - Merged with questions by question number

---

## 13. ADMIN PANEL FEATURES

### Dashboard:
- Statistics cards (4-grid layout)
- Quick actions
- Recent sessions table

### Subject Management:
- Create, view, edit, delete subjects
- Associate tests with subjects
- Bulk test management per subject

### Test Management:
- Upload test files (PDF/DOCX)
- Choose answer marking pattern
- Set time limit and passing score
- Publish/unpublish tests
- Reparse files
- View all questions with correct answer indicators

### Access Code Management:
- Generate codes in batches (1-100)
- Restrict to specific subject
- Set max attempts per user
- Track usage and users
- Status (active/inactive)

### Results Tracking:
- View all completed test sessions
- Filter by subject
- See scores with pass/fail badges
- View detailed user answers
- Compare selected vs correct answers

---

## 14. TEST SESSION MODES

### Mode 1: One-by-One (birma-bir)
- Single question per page
- User can finish test anytime
- Progress shows current/total
- Next/Finish buttons
- No timer on individual questions

### Mode 2: Batch_25 (25 questions at once)
- All 25 questions on one page
- Timer counting down (if time_limit > 0)
- Auto-submit when timer reaches 0
- Save progress button
- Submit test button

### Scoring:
- Calculated after submission: (correct_answers / total_questions) * 100
- Rounds to 2 decimal places
- Pass/fail determined by passing_score

---

## 15. KEY DEPENDENCIES (requirements.txt)

```
Django==5.0                 # Web framework
python-docx==1.1.0         # Word document parsing
PyPDF2==3.0.1              # PDF parsing (fallback)
pdfplumber==0.11.0         # Advanced PDF extraction
Pillow==10.1.0             # Image processing
openai==1.3.0              # OpenAI API client (gpt-4o-mini)
python-dotenv==1.0.0       # Environment variables (.env support)
```

---

## 16. CONFIGURATION FILES

### .env.example:
```
OPENAI_API_KEY=your-openai-api-key-here
```

### settings.py:
- DEBUG = True (for development)
- DATABASES: SQLite at db.sqlite3
- INSTALLED_APPS: Django built-ins + quiz
- MEDIA_ROOT: BASE_DIR / "media"
- MEDIA_URL: "/media/"
- LANGUAGE_CODE: "en-us"

### Database Setup (migrations):
1. 0001_initial.py - Creates all 7 models
2. 0002_remove_accesscode_is_used_and_more.py - Schema adjustments
3. 0003_testsession_test_mode.py - Adds test_mode field

---

## 17. WORKFLOW EXAMPLES

### Admin Workflow:
1. Admin registers (one-time) → /admin/register/
2. Admin logs in → /admin/login/
3. Creates subject → /admin/subjects/create/
4. Uploads test file → /admin/subjects/{id}/test/create/
5. System parses automatically
6. Admin verifies questions
7. Admin publishes test
8. Generates access codes → /admin/codes/
9. Shares codes with users
10. Views results → /admin/results/

### User Workflow:
1. User opens platform → /
2. Enters access code + name → login_view
3. Selects test → test_list
4. Chooses mode → start_test
5. Takes test → take_test (one_by_one or batch_25)
6. Submits → automatic scoring
7. Views results → test_results

---

## 18. KEY ARCHITECTURAL PATTERNS

### MVC Pattern:
- **Models:** 7 database models (models.py)
- **Views:** 32 view functions (views.py)
- **Templates:** 21 HTML templates

### Separation of Concerns:
- **Parsing Logic:** Separate ai_parser.py + file_parsers.py
- **Admin Views:** Separate from user views
- **Admin Templates:** Separate folder from user templates

### Fallback Mechanism:
- AI parsing (if OpenAI API available)
- → Regex parsing (if AI fails)
- → User can manually edit/reparse

### Multi-tenancy:
- Multiple users per access code
- One-time admin setup
- Per-user sessions with names

---

## 19. TECH STACK SUMMARY

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.0 |
| Database | SQLite3 (dev), recommend PostgreSQL (prod) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Math Rendering | MathJax 3.x |
| PDF Parsing | pdfplumber + PyPDF2 |
| DOCX Parsing | python-docx |
| AI Integration | OpenAI (gpt-4o-mini) |
| Authentication | Django auth + custom sessions |
| File Upload | Django FileField |

---

## 20. DEPLOYMENT NOTES

### For Production:
1. Change SECRET_KEY in settings.py
2. Set DEBUG = False
3. Configure ALLOWED_HOSTS
4. Use PostgreSQL instead of SQLite
5. Set up proper MEDIA storage (S3, etc.)
6. Enable HTTPS
7. Configure OPENAI_API_KEY in environment
8. Run migrations
9. Collect static files
10. Set up proper logging

### Security Checklist:
- [ ] SECRET_KEY changed
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configured
- [ ] Database secured
- [ ] HTTPS enabled
- [ ] API keys in environment variables
- [ ] Media files properly stored
- [ ] Regular backups enabled

