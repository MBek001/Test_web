from django.urls import path
from . import views

urlpatterns = [
    # User routes
    path('', views.login_view, name='login'),
    path('tests/', views.test_list, name='test_list'),
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('test/take/', views.take_test, name='take_test'),
    path('test/results/<int:session_id>/', views.test_results, name='test_results'),
    path('logout/', views.logout_view, name='logout'),

    # Admin routes
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # Subjects
    path('admin-panel/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin-panel/subjects/create/', views.admin_subject_create, name='admin_subject_create'),
    path('admin-panel/subjects/<int:subject_id>/', views.admin_subject_detail, name='admin_subject_detail'),

    # Tests
    path('admin-panel/subjects/<int:subject_id>/test/create/', views.admin_test_create, name='admin_test_create'),
    path('admin-panel/test/<int:test_id>/', views.admin_test_detail, name='admin_test_detail'),

    # Access codes
    path('admin-panel/codes/', views.admin_codes, name='admin_codes'),

    # Results
    path('admin-panel/results/', views.admin_results, name='admin_results'),
    path('admin-panel/session/<int:session_id>/', views.admin_session_detail, name='admin_session_detail'),
]
