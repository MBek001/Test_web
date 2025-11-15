# Quiz Platform - Online Training & Testing System

A Django-based quiz platform that allows administrators to upload test files in various formats (PDF, DOCX) and users to take tests using unique access codes.

## Features

### For Administrators
- Upload test files in PDF or DOCX format
- Flexible answer marking support:
  - `#` at the start of correct answer
  - `+` or `++++` at the end of correct answer
  - Separate answer file (1.A, 2.B format)
- Parse files automatically to extract questions and answers
- Publish/unpublish tests
- Generate unique access codes for users
- Track user progress and results
- Subject/category management

### For Users
- Login with unique access code
- Select subject and test
- Take tests with optional time limits
- Save progress while taking test
- View detailed results with correct answers
- Track attempts and scores

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 4. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage Guide

### Admin Panel Access

1. Navigate to `http://127.0.0.1:8000/admin/`
2. Login with your admin credentials

### Setting Up Tests

#### Step 1: Create Subjects

1. Go to **Quiz** → **Subjects**
2. Click **Add Subject**
3. Enter subject name and description
4. Click **Save**

#### Step 2: Upload Test Files

1. Go to **Quiz** → **Tests**
2. Click **Add Test**
3. Fill in the form:
   - **Subject**: Select the subject
   - **Title**: Test name
   - **Description**: Optional test description
   - **Question File**: Upload PDF or DOCX file with questions
   - **Answer File**: Upload if answers are in a separate file
   - **Answer Marking**: Select how correct answers are marked in your file:
     - `# at start of correct answer` - For DOCX files with # marking
     - `+ or ++++ at end of correct answer` - For files with + marking
     - `Answers in separate file` - For separate answer files
   - **Time Limit**: Minutes (0 for no limit)
   - **Passing Score**: Percentage required to pass
4. Click **Save**

#### Step 3: Parse Test Files

1. Go to **Quiz** → **Tests**
2. Select the test(s) you just created
3. From the "Actions" dropdown, select **Parse selected test files**
4. Click **Go**
5. Check for success messages

#### Step 4: Publish Tests

1. Select the parsed test(s)
2. From the "Actions" dropdown, select **Publish selected tests**
3. Click **Go**

#### Step 5: Generate Access Codes

1. Go to **Quiz** → **Access codes**
2. Click **Generate Codes** button (or use the action)
3. Enter:
   - Number of codes to generate
   - Subject restriction (optional)
4. Click **Generate Codes**
5. The generated codes will appear in the list
6. Share these codes with users

### User Flow

1. Navigate to `http://127.0.0.1:8000/`
2. Enter access code and name
3. Select subject
4. Select test to take
5. Answer questions
6. Submit test
7. View results

## File Format Examples

### Format 1: DOCX with # marking

```
Question text here?
====
Wrong answer
====
#Correct answer
====
Wrong answer
====
++++
```

### Format 2: PDF/DOCX with ++++ marking

```
1. Question text here?
A) Wrong answer
B) Correct answer ++++
C) Wrong answer
D) Wrong answer
```

### Format 3: Separate Files

**questions.pdf:**
```
1. Question text?
A) Option 1
B) Option 2
C) Option 3
D) Option 4
```

**answers.pdf:**
```
1. B
2. C
3. A
```

## Managing Access Codes

### Access Code Features:
- **Subject Restriction**: Limit code to specific subject
- **Max Attempts**: Set maximum number of tests (0 = unlimited)
- **Expiration Date**: Set when code expires
- **Active/Inactive**: Enable/disable codes

### Viewing Results:
1. Go to **Quiz** → **Test sessions**
2. View all user sessions with scores
3. Click on a session to see detailed answers

## Admin Actions Reference

### Test Actions:
- **Parse selected test files**: Extract questions from uploaded files
- **Publish selected tests**: Make tests available to users
- **Unpublish selected tests**: Hide tests from users

### Access Code Actions:
- **Generate new access codes**: Bulk create access codes
- **Deactivate selected codes**: Disable codes

## Troubleshooting

### Tests not appearing for users?
- Ensure test is **parsed** (is_parsed = True)
- Ensure test is **published** (is_published = True)
- Check that subject has published tests

### File parsing errors?
- Verify file format matches selected answer marking pattern
- Check that file is not corrupted
- Ensure text can be extracted from PDF
- For DOCX, ensure proper separators (====, ++++)

### Access code issues?
- Check if code is active
- Check if code has expired
- Verify max attempts not exceeded

## Database Models

- **Subject**: Test categories
- **Test**: Test information and files
- **Question**: Individual questions
- **Option**: Answer options for questions
- **AccessCode**: User access codes
- **TestSession**: User test sessions
- **UserAnswer**: Individual user answers

## Security Notes

For production deployment:
1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL, MySQL)
5. Set up proper media file storage
6. Enable HTTPS
7. Configure CSRF settings

## Support

For issues or questions, please contact the system administrator.
