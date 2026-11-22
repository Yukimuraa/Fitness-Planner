from django.contrib import admin
from .models import (
    Meal,
    MealItem,
    Workout,
    WorkoutSchedule,
    UserPreference,
    MembershipPackage,
    UserMembership,
    Instructor,
    InstructorBooking,
    InstructorAssignment,
    InstructorAvailability,
    InstructorUnavailableDate,
    SessionCreditTransaction,
    WorkoutPlan,
    WorkoutPlanExercise,
    FitnessAssessment,
    InstructorNote,
    Notification,
)


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'calories', 'allergens')
    list_filter = ('meal_type',)


@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal', 'calories')


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'muscle_group', 'workout_type', 'difficulty', 'duration_min')
    list_filter = ('muscle_group', 'workout_type', 'difficulty')


@admin.register(WorkoutSchedule)
class WorkoutScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'workout', 'date', 'completed')
    list_filter = ('completed', 'date')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_calorie_goal', 'preferred_workout_time')


@admin.register(MembershipPackage)
class MembershipPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'price', 'duration_days', 'included_instructor_sessions', 'is_popular', 'is_active')
    list_filter = ('tier', 'is_active')


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'amount_php', 'payment_status', 'status', 'start_date', 'end_date', 'sessions_remaining')
    list_filter = ('status', 'payment_status', 'package')


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'experience_years', 'hourly_rate', 'rating', 'is_active')
    list_filter = ('is_active',)


@admin.register(InstructorBooking)
class InstructorBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'instructor', 'session_date', 'time_slot', 'status', 'credit_reserved', 'credit_deducted')
    list_filter = ('status', 'session_date')


admin.site.register(InstructorAssignment)
admin.site.register(InstructorAvailability)
admin.site.register(InstructorUnavailableDate)
admin.site.register(SessionCreditTransaction)
admin.site.register(WorkoutPlan)
admin.site.register(WorkoutPlanExercise)
admin.site.register(FitnessAssessment)
admin.site.register(InstructorNote)
admin.site.register(Notification)
