from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


def generate_unique_code():
    """Generate a unique 8-character code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Subject(models.Model):
    """Subject/Category for tests"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Test(models.Model):
    """Test model with file upload support"""
    ANSWER_MARKING_CHOICES = [
        ('hash_start', '# at start of correct answer'),
        ('plus_end', '+ or ++++ at end of correct answer'),
        ('separate_file', 'Answers in separate file (1.A, 2.B format)'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    # File uploads
    question_file = models.FileField(upload_to='test_files/', help_text='Upload PDF/DOCX with questions')
    answer_file = models.FileField(upload_to='test_files/', blank=True, null=True, help_text='Upload if answers are in separate file')

    # Answer marking pattern
    answer_marking = models.CharField(max_length=20, choices=ANSWER_MARKING_CHOICES, default='hash_start')

    # Status
    is_published = models.BooleanField(default=False, help_text='Make test available to users')
    is_parsed = models.BooleanField(default=False, help_text='File has been parsed successfully')

    # Settings
    time_limit = models.IntegerField(default=60, help_text='Time limit in minutes (0 for no limit)')
    passing_score = models.IntegerField(default=70, help_text='Passing score percentage')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class Question(models.Model):
    """Question model"""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(help_text='Question text')
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

    class Meta:
        ordering = ['order']


class Option(models.Model):
    """Answer option for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField(help_text='Option text')
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:30]}"

    class Meta:
        ordering = ['order']


class AccessCode(models.Model):
    """Unique access codes for users"""
    code = models.CharField(max_length=20, unique=True, default=generate_unique_code)
    name = models.CharField(max_length=200, blank=True, help_text='User name (filled when code is used)')

    # Restrictions
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True, help_text='Limit to specific subject (optional)')
    max_attempts = models.IntegerField(default=0, help_text='Maximum test attempts (0 for unlimited)')
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Expiration date (optional)')

    # Status
    is_active = models.BooleanField(default=True)
    is_used = models.BooleanField(default=False)
    first_used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.code} - {self.name if self.name else 'Unused'}"

    def is_valid(self):
        """Check if code is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    class Meta:
        ordering = ['-created_at']


class TestSession(models.Model):
    """Track user test sessions"""
    access_code = models.ForeignKey(AccessCode, on_delete=models.CASCADE, related_name='sessions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions')

    # Session info
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    # Results
    score = models.FloatField(default=0.0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.access_code.name} - {self.test.title} ({self.score}%)"

    def calculate_score(self):
        """Calculate test score"""
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 2)

    class Meta:
        ordering = ['-started_at']


class UserAnswer(models.Model):
    """Store user's answers"""
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.access_code.name} - Q{self.question.order}"

    class Meta:
        ordering = ['question__order']
