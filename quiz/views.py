from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import Subject, Test, Question, Option, AccessCode, TestSession, UserAnswer
from .file_parsers import QuestionParser
import os


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_staff(user):
    return user.is_authenticated and user.is_staff


def parse_test_file(test, use_ai=False):
    """Parse test file and create questions"""
    try:
        file_extension = os.path.splitext(test.question_file.name)[1].lower()

        # Parse questions
        if file_extension in ['.pdf']:
            questions_data = QuestionParser.parse_pdf(
                test.question_file.path,
                test.answer_marking
            )
        elif file_extension in ['.docx', '.doc']:
            questions_data = QuestionParser.parse_docx(
                test.question_file.path,
                test.answer_marking
            )
        else:
            return False

        # If answers are in separate file
        if test.answer_marking == 'separate_file' and test.answer_file:
            answer_extension = os.path.splitext(test.answer_file.name)[1].lower()
            answers = QuestionParser.parse_answers_file(
                test.answer_file.path,
                answer_extension
            )
            questions_data = QuestionParser.merge_questions_with_answers(questions_data, answers)

        # Create questions and options
        for q_data in questions_data:
            question = Question.objects.create(
                test=test,
                text=q_data['text'],
                order=q_data['order']
            )

            for opt_data in q_data['options']:
                Option.objects.create(
                    question=question,
                    text=opt_data['text'],
                    is_correct=opt_data['is_correct'],
                    order=opt_data['order']
                )

        return True
    except Exception as e:
        print(f"Parse error: {str(e)}")
        return False


# ============================================================================
# ADMIN VIEWS
# ============================================================================

