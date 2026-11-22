from django.contrib import admin
from .models import (
    UserProfile,
    ProgressEntry,
    Allergen,
    MemberAllergy,
    FoodIntolerance,
    MemberIntolerance,
    DietaryPreferenceOption,
    MemberDietaryProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'age',
        'gender',
        'fitness_goal',
        'activity_level',
        'height_cm',
        'weight_kg',
    )
    list_filter = ('fitness_goal', 'gender', 'activity_level')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user',)


@admin.register(ProgressEntry)
class ProgressEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recorded_at', 'weight_kg', 'notes', 'created_at')
    list_filter = ('recorded_at',)
    search_fields = ('user__username',)


admin.site.register(Allergen)
admin.site.register(MemberAllergy)
admin.site.register(FoodIntolerance)
admin.site.register(MemberIntolerance)
admin.site.register(DietaryPreferenceOption)
admin.site.register(MemberDietaryProfile)
