from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Subject, Test, Question, Option, AccessCode, TestSession, UserAnswer
from .file_parsers import QuestionParser
import os


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'test_count', 'created_at']
    search_fields = ['name', 'description']

    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = 'Tests'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'is_parsed', 'is_published', 'question_count', 'created_at']
    list_filter = ['subject', 'is_published', 'is_parsed', 'answer_marking']
    search_fields = ['title', 'description']
    readonly_fields = ['is_parsed', 'created_at', 'updated_at']

    actions = ['parse_files', 'publish_tests', 'unpublish_tests']

    fieldsets = (
        ('Basic Information', {
            'fields': ('subject', 'title', 'description')
        }),
        ('Files', {
            'fields': ('question_file', 'answer_file', 'answer_marking')
        }),
        ('Settings', {
            'fields': ('time_limit', 'passing_score')
        }),
        ('Status', {
            'fields': ('is_published', 'is_parsed', 'created_at', 'updated_at')
        }),
    )

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

    def parse_files(self, request, queryset):
        """Parse uploaded files and create questions"""
        parsed_count = 0
        error_count = 0

        for test in queryset:
            try:
                # Delete existing questions for this test
                test.questions.all().delete()

                # Get file extension
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
                    self.message_user(request, f"Unsupported file format for {test.title}", messages.ERROR)
                    continue

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

                test.is_parsed = True
                test.save()
                parsed_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error parsing {test.title}: {str(e)}",
                    messages.ERROR
                )

        if parsed_count > 0:
            self.message_user(
                request,
                f"Successfully parsed {parsed_count} test(s)",
                messages.SUCCESS
            )

    parse_files.short_description = "Parse selected test files"

    def publish_tests(self, request, queryset):
        """Publish tests to make them available to users"""
        unparsed = queryset.filter(is_parsed=False)
        if unparsed.exists():
            self.message_user(
                request,
                f"{unparsed.count()} test(s) need to be parsed first",
                messages.WARNING
            )

        updated = queryset.filter(is_parsed=True).update(is_published=True)
        self.message_user(
            request,
            f"{updated} test(s) published successfully",
            messages.SUCCESS
        )

    publish_tests.short_description = "Publish selected tests"

    def unpublish_tests(self, request, queryset):
        """Unpublish tests"""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f"{updated} test(s) unpublished",
            messages.SUCCESS
        )

    unpublish_tests.short_description = "Unpublish selected tests"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'test', 'order', 'option_count']
    list_filter = ['test__subject', 'test']
    search_fields = ['text']

    def short_text(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    short_text.short_description = 'Question'

    def option_count(self, obj):
        return obj.options.count()
    option_count.short_description = 'Options'


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'question', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__test']

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    short_text.short_description = 'Option'


@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'user_count', 'subject', 'is_active', 'usage_count', 'created_at']
    list_filter = ['is_active', 'subject']
    search_fields = ['code']
    readonly_fields = ['code', 'first_used_at', 'created_at']

    actions = ['generate_codes', 'deactivate_codes']

    fieldsets = (
        ('Code Information', {
            'fields': ('code',)
        }),
        ('Restrictions', {
            'fields': ('subject', 'max_attempts_per_user', 'expires_at')
        }),
        ('Status', {
            'fields': ('is_active', 'first_used_at', 'created_at')
        }),
    )

    def user_count(self, obj):
        return obj.sessions.values('user_name').distinct().count()
    user_count.short_description = 'Users'

    def usage_count(self, obj):
        return obj.sessions.count()
    usage_count.short_description = 'Total Sessions'

    def generate_codes(self, request, queryset):
        """Generate new access codes"""
        if request.method == 'POST':
            count = int(request.POST.get('count', 1))
            subject_id = request.POST.get('subject')

            subject = None
            if subject_id:
                subject = Subject.objects.get(id=subject_id)

            created = 0
            for _ in range(count):
                AccessCode.objects.create(
                    subject=subject,
                    created_by=request.user
                )
                created += 1

            self.message_user(
                request,
                f"{created} access code(s) generated successfully",
                messages.SUCCESS
            )
            return redirect('admin:quiz_accesscode_changelist')

        # Show form
        subjects = Subject.objects.all()
        context = {
            'subjects': subjects,
            'title': 'Generate Access Codes'
        }
        return render(request, 'admin/generate_codes.html', context)

    generate_codes.short_description = "Generate new access codes"

    def deactivate_codes(self, request, queryset):
        """Deactivate selected codes"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} code(s) deactivated",
            messages.SUCCESS
        )

    deactivate_codes.short_description = "Deactivate selected codes"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate/', self.admin_site.admin_view(self.generate_codes), name='generate_codes'),
        ]
        return custom_urls + urls


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'access_code', 'test', 'score', 'correct_answers', 'total_questions', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'test__subject', 'test']
    search_fields = ['user_name', 'access_code__code']
    readonly_fields = ['access_code', 'test', 'user_name', 'started_at', 'completed_at', 'score', 'correct_answers', 'total_questions']

    def has_add_permission(self, request):
        return False


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['get_user_name', 'question_text', 'selected_option', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'session__test']
    search_fields = ['session__user_name']
    readonly_fields = ['session', 'question', 'selected_option', 'is_correct', 'answered_at']

    def get_user_name(self, obj):
        return obj.session.user_name
    get_user_name.short_description = 'User'

    def question_text(self, obj):
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text
    question_text.short_description = 'Question'

    def has_add_permission(self, request):
        return False