def admin_login(request):
    """Admin login page"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or you do not have admin access.')

    return render(request, 'admin_custom/login.html')


def admin_logout(request):
    """Admin logout"""
    auth_logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('admin_login')


@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    """Admin dashboard"""
    context = {
        'total_subjects': Subject.objects.count(),
        'total_tests': Test.objects.count(),
        'total_codes': AccessCode.objects.count(),
        'total_sessions': TestSession.objects.filter(is_completed=True).count(),
        'recent_sessions': TestSession.objects.filter(is_completed=True).select_related('access_code', 'test').order_by('-completed_at')[:10],
        'active_codes': AccessCode.objects.filter(is_active=True).count(),
        'used_codes': AccessCode.objects.filter(is_used=True).count(),
    }
    return render(request, 'admin_custom/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def admin_subjects(request):
    """List all subjects"""
    subjects = Subject.objects.annotate(test_count=Count('tests')).order_by('name')
    return render(request, 'admin_custom/subjects.html', {'subjects': subjects})


@login_required
@user_passes_test(is_staff)
def admin_subject_create(request):
    """Create new subject"""
    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        subject_description = request.POST.get('subject_description', '')

        subject = Subject.objects.create(
            name=subject_name,
            description=subject_description
        )

        messages.success(request, f'Subject "{subject_name}" created successfully!')
        return redirect('admin_subject_detail', subject_id=subject.id)

    return render(request, 'admin_custom/subject_create.html')


@login_required
@user_passes_test(is_staff)
def admin_subject_detail(request, subject_id):
    """View and manage subject"""
    subject = get_object_or_404(Subject, id=subject_id)
    tests = subject.tests.annotate(question_count=Count('questions')).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            subject.name = request.POST.get('name')
            subject.description = request.POST.get('description', '')
            subject.save()
            messages.success(request, 'Subject updated!')

        elif action == 'delete':
            name = subject.name
            subject.delete()
            messages.success(request, f'Subject "{name}" deleted!')
            return redirect('admin_subjects')

    context = {'subject': subject, 'tests': tests}
    return render(request, 'admin_custom/subject_detail.html', context)


@login_required
@user_passes_test(is_staff)
def admin_test_create(request, subject_id):
    """Create new test"""
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        question_file = request.FILES.get('question_file')
        answer_file = request.FILES.get('answer_file')
        answer_marking = request.POST.get('answer_marking')
        time_limit = int(request.POST.get('time_limit', 60))
        passing_score = int(request.POST.get('passing_score', 70))

        # Create test
        test = Test.objects.create(
            subject=subject,
            title=title,
            description=description,
            question_file=question_file,
            answer_file=answer_file if answer_file else None,
            answer_marking=answer_marking,
            time_limit=time_limit,
            passing_score=passing_score,
        )

        # Auto-parse
        try:
            success = parse_test_file(test)
            if success:
                test.is_parsed = True
                test.save()
                messages.success(request, f'Test "{title}" created and parsed successfully with {test.questions.count()} questions!')
            else:
                messages.warning(request, f'Test created but parsing failed. Check file format.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('admin_subject_detail', subject_id=subject.id)

    return render(request, 'admin_custom/test_create.html', {'subject': subject})


@login_required
@user_passes_test(is_staff)
def admin_test_detail(request, test_id):
    """View and manage test"""
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.prefetch_related('options').order_by('order')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            test.title = request.POST.get('title')
            test.description = request.POST.get('description', '')
            test.time_limit = int(request.POST.get('time_limit', 60))
            test.passing_score = int(request.POST.get('passing_score', 70))
            test.save()
            messages.success(request, 'Test updated!')

        elif action == 'publish':
            test.is_published = True
            test.save()
            messages.success(request, 'Test published!')

        elif action == 'unpublish':
            test.is_published = False
            test.save()
            messages.success(request, 'Test unpublished!')

        elif action == 'delete':
            subject_id = test.subject.id
            test.delete()
            messages.success(request, 'Test deleted!')
            return redirect('admin_subject_detail', subject_id=subject_id)

        elif action == 'reparse':
            test.questions.all().delete()
            success = parse_test_file(test)
            if success:
                test.is_parsed = True
                test.save()
                messages.success(request, f'Reparsed! Found {test.questions.count()} questions.')
            else:
                messages.error(request, 'Failed to parse.')
            return redirect('admin_test_detail', test_id=test.id)

    context = {'test': test, 'questions': questions}
    return render(request, 'admin_custom/test_detail.html', context)


@login_required
@user_passes_test(is_staff)
def admin_codes(request):
    """Manage access codes"""
    codes = AccessCode.objects.select_related('subject').annotate(
        session_count=Count('sessions')
    ).order_by('-created_at')

    if request.method == 'POST':
        count = int(request.POST.get('count', 1))
        subject_id = request.POST.get('subject')
        max_attempts = int(request.POST.get('max_attempts', 0))

        subject = Subject.objects.get(id=subject_id) if subject_id else None

        generated = []
        for _ in range(count):
            code = AccessCode.objects.create(
                subject=subject,
                max_attempts=max_attempts,
                created_by=request.user
            )
            generated.append(code.code)

        messages.success(request, f'Generated {count} code(s): {", ".join(generated)}')
        return redirect('admin_codes')

    context = {
        'codes': codes,
        'subjects': Subject.objects.all(),
    }
    return render(request, 'admin_custom/codes.html', context)


@login_required
@user_passes_test(is_staff)
def admin_results(request):
    """View all results"""
    sessions = TestSession.objects.filter(is_completed=True).select_related(
        'access_code', 'test', 'test__subject'
    ).order_by('-completed_at')

    subject_id = request.GET.get('subject')
    if subject_id:
        sessions = sessions.filter(test__subject_id=subject_id)

    context = {
        'sessions': sessions,
        'subjects': Subject.objects.all(),
    }
    return render(request, 'admin_custom/results.html', context)


@login_required
@user_passes_test(is_staff)
def admin_session_detail(request, session_id):
    """View session details"""
    session = get_object_or_404(TestSession, id=session_id)
    answers = UserAnswer.objects.filter(session=session).select_related(
        'question', 'selected_option'
    ).order_by('question__order')

    context = {'session': session, 'answers': answers}
    return render(request, 'admin_custom/session_detail.html', context)


# ============================================================================
# USER VIEWS
# ============================================================================

def login_view(request):
    """User login with access code - FIXED"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()

        if not code or not name:
            messages.error(request, 'Please enter both access code and your name.')
            return redirect('login')

        try:
            access_code = AccessCode.objects.get(code=code)

            if not access_code.is_valid():
                messages.error(request, 'This access code is expired or inactive.')
                return redirect('login')

            # FIX: Always update name if empty
            if not access_code.name:
                access_code.name = name
                access_code.first_used_at = timezone.now()

            # Always mark as used
            access_code.is_used = True
            access_code.save()

            # Store in session
            request.session['access_code_id'] = access_code.id
            request.session['user_name'] = access_code.name

            messages.success(request, f'Welcome, {access_code.name}!')
            return redirect('test_list')

        except AccessCode.DoesNotExist:
            messages.error(request, 'Invalid access code. Please check and try again.')

    return render(request, 'quiz/login.html')


