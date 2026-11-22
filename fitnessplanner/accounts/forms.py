from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile, ProgressEntry

FORM_CONTROL = {'class': 'form-control'}


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=FORM_CONTROL))
    height_cm = forms.IntegerField(
        min_value=50,
        max_value=300,
        required=True,
        label='Height (cm)',
        widget=forms.NumberInput(attrs=FORM_CONTROL),
    )
    weight_kg = forms.FloatField(
        min_value=20,
        max_value=500,
        required=True,
        label='Weight (kg)',
        widget=forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
    )
    age = forms.IntegerField(
        min_value=10,
        max_value=120,
        required=True,
        widget=forms.NumberInput(attrs=FORM_CONTROL),
    )
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs=FORM_CONTROL),
    )
    activity_level = forms.ChoiceField(
        choices=UserProfile.ACTIVITY_LEVEL_CHOICES,
        required=True,
        label='Activity level',
        widget=forms.Select(attrs=FORM_CONTROL),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'password1', 'password2'):
            self.fields[name].widget.attrs.update(FORM_CONTROL)
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username', 'autocomplete': 'username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'name@example.com', 'autocomplete': 'email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Create a secure password', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Re-enter password', 'autocomplete': 'new-password'})
        self.fields['height_cm'].widget.attrs.update({'placeholder': 'e.g. 175', 'min': '50', 'max': '300'})
        self.fields['weight_kg'].widget.attrs.update({'placeholder': 'e.g. 70.0', 'min': '20', 'max': '500'})
        self.fields['age'].widget.attrs.update({'placeholder': 'e.g. 26', 'min': '10', 'max': '120'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.userprofile
            profile.height_cm = self.cleaned_data['height_cm']
            profile.weight_kg = self.cleaned_data['weight_kg']
            profile.age = self.cleaned_data['age']
            profile.gender = self.cleaned_data['gender']
            profile.activity_level = self.cleaned_data['activity_level']
            profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs=FORM_CONTROL),
            'last_name': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
        }


class UserProfileForm(forms.ModelForm):
    allergies = forms.MultipleChoiceField(
        choices=UserProfile.ALLERGY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Food Allergies',
    )
    health_conditions = forms.MultipleChoiceField(
        choices=UserProfile.HEALTH_CONDITION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Health Conditions',
    )

    class Meta:
        model = UserProfile
        fields = (
            'bio',
            'age',
            'gender',
            'fitness_goal',
            'activity_level',
            'height_cm',
            'weight_kg',
            'dietary_preference',
            'allergies',
            'custom_allergies',
            'health_conditions',
        )
        widgets = {
            'bio': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'age': forms.NumberInput(attrs=FORM_CONTROL),
            'gender': forms.Select(attrs=FORM_CONTROL),
            'fitness_goal': forms.Select(attrs=FORM_CONTROL),
            'activity_level': forms.Select(attrs=FORM_CONTROL),
            'height_cm': forms.NumberInput(attrs=FORM_CONTROL),
            'weight_kg': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'dietary_preference': forms.Select(attrs=FORM_CONTROL),
            'custom_allergies': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. sesame, strawberries, avocado'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.allergies:
                self.initial['allergies'] = [a.strip() for a in self.instance.allergies.split(',') if a.strip()]
            if self.instance.health_conditions:
                self.initial['health_conditions'] = [c.strip() for c in self.instance.health_conditions.split(',') if c.strip()]

    def clean_allergies(self):
        return ','.join(self.cleaned_data.get('allergies', []))

    def clean_health_conditions(self):
        return ','.join(self.cleaned_data.get('health_conditions', []))


class ProgressEntryForm(forms.ModelForm):
    class Meta:
        model = ProgressEntry
        fields = ('recorded_at', 'weight_kg', 'notes')
        widgets = {
            'recorded_at': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'weight_kg': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.1'}),
            'notes': forms.TextInput(attrs=FORM_CONTROL),
        }
