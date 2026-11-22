from django.urls import path
from . import views
from . import instructor_views

app_name = 'planner'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/memberships/', views.admin_memberships, name='admin_memberships'),
    path('admin-dashboard/instructors/', views.admin_instructors, name='admin_instructors'),
    path('admin-dashboard/instructors/new/', views.admin_instructor_new, name='admin_instructor_new'),
    path('admin-dashboard/instructors/add/', views.admin_instructor_create, name='admin_instructor_create'),
    path('admin-dashboard/instructors/<int:pk>/edit/', views.admin_instructor_edit, name='admin_instructor_edit'),
    path('admin-dashboard/instructors/<int:pk>/toggle/', views.admin_instructor_toggle, name='admin_instructor_toggle'),
    path('admin-dashboard/instructors/<int:pk>/delete/', views.admin_instructor_delete, name='admin_instructor_delete'),
    path('admin-dashboard/assignments/', views.admin_assignments, name='admin_assignments'),
    path('admin-dashboard/assignments/add/', views.admin_assign_member, name='admin_assign_member'),
    path('admin-dashboard/memberships/<int:pk>/approve/', views.admin_membership_approve, name='admin_membership_approve'),
    path('admin-dashboard/memberships/<int:pk>/reject/', views.admin_membership_reject, name='admin_membership_reject'),

    # Instructor Portal Routes (8 navigation items + detail/action endpoints)
    path('instructor/', instructor_views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/members/', instructor_views.instructor_members, name='instructor_members'),
    path('instructor/members/<int:member_id>/', instructor_views.instructor_member_detail, name='instructor_member_detail'),
    path('instructor/appointments/', instructor_views.instructor_appointments, name='instructor_appointments'),
    path('instructor/appointments/<int:pk>/<str:action>/', instructor_views.instructor_booking_action, name='instructor_booking_action'),
    path('instructor/schedule/', instructor_views.instructor_schedule, name='instructor_schedule'),
    path('instructor/workout-plans/', instructor_views.instructor_workout_plans, name='instructor_workout_plans'),
    path('instructor/workout-plans/<int:pk>/', instructor_views.instructor_workout_plan_detail, name='instructor_workout_plan_detail'),
    path('instructor/assessments/', instructor_views.instructor_assessments, name='instructor_assessments'),
    path('instructor/progress/', instructor_views.instructor_progress, name='instructor_progress'),
    path('instructor/settings/', instructor_views.instructor_profile_settings, name='instructor_profile_settings'),
    path('notifications/read/', instructor_views.notifications_mark_read, name='notifications_mark_read'),

    path('meals/', views.meal_list, name='meal_list'),
    path('meals/add/', views.meal_create, name='meal_create'),
    path('meals/<int:pk>/edit/', views.meal_edit, name='meal_edit'),
    path('meals/<int:pk>/delete/', views.meal_delete, name='meal_delete'),
    path('meals/health-check/', views.meal_health_check, name='meal_health_check'),
    path('meals/<int:pk>/health-check/', views.meal_health_check, name='meal_health_check_detail'),

    path('workouts/', views.workout_list, name='workout_list'),
    path('workouts/add/', views.workout_create, name='workout_create'),
    path('workouts/<int:pk>/edit/', views.workout_edit, name='workout_edit'),
    path('workouts/<int:pk>/delete/', views.workout_delete, name='workout_delete'),

    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/add/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/toggle/', views.schedule_toggle, name='schedule_toggle'),
    path('schedule/quick-add/<int:workout_id>/', views.quick_schedule_workout, name='quick_schedule_workout'),

    path('memberships/', views.membership_list, name='membership_list'),
    path('memberships/subscribe/<int:pk>/', views.membership_subscribe, name='membership_subscribe'),
    path('memberships/cancel/<int:pk>/', views.membership_cancel, name='membership_cancel'),

    path('instructors/', views.instructor_list, name='instructor_list'),
    path('instructors/cancel/<int:pk>/', views.instructor_booking_cancel, name='instructor_booking_cancel'),

    path('suggestions/', views.smart_suggestions, name='smart_suggestions'),
]