def test_list(request):
    """List all available tests - SIMPLIFIED"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])

    # Get published tests
    if access_code.subject:
        tests = Test.objects.filter(
            subject=access_code.subject,
            is_published=True,
            is_parsed=True
        ).select_related('subject').annotate(question_count=Count('questions'))
    else:
        tests = Test.objects.filter(
            is_published=True,
            is_parsed=True
        ).select_related('subject').annotate(question_count=Count('questions'))

    # Group by subject
    subjects_dict = {}
    for test in tests:
        subject_name = test.subject.name
        if subject_name not in subjects_dict:
            subjects_dict[subject_name] = {
                'name': subject_name,
                'description': test.subject.description,
                'tests': []
            }
        subjects_dict[subject_name]['tests'].append(test)

    # Check attempts
    total_sessions = TestSession.objects.filter(access_code=access_code).count()
    remaining = None
    if access_code.max_attempts > 0:
        remaining = access_code.max_attempts - total_sessions

    context = {
        'subjects': subjects_dict.values(),
        'user_name': access_code.name,
        'remaining_attempts': remaining,
        'total_sessions': total_sessions,
    }
    return render(request, 'quiz/test_list.html', context)


def start_test(request, test_id):
    """Start a test"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])
    test = get_object_or_404(Test, id=test_id, is_published=True)

    # Check max attempts
    if access_code.max_attempts > 0:
        attempts_count = TestSession.objects.filter(access_code=access_code).count()
        if attempts_count >= access_code.max_attempts:
            messages.error(request, 'You have reached the maximum number of attempts.')
            return redirect('test_list')

    # Create new test session
    session = TestSession.objects.create(
        access_code=access_code,
        test=test,
        total_questions=test.questions.count()
    )

    request.session['test_session_id'] = session.id
    request.session['test_start_time'] = timezone.now().isoformat()

    return redirect('take_test')


def take_test(request):
    """Take test page"""
    if 'test_session_id' not in request.session:
        return redirect('test_list')

    session = get_object_or_404(TestSession, id=request.session['test_session_id'])

    if session.is_completed:
        return redirect('test_results', session_id=session.id)

    questions = session.test.questions.all().prefetch_related('options')
    answered = UserAnswer.objects.filter(session=session).values_list('question_id', flat=True)

    if request.method == 'POST':
        # Save answers
        for question in questions:
            option_id = request.POST.get(f'question_{question.id}')
            if option_id:
                option = get_object_or_404(Option, id=option_id, question=question)
                UserAnswer.objects.update_or_create(
                    session=session,
                    question=question,
                    defaults={
                        'selected_option': option,
                        'is_correct': option.is_correct
                    }
                )

        if 'submit_test' in request.POST:
            correct = UserAnswer.objects.filter(session=session, is_correct=True).count()
            session.correct_answers = correct
            session.score = session.calculate_score()
            session.is_completed = True
            session.completed_at = timezone.now()
            session.save()
            return redirect('test_results', session_id=session.id)

        messages.success(request, 'Progress saved!')
        return redirect('take_test')

    # Calculate time remaining
    time_remaining = None
    if session.test.time_limit > 0:
        start_time = timezone.datetime.fromisoformat(request.session['test_start_time'])
        if timezone.is_aware(start_time):
            elapsed = (timezone.now() - start_time).total_seconds() / 60
        else:
            start_time = timezone.make_aware(start_time)
            elapsed = (timezone.now() - start_time).total_seconds() / 60
        time_remaining = max(0, session.test.time_limit - elapsed)

    context = {
        'session': session,
        'questions': questions,
        'answered_ids': list(answered),
        'time_remaining': time_remaining,
        'user_name': session.access_code.name
    }
    return render(request, 'quiz/take_test.html', context)


def test_results(request, session_id):
    """Show test results"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    session = get_object_or_404(TestSession, id=session_id)

    if session.access_code.id != request.session['access_code_id']:
        messages.error(request, 'Unauthorized access.')
        return redirect('test_list')

    answers = UserAnswer.objects.filter(session=session).select_related('question', 'selected_option')
    passed = session.score >= session.test.passing_score

    context = {
        'session': session,
        'answers': answers,
        'passed': passed,
        'user_name': session.access_code.name
    }
    return render(request, 'quiz/test_results.html', context)


def logout_view(request):
    """Logout user"""
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('login')
