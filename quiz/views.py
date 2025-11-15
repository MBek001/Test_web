from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Subject, Test, Question, Option, AccessCode, TestSession, UserAnswer


def login_view(request):
    """User login with access code"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()

        try:
            access_code = AccessCode.objects.get(code=code)

            if not access_code.is_valid():
                messages.error(request, 'This access code is expired or inactive.')
                return redirect('login')

            # Update access code with user's name
            if not access_code.is_used:
                access_code.name = name
                access_code.is_used = True
                access_code.first_used_at = timezone.now()
                access_code.save()

            # Store in session
            request.session['access_code_id'] = access_code.id
            request.session['user_name'] = access_code.name

            return redirect('subject_selection')

        except AccessCode.DoesNotExist:
            messages.error(request, 'Invalid access code.')

    return render(request, 'quiz/login.html')


def subject_selection(request):
    """Select subject/category"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])

    # Get available subjects
    if access_code.subject:
        subjects = [access_code.subject]
    else:
        subjects = Subject.objects.filter(tests__is_published=True).distinct()

    context = {
        'subjects': subjects,
        'user_name': access_code.name
    }
    return render(request, 'quiz/subject_selection.html', context)


def test_selection(request, subject_id):
    """Select test from subject"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])
    subject = get_object_or_404(Subject, id=subject_id)

    # Check access
    if access_code.subject and access_code.subject != subject:
        messages.error(request, 'You do not have access to this subject.')
        return redirect('subject_selection')

    # Get published tests
    tests = Test.objects.filter(subject=subject, is_published=True, is_parsed=True)

    # Check max attempts
    if access_code.max_attempts > 0:
        attempts_count = TestSession.objects.filter(access_code=access_code).count()
        remaining = access_code.max_attempts - attempts_count
    else:
        remaining = None

    context = {
        'subject': subject,
        'tests': tests,
        'user_name': access_code.name,
        'remaining_attempts': remaining
    }
    return render(request, 'quiz/test_selection.html', context)


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
            return redirect('subject_selection')

    # Create new test session
    session = TestSession.objects.create(
        access_code=access_code,
        test=test,
        total_questions=test.questions.count()
    )

    # Store session in request session
    request.session['test_session_id'] = session.id
    request.session['test_start_time'] = timezone.now().isoformat()

    return redirect('take_test')


def take_test(request):
    """Take test page"""
    if 'test_session_id' not in request.session:
        return redirect('subject_selection')

    session = get_object_or_404(TestSession, id=request.session['test_session_id'])

    if session.is_completed:
        return redirect('test_results', session_id=session.id)

    # Get all questions
    questions = session.test.questions.all().prefetch_related('options')

    # Get already answered questions
    answered = UserAnswer.objects.filter(session=session).values_list('question_id', flat=True)

    if request.method == 'POST':
        # Process submitted answers
        for question in questions:
            option_id = request.POST.get(f'question_{question.id}')
            if option_id:
                option = get_object_or_404(Option, id=option_id, question=question)

                # Update or create answer
                UserAnswer.objects.update_or_create(
                    session=session,
                    question=question,
                    defaults={
                        'selected_option': option,
                        'is_correct': option.is_correct
                    }
                )

        # Check if test is being submitted
        if 'submit_test' in request.POST:
            # Calculate score
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

    # Check if user has access to this result
    if session.access_code.id != request.session['access_code_id']:
        messages.error(request, 'Unauthorized access.')
        return redirect('subject_selection')

    # Get all answers
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
