from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Subject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Test(models.Model):
    ANSWER_MARKING_CHOICES = [
        ('hash_start', '# at start of correct answer'),
        ('plus_end', '+ or ++++ at end of correct answer'),
        ('separate_file', 'Answers in separate file (1.A, 2.B format)'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    question_file = models.FileField(upload_to='test_files/', help_text='Upload PDF/DOCX with questions')
    answer_file = models.FileField(upload_to='test_files/', blank=True, null=True, help_text='Upload if answers are in separate file')

    answer_marking = models.CharField(max_length=20, choices=ANSWER_MARKING_CHOICES, default='hash_start')

    is_published = models.BooleanField(default=False, help_text='Make test available to users')
    is_parsed = models.BooleanField(default=False, help_text='File has been parsed successfully')

    time_limit = models.IntegerField(default=60, help_text='Time limit in minutes (0 for no limit)')
    passing_score = models.IntegerField(default=70, help_text='Passing score percentage')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(help_text='Question text')
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

    class Meta:
        ordering = ['order']


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField(help_text='Option text')
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:30]}"

    class Meta:
        ordering = ['order']


class AccessCode(models.Model):
    code = models.CharField(max_length=20, unique=True, default=generate_unique_code)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True, help_text='Limit to specific subject (optional)')
    max_attempts_per_user = models.IntegerField(default=0, help_text='Maximum test attempts per user (0 for unlimited)')
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Expiration date (optional)')

    is_active = models.BooleanField(default=True)
    first_used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        user_count = self.sessions.values('user_name').distinct().count()
        return f"{self.code} - {user_count} user(s)"

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def get_users(self):
        return self.sessions.values_list('user_name', flat=True).distinct()

    class Meta:
        ordering = ['-created_at']


class TestSession(models.Model):
    TEST_MODE_CHOICES = [
        ('one_by_one', 'Birma-bir (istalgan vaqtda yakunlash)'),
        ('batch_25', '25 ta savol (hammasi birdan)')
    ]

    access_code = models.ForeignKey(AccessCode, on_delete=models.CASCADE, related_name='sessions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions')
    user_name = models.CharField(max_length=200, default='Unknown User', help_text='Name of the user taking this test')
    test_mode = models.CharField(max_length=20, choices=TEST_MODE_CHOICES, default='batch_25')

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    score = models.FloatField(default=0.0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user_name} - {self.test.title} ({self.score}%)"

    def calculate_score(self):
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 2)

    class Meta:
        ordering = ['-started_at']


class UserAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.user_name} - Q{self.question.order}"

    class Meta:
        ordering = ['question__order']


class UserLogin(models.Model):
    access_code = models.ForeignKey(AccessCode, on_delete=models.CASCADE, related_name='logins')
    user_name = models.CharField(max_length=200)
    login_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_name} - {self.access_code.code}"

    class Meta:
        ordering = ['-last_activity']
        unique_together = ['access_code', 'user_name']
