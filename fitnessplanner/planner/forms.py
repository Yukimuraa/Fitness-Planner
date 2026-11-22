from datetime import date
from django import forms
from .models import (
    Meal,
    MealItem,
    Workout,
    WorkoutSchedule,
    Instructor,
    InstructorBooking,
    WorkoutPlan,
    WorkoutPlanExercise,
    FitnessAssessment,
    InstructorNote,
)

FORM_CONTROL = {'class': 'form-control'}


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = (
            'name',
            'meal_type',
            'description',
            'allergens',
            'dietary_tags',
            'calories',
            'protein_g',
            'carbs_g',
            'fat_g',
        )
        widgets = {
            'name': forms.TextInput(attrs=FORM_CONTROL),
            'meal_type': forms.Select(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'allergens': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. nuts, dairy, gluten, eggs, soy'}),
            'dietary_tags': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. vegetarian, high_protein, low_sodium'}),
            'calories': forms.NumberInput(attrs=FORM_CONTROL),
            'protein_g': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'carbs_g': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'fat_g': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
        }


class MealItemForm(forms.ModelForm):
    class Meta:
        model = MealItem
        fields = ('meal', 'name', 'calories', 'protein_g', 'carbs_g', 'fat_g')


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = (
            'name',
            'description',
            'duration_min',
            'muscle_group',
            'workout_type',
            'difficulty',
            'calories_burned_est',
        )
        widgets = {
            'name': forms.TextInput(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'duration_min': forms.NumberInput(attrs=FORM_CONTROL),
            'muscle_group': forms.Select(attrs=FORM_CONTROL),
            'workout_type': forms.Select(attrs=FORM_CONTROL),
            'difficulty': forms.Select(attrs=FORM_CONTROL),
            'calories_burned_est': forms.NumberInput(attrs=FORM_CONTROL),
        }


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkoutSchedule
        fields = ('workout', 'date')
        widgets = {
            'workout': forms.Select(attrs=FORM_CONTROL),
            'date': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['workout'].empty_label = '— Select a workout —'
        self.fields['workout'].queryset = Workout.objects.order_by('name')
        self.fields['workout'].label = 'Workout'


class InstructorBookingForm(forms.ModelForm):
    time_slot = forms.CharField(
        max_length=50,
        widget=forms.Select(attrs=FORM_CONTROL, choices=InstructorBooking.TIME_SLOT_CHOICES),
        label='Time Slot',
    )

    class Meta:
        model = InstructorBooking
        fields = ('instructor', 'session_date', 'time_slot', 'focus_area', 'notes')
        widgets = {
            'instructor': forms.Select(attrs=FORM_CONTROL),
            'session_date': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date', 'min': date.today().isoformat()}),
            'focus_area': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. Muscle imbalance fix, Form check, Fat loss'}),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2, 'placeholder': 'Any injuries, goals, or preferences for your coach...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = Instructor.objects.filter(status='active').order_by('name')
        self.fields['instructor'].empty_label = '— Choose an instructor —'


class InstructorForm(forms.ModelForm):
    username = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Auto-generated if blank'}),
        label='Login Username',
    )
    temporary_password = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Auto-generated if blank'}),
        label='Temporary Password',
    )

    class Meta:
        model = Instructor
        fields = (
            'name',
            'email',
            'contact_number',
            'profile_photo',
            'specialty',
            'experience_years',
            'certification',
            'hourly_rate',
            'available_days',
            'avatar_emoji',
            'status',
            'bio',
        )
        widgets = {
            'name': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={**FORM_CONTROL, 'placeholder': 'instructor@fitlife.com'}),
            'contact_number': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': '+63 9XX XXX XXXX'}),
            'profile_photo': forms.ClearableFileInput(attrs=FORM_CONTROL),
            'specialty': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Weight Loss, Strength Training, etc.'}),
            'experience_years': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 0}),
            'certification': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. NASM-CPT, CSCS'}),
            'hourly_rate': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'min': 0}),
            'available_days': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. Mon, Wed, Fri'}),
            'avatar_emoji': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': '🏋️'}),
            'status': forms.Select(attrs=FORM_CONTROL),
            'bio': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2, 'placeholder': 'Instructor biography...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for opt_field in ('hourly_rate', 'avatar_emoji', 'available_days', 'status', 'experience_years'):
            if opt_field in self.fields:
                self.fields[opt_field].required = False

    def clean_status(self):
        return self.cleaned_data.get('status') or 'active'

    def clean_hourly_rate(self):
        val = self.cleaned_data.get('hourly_rate')
        return val if val is not None else 45.00

    def clean_avatar_emoji(self):
        return self.cleaned_data.get('avatar_emoji') or '🏋️'

    def clean_available_days(self):
        return self.cleaned_data.get('available_days') or 'Mon, Wed, Fri'

    def clean_experience_years(self):
        val = self.cleaned_data.get('experience_years')
        return val if val is not None else 3


class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = (
            'name',
            'email',
            'contact_number',
            'profile_photo',
            'specialty',
            'certification',
            'experience_years',
            'available_days',
            'bio',
        )
        widgets = {
            'name': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'contact_number': forms.TextInput(attrs=FORM_CONTROL),
            'profile_photo': forms.ClearableFileInput(attrs=FORM_CONTROL),
            'specialty': forms.TextInput(attrs=FORM_CONTROL),
            'certification': forms.TextInput(attrs=FORM_CONTROL),
            'experience_years': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 0}),
            'available_days': forms.TextInput(attrs=FORM_CONTROL),
            'bio': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
        }


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ('member', 'title', 'fitness_goal', 'target_muscle_groups', 'frequency_per_week', 'notes', 'recommendations')
        widgets = {
            'member': forms.Select(attrs=FORM_CONTROL),
            'title': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. 4-Week Upper/Lower Strength Plan'}),
            'fitness_goal': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. Build Muscle / Lose Weight'}),
            'target_muscle_groups': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. Chest, Back, Legs, Core'}),
            'frequency_per_week': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'max': 7}),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'recommendations': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }


class FitnessAssessmentForm(forms.ModelForm):
    class Meta:
        model = FitnessAssessment
        fields = (
            'member',
            'assessed_at',
            'weight_kg',
            'height_cm',
            'chest_cm',
            'waist_cm',
            'hips_cm',
            'arms_cm',
            'thighs_cm',
            'fitness_goals',
            'strength_observations',
            'endurance_observations',
            'muscle_group_performance',
            'mobility_observations',
            'assessment_notes',
        )
        widgets = {
            'member': forms.Select(attrs=FORM_CONTROL),
            'assessed_at': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'weight_kg': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'height_cm': forms.NumberInput(attrs=FORM_CONTROL),
            'chest_cm': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'waist_cm': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'hips_cm': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'arms_cm': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'thighs_cm': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'fitness_goals': forms.TextInput(attrs=FORM_CONTROL),
            'strength_observations': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'endurance_observations': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'muscle_group_performance': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'mobility_observations': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'assessment_notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }


class InstructorNoteForm(forms.ModelForm):
    class Meta:
        model = InstructorNote
        fields = ('note_type', 'title', 'content', 'visible_to_member')
        widgets = {
            'note_type': forms.Select(attrs=FORM_CONTROL),
            'title': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Note title'}),
            'content': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3, 'placeholder': 'Coaching feedback or recommendation...'}),
        }
