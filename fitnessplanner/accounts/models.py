from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    FITNESS_GOAL_CHOICES = [
        ('', 'Not Selected'),
        ('lose_weight', 'Lose Weight'),
        ('build_muscle', 'Build Muscle'),
        ('maintain_weight', 'Maintain Weight'),
        ('improve_fitness', 'Improve Fitness'),
    ]
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Light (1–3 days/week)'),
        ('moderate', 'Moderate (3–5 days/week)'),
        ('active', 'Active (6–7 days/week)'),
        ('very_active', 'Very active (athlete / physical job)'),
    ]
    ALLERGY_CHOICES = [
        ('nuts', 'Peanuts & Tree Nuts'),
        ('dairy', 'Dairy / Milk'),
        ('gluten', 'Gluten / Wheat'),
        ('eggs', 'Eggs'),
        ('shellfish', 'Shellfish'),
        ('soy', 'Soy'),
        ('fish', 'Fish'),
    ]
    DIETARY_PREFERENCE_CHOICES = [
        ('none', 'No Restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto / Low-Carb'),
        ('halal', 'Halal'),
        ('low_sodium', 'Low Sodium'),
        ('diabetic_friendly', 'Diabetic Friendly'),
    ]
    HEALTH_CONDITION_CHOICES = [
        ('hypertension', 'High Blood Pressure (Hypertension)'),
        ('diabetes', 'Diabetes / Blood Sugar Management'),
        ('high_cholesterol', 'High Cholesterol'),
        ('lactose_intolerant', 'Lactose Intolerance'),
        ('celiac', 'Celiac / Gluten Sensitivity'),
        ('joint_pain', 'Joint / Knee Sensitivity'),
    ]

    ROLE_CHOICES = [
        ('member', 'Member'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    must_change_password = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    fitness_goal = models.CharField(max_length=30, choices=FITNESS_GOAL_CHOICES, blank=True)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    focused_muscles = models.TextField(blank=True, default='')
    allergies = models.TextField(blank=True, default='')
    custom_allergies = models.CharField(max_length=255, blank=True, default='')
    dietary_preference = models.CharField(
        max_length=30,
        choices=DIETARY_PREFERENCE_CHOICES,
        default='none',
        blank=True,
    )
    health_conditions = models.TextField(blank=True, default='')

    MUSCLE_GROUPS = {
        'arms': {
            'name': 'Arms',
            'subtitle': 'Biceps & Triceps',
            'desc': 'Build stronger biceps and triceps for bigger and more defined arms.',
            'image': 'arms_muscle_1780878009010.png',
        },
        'chest': {
            'name': 'Chest',
            'subtitle': 'Pectorals',
            'desc': 'Develop chest size, strength, and upper body power.',
            'image': 'chest_muscle_1780878065929.png',
        },
        'back': {
            'name': 'Back',
            'subtitle': 'Lats & Traps',
            'desc': 'Improve posture and build a wider, stronger back.',
            'image': 'back_muscle_1780878079161.png',
        },
        'shoulders': {
            'name': 'Shoulders',
            'subtitle': 'Deltoids',
            'desc': 'Increase shoulder size and create a broader physique.',
            'image': 'shoulders_muscle_1780878092117.png',
        },
        'core': {
            'name': 'Abs/Core',
            'subtitle': 'Abdominals',
            'desc': 'Strengthen your core and improve abdominal definition.',
            'image': 'core_muscle_1780878105617.png',
        },
        'legs': {
            'name': 'Legs',
            'subtitle': 'Quads & Hamstrings',
            'desc': 'Build stronger quads, hamstrings, and overall leg strength.',
            'image': 'legs_muscle_1780878122120.png',
        },
        'glutes': {
            'name': 'Glutes',
            'subtitle': 'Gluteus Maximus',
            'desc': 'Develop stronger and more powerful glute muscles.',
            'image': 'legs_muscle_1780878122120.png',
        },
        'calves': {
            'name': 'Calves',
            'subtitle': 'Gastrocnemius',
            'desc': 'Increase lower leg strength and muscle development.',
            'image': 'legs_muscle_1780878122120.png',
        },
    }

    def get_focused_muscles_list(self):
        if self.focused_muscles:
            return [m.strip() for m in self.focused_muscles.split(',') if m.strip()]
        return []

    def get_focused_muscles_display(self):
        slugs = self.get_focused_muscles_list()
        result = []
        for slug in slugs:
            if slug in self.MUSCLE_GROUPS:
                result.append(self.MUSCLE_GROUPS[slug])
        return result

    def bmi(self):
        if self.height_cm and self.weight_kg:
            h_m = self.height_cm / 100
            return round(self.weight_kg / (h_m * h_m), 1)
        return None

    def bmi_category(self):
        val = self.bmi()
        if val is None:
            return "—"
        if val < 18.5:
            return 'Underweight'
        elif val < 25.0:
            return 'Normal Weight'
        elif val < 30.0:
            return 'Overweight'
        else:
            return 'Obese'

    def daily_calorie_recommendation(self):
        if not (self.height_cm and self.weight_kg and self.age and self.gender and self.activity_level):
            return None
        
        weight = float(self.weight_kg)
        height = float(self.height_cm)
        age = int(self.age)
        
        if self.gender == 'male':
            bmr = 10.0 * weight + 6.25 * height - 5.0 * age + 5.0
        elif self.gender == 'female':
            bmr = 10.0 * weight + 6.25 * height - 5.0 * age - 161.0
        else:
            bmr = 10.0 * weight + 6.25 * height - 5.0 * age - 78.0
            
        activity_factors = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        
        factor = activity_factors.get(self.activity_level, 1.2)
        tdee = bmr * factor
        
        if self.fitness_goal == 'lose_weight':
            calories = tdee - 500
            if calories < 1200:
                calories = 1200
        elif self.fitness_goal == 'build_muscle':
            calories = tdee + 300
        else:
            calories = tdee
            
        return int(round(calories))

    def water_recommendation_liters(self):
        if not self.weight_kg:
            return None
        
        base_liters = float(self.weight_kg) * 0.033
        
        activity_adjustments = {
            'sedentary': 0.0,
            'light': 0.3,
            'moderate': 0.5,
            'active': 0.7,
            'very_active': 1.0,
        }
        adjust = activity_adjustments.get(self.activity_level, 0.0)
        
        goal_adjust = 0.0
        if self.fitness_goal in ['lose_weight', 'build_muscle']:
            goal_adjust = 0.3
            
        total_liters = base_liters + adjust + goal_adjust
        return round(total_liters, 1)

    def water_recommendation_glasses(self):
        liters = self.water_recommendation_liters()
        if liters is None:
            return None
        return int(round(liters / 0.25))

    def get_gender_display_short(self):
        return self.get_gender_display() if self.gender else '—'

    def get_fitness_goal_display_short(self):
        return self.get_fitness_goal_display() if self.fitness_goal else '—'

    def get_activity_level_display_short(self):
        return self.get_activity_level_display() if self.activity_level else '—'

    def get_allergies_list(self):
        items = [a.strip().lower() for a in self.allergies.split(',') if a.strip()] if self.allergies else []
        if self.custom_allergies:
            items.extend([a.strip().lower() for a in self.custom_allergies.split(',') if a.strip()])
        return list(dict.fromkeys(items))

    def get_allergies_display_list(self):
        label_map = dict(self.ALLERGY_CHOICES)
        result = []
        if self.allergies:
            for slug in self.allergies.split(','):
                s = slug.strip().lower()
                if s:
                    result.append(label_map.get(s, s.title()))
        if self.custom_allergies:
            for item in self.custom_allergies.split(','):
                if item.strip():
                    result.append(item.strip())
        return result

    def get_health_conditions_list(self):
        if self.health_conditions:
            return [c.strip().lower() for c in self.health_conditions.split(',') if c.strip()]
        return []

    def get_health_conditions_display_list(self):
        label_map = dict(self.HEALTH_CONDITION_CHOICES)
        return [label_map.get(c, c.replace('_', ' ').title()) for c in self.get_health_conditions_list()]

    def is_admin_role(self):
        return self.user.is_staff or self.user.is_superuser or self.role == 'admin'

    def is_instructor_role(self):
        return self.role == 'instructor' or hasattr(self.user, 'instructor_profile')

    def __str__(self):
        return f"{self.user.username} profile"


class ProgressEntry(models.Model):
    """User-logged fitness progress (weight, notes) over time."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress_entries',
    )
    recorded_at = models.DateField()
    weight_kg = models.FloatField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at', '-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.recorded_at}"


class Allergen(models.Model):
    """Normalized lookup table of standard food allergens."""
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class MemberAllergy(models.Model):
    """Member-specific food allergy record with optional custom name and severity/reaction notes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='member_allergies',
    )
    allergen = models.ForeignKey(Allergen, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=120, blank=True, default='')
    severity_notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['allergen__display_order', 'allergen__name']

    def label(self):
        if self.allergen.slug == 'other' and self.custom_name:
            return self.custom_name
        return self.allergen.name

    def __str__(self):
        return f"{self.user.username} — {self.label()}"


class FoodIntolerance(models.Model):
    """Normalized lookup table of food intolerances (kept separate from allergies)."""
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class MemberIntolerance(models.Model):
    """Member-specific food intolerance record."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='member_intolerances',
    )
    intolerance = models.ForeignKey(FoodIntolerance, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=120, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['intolerance__display_order', 'intolerance__name']

    def label(self):
        if self.intolerance.slug == 'other' and self.custom_name:
            return self.custom_name
        return self.intolerance.name

    def __str__(self):
        return f"{self.user.username} — {self.label()}"


class DietaryPreferenceOption(models.Model):
    """Normalized lookup table of dietary preferences."""
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class MemberDietaryProfile(models.Model):
    """Stores a member's dietary preferences, restrictions, and onboarding completion state."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dietary_profile',
    )
    no_known_allergies = models.BooleanField(default=False)
    no_known_intolerances = models.BooleanField(default=False)
    dietary_preferences = models.ManyToManyField(DietaryPreferenceOption, blank=True)
    other_restrictions = models.TextField(blank=True, default='')
    assessment_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} dietary profile"
