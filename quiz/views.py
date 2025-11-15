from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.db.models import Count, Avg, Q, Max
from .models import Subject, Test, Question, Option, AccessCode, TestSession, UserAnswer, UserLogin
from .ai_parser import AIQuestionParser
import os


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_staff(user):
    return user.is_authenticated and user.is_staff


def parse_test_file(test):
    """Parse test file using AI"""
    try:
        parser = AIQuestionParser()
        question_file_path = test.question_file.path
        answer_file_path = test.answer_file.path if test.answer_file else None

        questions_data = parser.parse_with_ai(
            question_file_path,
            test.answer_marking,
            answer_file_path
        )

        if not questions_data:
            return False

        for q_data in questions_data:
            question = Question.objects.create(
                test=test,
                text=q_data['text'],
                order=q_data.get('order', 0)
            )

            for opt_data in q_data['options']:
                Option.objects.create(
                    question=question,
                    text=opt_data['text'],
                    is_correct=opt_data['is_correct'],
                    order=opt_data.get('order', 0)
                )

        return True
    except Exception as e:
        print(f"Parse error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# ADMIN VIEWS
# ============================================================================

def admin_register(request):
    """One-time admin registration"""
    from django.contrib.auth.models import User

    if User.objects.filter(is_staff=True).exists():
        messages.error(request, 'Admin already registered. Please login.')
        return redirect('admin_login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('admin_register')

        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('admin_register')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('admin_register')

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            messages.success(request, f'Admin account "{username}" created successfully! Please login.')
            return redirect('admin_login')
        except Exception as e:
            messages.error(request, f'Error creating admin: {str(e)}')
            return redirect('admin_register')

    return render(request, 'admin_custom/register.html')


def admin_login(request):
    """Admin login"""
    from django.contrib.auth.models import User

    if not User.objects.filter(is_staff=True).exists():
        messages.info(request, 'No admin account exists. Please register first.')
        return redirect('admin_register')

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
    used_codes = AccessCode.objects.annotate(
        session_count=Count('sessions')
    ).filter(session_count__gt=0).count()

    context = {
        'total_subjects': Subject.objects.count(),
        'total_tests': Test.objects.count(),
        'total_codes': AccessCode.objects.count(),
        'total_sessions': TestSession.objects.filter(is_completed=True).count(),
        'recent_sessions': TestSession.objects.filter(is_completed=True).select_related('access_code', 'test').order_by('-completed_at')[:10],
        'active_codes': AccessCode.objects.filter(is_active=True).count(),
        'used_codes': used_codes,
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
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        question_file = request.FILES.get('question_file')
        answer_file = request.FILES.get('answer_file')
        answer_marking = request.POST.get('answer_marking')
        time_limit = int(request.POST.get('time_limit', 60))
        passing_score = int(request.POST.get('passing_score', 70))

        if not title and question_file:
            title = os.path.splitext(question_file.name)[0]

        test = Test.objects.create(
            subject=subject,
            title=title or 'Test',
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

        elif action == 'edit_question':
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, id=question_id, test=test)
            question.text = request.POST.get('question_text')
            question.save()
            messages.success(request, 'Question updated!')

        elif action == 'edit_option':
            option_id = request.POST.get('option_id')
            option = get_object_or_404(Option, id=option_id)
            option.text = request.POST.get('option_text')
            option.is_correct = request.POST.get(f'correct_{option_id}') == 'on'
            option.save()

            option.question.options.exclude(id=option_id).update(is_correct=False) if option.is_correct else None
            messages.success(request, 'Option updated!')

        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            Question.objects.filter(id=question_id, test=test).delete()
            messages.success(request, 'Question deleted!')
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
        max_attempts_per_user = int(request.POST.get('max_attempts', 0))

        subject = Subject.objects.get(id=subject_id) if subject_id else None

        generated = []
        for _ in range(count):
            code = AccessCode.objects.create(
                subject=subject,
                max_attempts_per_user=max_attempts_per_user,
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


@login_required
@user_passes_test(is_staff)
def admin_users(request):
    """View all logged in users"""
    users_data = []

    for user_login in UserLogin.objects.select_related('access_code').order_by('-last_activity'):
        sessions = TestSession.objects.filter(
            user_name=user_login.user_name,
            access_code=user_login.access_code
        )

        total_tests = sessions.count()
        completed = sessions.filter(is_completed=True)
        avg_score = completed.aggregate(avg=Avg('score'))['avg']

        users_data.append({
            'user_name': user_login.user_name,
            'access_code__code': user_login.access_code.code,
            'total_tests': total_tests,
            'completed_tests': completed.count(),
            'avg_score': avg_score,
            'last_activity': user_login.last_activity,
            'login_at': user_login.login_at
        })

    context = {'users': users_data}
    return render(request, 'admin_custom/users.html', context)


@login_required
@user_passes_test(is_staff)
def admin_user_detail(request, user_name, access_code):
    """View individual user details"""
    from django.utils.http import unquote
    user_name = unquote(user_name)

    code_obj = get_object_or_404(AccessCode, code=access_code)
    user_sessions = TestSession.objects.filter(
        user_name=user_name,
        access_code=code_obj
    ).select_related('test', 'access_code').order_by('-started_at')

    if request.method == 'POST' and 'delete_user' in request.POST:
        user_sessions.delete()
        messages.success(request, f'All sessions for {user_name} deleted successfully')
        return redirect('admin_users')

    context = {
        'user_name': user_name,
        'access_code': code_obj,
        'sessions': user_sessions
    }
    return render(request, 'admin_custom/user_detail.html', context)


# ============================================================================
# USER VIEWS
# ============================================================================

def login_view(request):
    """User login with access code"""
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

            if not access_code.first_used_at:
                access_code.first_used_at = timezone.now()
                access_code.save()

            UserLogin.objects.update_or_create(
                access_code=access_code,
                user_name=name,
                defaults={'last_activity': timezone.now()}
            )

            request.session['access_code_id'] = access_code.id
            request.session['user_name'] = name

            messages.success(request, f'Welcome, {name}!')
            return redirect('test_list')

        except AccessCode.DoesNotExist:
            messages.error(request, 'Invalid access code. Please check and try again.')

    return render(request, 'quiz/login.html')


def test_list(request):
    """List available tests"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])

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

    user_name = request.session.get('user_name', '')
    user_sessions = TestSession.objects.filter(access_code=access_code, user_name=user_name)
    total_sessions = user_sessions.count()
    remaining = None
    if access_code.max_attempts_per_user > 0:
        remaining = access_code.max_attempts_per_user - total_sessions

    context = {
        'subjects': subjects_dict.values(),
        'user_name': user_name,
        'remaining_attempts': remaining,
        'total_sessions': total_sessions,
    }
    return render(request, 'quiz/test_list.html', context)


def start_test(request, test_id):
    """Show test mode selection page"""
    if 'access_code_id' not in request.session or 'user_name' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])
    test = get_object_or_404(Test, id=test_id, is_published=True)
    user_name = request.session['user_name']

    # Check max attempts per user
    if access_code.max_attempts_per_user > 0:
        user_attempts = TestSession.objects.filter(
            access_code=access_code,
            user_name=user_name
        ).count()
        if user_attempts >= access_code.max_attempts_per_user:
            messages.error(request, 'Maksimal urinishlar soniga yetdingiz.')
            return redirect('test_list')

    if request.method == 'POST':
        test_mode = request.POST.get('test_mode', 'batch_25')

        session = TestSession.objects.create(
            access_code=access_code,
            test=test,
            user_name=user_name,
            test_mode=test_mode,
            total_questions=test.questions.count()
        )

        request.session['test_session_id'] = session.id
        request.session['test_start_time'] = timezone.now().isoformat()
        request.session['current_question'] = 0

        if test_mode == 'one_by_one':
            import random
            question_ids = list(test.questions.values_list('id', flat=True))
            random.shuffle(question_ids)
            request.session['question_order'] = question_ids

        return redirect('take_test')

    context = {
        'test': test,
        'question_count': test.questions.count()
    }
    return render(request, 'quiz/select_mode.html', context)


def take_test(request):
    """Take test page - supports two modes"""
    if 'test_session_id' not in request.session:
        return redirect('test_list')

    session = get_object_or_404(TestSession, id=request.session['test_session_id'])

    if session.is_completed:
        return redirect('test_results', session_id=session.id)

    if session.test_mode == 'one_by_one':
        question_order = request.session.get('question_order', [])
        if not question_order:
            import random
            question_order = list(session.test.questions.values_list('id', flat=True))
            random.shuffle(question_order)
            request.session['question_order'] = question_order

        all_questions = Question.objects.filter(id__in=question_order).prefetch_related('options')
        questions_dict = {q.id: q for q in all_questions}
        ordered_questions = [questions_dict[qid] for qid in question_order if qid in questions_dict]
    else:
        ordered_questions = session.test.questions.all().order_by('order').prefetch_related('options')

    answered = UserAnswer.objects.filter(session=session).values_list('question_id', flat=True)

    if session.test_mode == 'one_by_one':
        current_index = request.session.get('current_question', 0)

        if request.method == 'POST':
            current_question = ordered_questions[current_index]
            option_id = request.POST.get(f'question_{current_question.id}')
            if option_id:
                option = get_object_or_404(Option, id=option_id, question=current_question)
                UserAnswer.objects.update_or_create(
                    session=session,
                    question=current_question,
                    defaults={
                        'selected_option': option,
                        'is_correct': option.is_correct
                    }
                )

            if 'finish_test' in request.POST:
                correct = UserAnswer.objects.filter(session=session, is_correct=True).count()
                session.correct_answers = correct
                session.total_questions = UserAnswer.objects.filter(session=session).count()
                session.score = session.calculate_score()
                session.is_completed = True
                session.completed_at = timezone.now()
                session.save()
                return redirect('test_results', session_id=session.id)

            current_index += 1
            request.session['current_question'] = current_index

            if current_index >= len(ordered_questions):
                messages.info(request, 'Barcha savollarga javob berdingiz. Testni yakunlashingiz mumkin.')
                current_index = len(ordered_questions) - 1
                request.session['current_question'] = current_index

            messages.success(request, 'Javob saqlandi!')
            return redirect('take_test')

        if current_index >= len(ordered_questions):
            current_index = len(ordered_questions) - 1

        current_question = ordered_questions[current_index]

        context = {
            'session': session,
            'question': current_question,
            'current_index': current_index,
            'total_questions': len(ordered_questions),
            'answered_count': UserAnswer.objects.filter(session=session).count(),
            'user_name': session.user_name,
            'mode': 'one_by_one'
        }
        return render(request, 'quiz/take_test.html', context)

    else:
        if request.method == 'POST':
            for question in ordered_questions[:25]:
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

            messages.success(request, 'Javoblar saqlandi!')
            return redirect('take_test')

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
            'questions': ordered_questions[:25],
            'answered_ids': list(answered),
            'time_remaining': time_remaining,
            'user_name': session.user_name,
            'mode': 'batch_25'
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
        'user_name': session.user_name
    }
    return render(request, 'quiz/test_results.html', context)


def my_statistics(request):
    """User statistics dashboard"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])
    user_name = request.session['user_name']

    sessions = TestSession.objects.filter(
        access_code=access_code,
        user_name=user_name,
        is_completed=True
    ).select_related('test').order_by('started_at')

    total_tests = sessions.count()
    if total_tests > 0:
        avg_score = sessions.aggregate(Avg('score'))['score__avg']
        best_score = sessions.aggregate(Max('score'))['score__max']
        recent_sessions = sessions.order_by('-started_at')[:5]
    else:
        avg_score = 0
        best_score = 0
        recent_sessions = []

    wrong_answers = UserAnswer.objects.filter(
        session__access_code=access_code,
        session__user_name=user_name,
        session__is_completed=True,
        is_correct=False
    ).select_related('question').values('question__id', 'question__text').annotate(
        wrong_count=Count('id')
    ).order_by('-wrong_count')[:10]

    context = {
        'total_tests': total_tests,
        'avg_score': round(avg_score, 1) if avg_score else 0,
        'best_score': best_score,
        'sessions': recent_sessions,
        'wrong_answers': wrong_answers,
        'user_name': user_name
    }
    return render(request, 'quiz/my_statistics.html', context)


def practice_mode(request):
    """Practice wrong answers"""
    if 'access_code_id' not in request.session:
        return redirect('login')

    access_code = get_object_or_404(AccessCode, id=request.session['access_code_id'])
    user_name = request.session['user_name']

    wrong_questions = UserAnswer.objects.filter(
        session__access_code=access_code,
        session__user_name=user_name,
        session__is_completed=True,
        is_correct=False
    ).select_related('question').values_list('question__id', flat=True).distinct()

    questions = Question.objects.filter(id__in=wrong_questions).prefetch_related('options')

    context = {
        'questions': questions,
        'user_name': user_name
    }
    return render(request, 'quiz/practice_mode.html', context)


def logout_view(request):
    """Logout user"""
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('login')
