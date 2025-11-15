from django.urls import path
from . import views

urlpatterns = [
    # User routes
    path('', views.login_view, name='login'),
    path('tests/', views.test_list, name='test_list'),
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('test/take/', views.take_test, name='take_test'),
    path('test/results/<int:session_id>/', views.test_results, name='test_results'),
    path('my-statistics/', views.my_statistics, name='my_statistics'),
    path('practice/', views.practice_mode, name='practice_mode'),
    path('logout/', views.logout_view, name='logout'),

    # Admin routes - /admin redirects here
    path('admin/', views.admin_dashboard, name='admin_dashboard'),  # Main admin entry point
    path('admin/register/', views.admin_register, name='admin_register'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),

    # Subjects
    path('admin/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin/subjects/create/', views.admin_subject_create, name='admin_subject_create'),
    path('admin/subjects/<int:subject_id>/', views.admin_subject_detail, name='admin_subject_detail'),

    # Tests
    path('admin/subjects/<int:subject_id>/test/create/', views.admin_test_create, name='admin_test_create'),
    path('admin/test/<int:test_id>/', views.admin_test_detail, name='admin_test_detail'),

    # Access codes
    path('admin/codes/', views.admin_codes, name='admin_codes'),

    # Results
    path('admin/results/', views.admin_results, name='admin_results'),
    path('admin/session/<int:session_id>/', views.admin_session_detail, name='admin_session_detail'),

    # Users
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<str:user_name>/<str:access_code>/', views.admin_user_detail, name='admin_user_detail'),
]
