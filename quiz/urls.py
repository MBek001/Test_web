from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('subjects/', views.subject_selection, name='subject_selection'),
    path('subject/<int:subject_id>/tests/', views.test_selection, name='test_selection'),
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('test/take/', views.take_test, name='take_test'),
    path('test/results/<int:session_id>/', views.test_results, name='test_results'),
    path('logout/', views.logout_view, name='logout'),
]
