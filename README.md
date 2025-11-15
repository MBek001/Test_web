# Quiz Platform - Online Training & Testing System

A Django-based quiz platform with a custom admin panel for managing tests and tracking user progress.

## Features

### Custom Admin Panel
- Intuitive admin interface (no Django admin)
- Dashboard with statistics
- One-click test file upload and parsing
- Subject and test management
- Access code generation
- Detailed results tracking

### For Users
- Simple login with access code
- Clean test selection interface
- Timer support
- Progress saving
- Detailed results with correct answers

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create admin account
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### 2. Access the Platform

- **Admin Panel**: `http://127.0.0.1:8000/admin-panel/login/`
- **User Login**: `http://127.0.0.1:8000/`

## Admin Workflow (Simple!)

### Step 1: Create a Subject
1. Login to admin panel
2. Click "Create New Subject"
3. Enter subject name (e.g., "Python Programming")
4. Save

### Step 2: Upload Test File
1. Click on the subject you created
2. Click "Upload Test"
3. Fill in the form:
   - **Title**: Test name
   - **Question File**: Upload PDF or DOCX
   - **Answer Marking**: Choose how correct answers are marked:
     - `# at start` - For files like: `#Correct answer`
     - `+++ at end` - For files like: `Correct answer ++++`
     - `Separate file` - Upload answer file separately
   - **Answer File**: Only if you selected "Separate file"
   - **Time Limit**: Minutes (0 for no limit)
   - **Passing Score**: Percentage required to pass
4. Click "Upload & Parse Test"

The system will automatically:
- Parse the file
- Extract all questions and options
- Mark correct answers
- Show you the results

### Step 3: Review Questions
- You'll see all parsed questions
- Verify they look correct
- If needed, click "Reparse File" to try again

### Step 4: Publish Test
- Click "Publish" button
- Test is now available to users

### Step 5: Generate Access Codes
1. Go to "Access Codes" in menu
2. Enter number of codes to generate
3. Optionally restrict to a subject
4. Click "Generate Codes"
5. Share codes with users

### Step 6: View Results
- Click "Results" in menu
- See all user sessions
- Click "View Details" to see individual answers

## Supported File Formats

### Format 1: DOCX with # marking
```
Question text?
====
Wrong option
====
#Correct option
====
Wrong option
====
++++

Next question?
====
#Correct
====
Wrong
====
++++
```

### Format 2: PDF/DOCX with ++++ marking
```
1. Question text?
A) Wrong answer
B) Correct answer ++++
C) Wrong answer
D) Wrong answer

2. Another question?
A) Wrong
B) Wrong
C) Correct ++++
D) Wrong
```

### Format 3: Separate Files

**questions.pdf:**
```
1. Question text?
A) Option 1
B) Option 2
C) Option 3
D) Option 4

2. Another question?
A) Option A
B) Option B
C) Option C
```

**answers.pdf:**
```
1. B
2. C
```

## User Workflow

1. Go to `http://127.0.0.1:8000/`
2. Enter access code and name
3. See all available tests (grouped by subject)
4. Click "Start Test"
5. Answer questions
6. Submit test
7. View detailed results

## Features Explained

### Access Codes
- **Unique Code**: 8-character code (e.g., "AB12CD34")
- **User Name**: Saved when code is first used
- **Subject Restriction**: Optionally limit to one subject
- **Max Attempts**: Limit number of tests (0 = unlimited)
- **Status Tracking**: See who used which code

### Test Settings
- **Time Limit**: Auto-submit when time runs out
- **Passing Score**: Minimum percentage to pass
- **Published Status**: Control test availability

### Results Tracking
- See all user sessions
- Filter by subject
- View detailed answers for each session
- Track pass/fail rates

## File Parsing Logic

The system automatically detects:
1. Question numbers (1., 2., etc.)
2. Options (A), B), C), D) or A. B. C. D.
3. Correct answer markers (# or +++)
4. Question separators (==== or ++++)

## Troubleshooting

### Users not showing in database?
**Fixed!** The login bug has been resolved. User names now properly save to the database.

### File parsing failed?
1. Check file format matches selected answer marking
2. Ensure consistent formatting throughout file
3. Try "Reparse File" button
4. Check admin panel for error messages

### Tests not appearing for users?
1. Ensure test is **published** (not draft)
2. Check that test has questions (parsed successfully)
3. Verify access code isn't restricted to different subject

### Access code not working?
1. Check if code is active
2. Verify code hasn't expired
3. Check max attempts not exceeded

## Admin Panel Navigation

- **Dashboard**: Overview and statistics
- **Subjects**: Manage subjects and their tests
- **Access Codes**: Generate and manage user codes
- **Results**: View all test sessions and detailed answers

## Database Models

- **Subject**: Test categories/subjects
- **Test**: Tests with file uploads
- **Question**: Individual questions
- **Option**: Multiple choice options
- **AccessCode**: User access codes
- **TestSession**: User test attempts
- **UserAnswer**: Individual answers

## URLs

### User URLs
- `/` - Login
- `/tests/` - Test list
- `/test/{id}/start/` - Start test
- `/test/take/` - Take test
- `/test/results/{id}/` - View results

### Admin URLs
- `/admin-panel/login/` - Admin login
- `/admin-panel/` - Dashboard
- `/admin-panel/subjects/` - Manage subjects
- `/admin-panel/codes/` - Manage access codes
- `/admin-panel/results/` - View results

## Tips for Best Results

1. **Keep file formatting consistent**
2. **Use clear question separators** (====, ++++)
3. **Test with small file first** to verify parsing
4. **Review parsed questions** before publishing
5. **Generate codes in batches** for easier tracking
6. **Regular backups** of database

## Security Notes

For production:
1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use production database (PostgreSQL recommended)
5. Set up proper file storage
6. Enable HTTPS
7. Regular security updates

## Support

All major issues have been fixed:
- ✅ User login database storage
- ✅ Custom admin panel
- ✅ Simplified user interface
- ✅ Automatic file parsing
- ✅ One-step test upload

The platform is now simple, clean, and fully functional!
