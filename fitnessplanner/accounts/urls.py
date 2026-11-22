
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('select-goal/', views.select_goal, name='select_goal'),
    path('select-muscle-groups/', views.select_muscle_groups, name='select_muscle_groups'),
    path('allergy-assessment/', views.allergy_assessment, name='allergy_assessment'),
    path('review/', views.onboarding_review, name='onboarding_review'),
    path('login/', views.login_view, name='login'),
    path('force-password-change/', views.force_password_change, name='force_password_change'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('progress/', views.progress_list, name='progress'),
    path('progress/<int:pk>/delete/', views.progress_delete, name='progress_delete'),
]
