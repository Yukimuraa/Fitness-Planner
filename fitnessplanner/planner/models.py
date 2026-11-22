from django.db import models
from django.conf import settings
from django.utils import timezone


class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='lunch')
    allergens = models.TextField(
        blank=True,
        default='',
        help_text='Comma-separated allergens e.g. nuts, dairy, gluten, eggs, shellfish, soy, fish',
    )
    dietary_tags = models.TextField(
        blank=True,
        default='',
        help_text='Comma-separated tags e.g. vegetarian, vegan, keto, low_sodium, high_protein',
    )
    ingredients = models.TextField(
        blank=True,
        default='',
        help_text='Comma-separated list of verified meal ingredients',
    )
    cross_contact_notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional cross-contact or facility allergen notes',
    )
    ingredients_verified = models.BooleanField(
        default=False,
        help_text='True only when all ingredients and cross-contact details are known',
    )
    calories = models.PositiveIntegerField(default=0)
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)

    def get_allergens_list(self):
        if self.allergens:
            return [a.strip().lower() for a in self.allergens.split(',') if a.strip()]
        return []

    def get_dietary_tags_list(self):
        if self.dietary_tags:
            return [t.strip().lower() for t in self.dietary_tags.split(',') if t.strip()]
        return []

    @property
    def total_calories(self):
        item_total = sum(i.calories for i in self.items.all())
        return item_total if item_total > 0 else self.calories

    @property
    def total_protein(self):
        item_total = sum(i.protein_g for i in self.items.all())
        return round(item_total if item_total > 0 else self.protein_g, 1)

    @property
    def total_carbs(self):
        item_total = sum(i.carbs_g for i in self.items.all())
        return round(item_total if item_total > 0 else self.carbs_g, 1)

    @property
    def total_fat(self):
        item_total = sum(i.fat_g for i in self.items.all())
        return round(item_total if item_total > 0 else self.fat_g, 1)

    def __str__(self):
        return self.name


class MealItem(models.Model):
    meal = models.ForeignKey(Meal, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    calories = models.PositiveIntegerField(default=0)
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} ({self.calories} kcal)"


class Workout(models.Model):
    MUSCLE_GROUP_CHOICES = [
        ('full_body', 'Full Body'),
        ('chest', 'Chest (Push)'),
        ('back', 'Back (Pull)'),
        ('legs', 'Legs & Glutes'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms (Biceps & Triceps)'),
        ('core', 'Abs / Core'),
        ('cardio', 'Cardio & Endurance'),
    ]
    WORKOUT_TYPE_CHOICES = [
        ('strength', 'Strength Training'),
        ('cardio', 'Cardio'),
        ('hiit', 'HIIT'),
        ('flexibility', 'Flexibility & Mobility'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_min = models.PositiveIntegerField(default=30)
    muscle_group = models.CharField(max_length=30, choices=MUSCLE_GROUP_CHOICES, default='full_body')
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES, default='strength')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    calories_burned_est = models.PositiveIntegerField(default=250)

    def __str__(self):
        return self.name


class WorkoutSchedule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.workout} on {self.date}"


class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    daily_calorie_goal = models.PositiveIntegerField(null=True, blank=True)
    preferred_workout_time = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Prefs for {self.user}"


class MembershipPackage(models.Model):
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
        ('bundle', 'Bundle Package'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='pro')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)
    features = models.TextField(help_text='Newline-separated list of package features')
    included_instructor_sessions = models.PositiveIntegerField(default=0)
    includes_meal_coaching = models.BooleanField(default=False)
    includes_ai_suggestions = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']

    def get_features_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    @property
    def price_display(self):
        return f"₱{self.price:,.0f}"

    def __str__(self):
        return f"{self.name} (₱{self.price:,.0f}/{self.duration_days}d)"


class UserMembership(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    package = models.ForeignKey(MembershipPackage, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_required')
    amount_php = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=120, blank=True, default='')
    admin_notes = models.CharField(max_length=255, blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    sessions_remaining = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def amount_display(self):
        return f"₱{self.amount_php:,.0f}"

    @property
    def days_remaining(self):
        if self.status != 'active':
            return 0
        delta = (self.end_date - timezone.now().date()).days
        return max(0, delta)

    def __str__(self):
        return f"{self.user.username} - {self.package.name} ({self.status})"


class Instructor(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    SPECIALIZATION_CHOICES = [
        ('Weight Loss', 'Weight Loss'),
        ('Muscle Building', 'Muscle Building'),
        ('Strength Training', 'Strength Training'),
        ('Personal Training', 'Personal Training'),
        ('Nutrition Coaching', 'Nutrition Coaching'),
        ('HIIT & Conditioning', 'HIIT & Conditioning'),
        ('Yoga & Mobility', 'Yoga & Mobility'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instructor_profile',
    )
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default='')
    contact_number = models.CharField(max_length=30, blank=True, default='')
    profile_photo = models.ImageField(upload_to='instructors/', null=True, blank=True)
    specialty = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=3)
    certification = models.CharField(max_length=150, blank=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2, default=45.00)
    rating = models.FloatField(default=4.8)
    available_days = models.CharField(max_length=120, default='Mon, Wed, Fri')
    avatar_emoji = models.CharField(max_length=10, default='🏋️')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        self.is_active = (self.status == 'active')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.specialty})"


class InstructorAssignment(models.Model):
    """Links an assigned Member to an Instructor (managed by Admin)."""
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='assignments')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_assignments',
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assignments',
    )
    notes = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.member.username} -> {self.instructor.name}"


class InstructorAvailability(models.Model):
    """Customizable weekly availability slots for an Instructor."""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    DEFAULT_SLOTS = [
        ('07:00', '08:00', '07:00 AM - 08:00 AM'),
        ('08:00', '09:00', '08:00 AM - 09:00 AM'),
        ('09:00', '10:00', '09:00 AM - 10:00 AM'),
        ('12:00', '13:00', '12:00 PM - 01:00 PM'),
        ('14:00', '15:00', '02:00 PM - 03:00 PM'),
        ('15:00', '16:00', '03:00 PM - 04:00 PM'),
        ('17:00', '18:00', '05:00 PM - 06:00 PM'),
        ('18:00', '19:00', '06:00 PM - 07:00 PM'),
        ('19:00', '20:00', '07:00 PM - 08:00 PM'),
    ]

    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    time_slot_label = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.instructor.name} — {self.get_day_of_week_display()} {self.time_slot_label}"


class InstructorUnavailableDate(models.Model):
    """Specific unavailable dates or blocked time ranges for an Instructor."""
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='unavailable_dates')
    date = models.DateField()
    is_full_day = models.BooleanField(default=True)
    blocked_time_slot = models.CharField(max_length=50, blank=True, default='')
    reason = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.instructor.name} unavailable {self.date}"


class InstructorBooking(models.Model):
    TIME_SLOT_CHOICES = [
        ('07:00 AM - 08:00 AM', '07:00 AM – 08:00 AM'),
        ('08:00 AM - 09:00 AM', '08:00 AM – 09:00 AM'),
        ('09:00 AM - 10:00 AM', '09:00 AM – 10:00 AM'),
        ('12:00 PM - 01:00 PM', '12:00 PM – 01:00 PM'),
        ('02:00 PM - 03:00 PM', '02:00 PM – 03:00 PM'),
        ('03:00 PM - 04:00 PM', '03:00 PM – 04:00 PM'),
        ('05:00 PM - 06:00 PM', '05:00 PM – 06:00 PM'),
        ('06:00 PM - 07:00 PM', '06:00 PM – 07:00 PM'),
        ('07:00 PM - 08:00 PM', '07:00 PM – 08:00 PM'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('reschedule_requested', 'Reschedule Requested'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='instructor_bookings')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='bookings')
    membership = models.ForeignKey(
        UserMembership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
    )
    session_date = models.DateField()
    time_slot = models.CharField(max_length=50, default='09:00 AM - 10:00 AM')
    focus_area = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    used_package_session = models.BooleanField(default=False)
    credit_reserved = models.BooleanField(default=False)
    credit_deducted = models.BooleanField(default=False)
    suggested_date = models.DateField(null=True, blank=True)
    suggested_time_slot = models.CharField(max_length=50, blank=True, default='')
    instructor_response_note = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session_date', 'time_slot']

    def __str__(self):
        return f"{self.user.username} with {self.instructor.name} on {self.session_date}"


class SessionCreditTransaction(models.Model):
    """Audit trail for every coaching session credit reservation, release, or completion deduction."""
    ACTION_CHOICES = [
        ('reserve', 'Credit Reserved (Booking Confirmed)'),
        ('release', 'Credit Released (Cancelled / Rejected)'),
        ('deduct', 'Credit Deducted (Session Completed)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credit_transactions')
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='credit_transactions')
    booking = models.ForeignKey(
        InstructorBooking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    credits_delta = models.IntegerField(default=0)
    balance_after = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.action} ({self.credits_delta})"


class WorkoutPlan(models.Model):
    """Instructor-created workout plan assigned to a specific member (separate from AI recommendations)."""
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='workout_plans')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_workout_plans')
    title = models.CharField(max_length=150)
    fitness_goal = models.CharField(max_length=100, blank=True, default='')
    target_muscle_groups = models.CharField(max_length=200, blank=True, default='')
    frequency_per_week = models.PositiveSmallIntegerField(default=3)
    notes = models.TextField(blank=True, default='')
    recommendations = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.member.username})"


class WorkoutPlanExercise(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise_name = models.CharField(max_length=150)
    sets = models.PositiveSmallIntegerField(default=3)
    reps = models.CharField(max_length=40, default='10-12')
    duration_min = models.PositiveSmallIntegerField(default=0)
    rest_seconds = models.PositiveSmallIntegerField(default=60)
    instructions = models.TextField(blank=True, default='')
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.exercise_name} ({self.sets}x{self.reps})"


class FitnessAssessment(models.Model):
    """Fitness screening & training observations recorded by an Instructor for an assigned member."""
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='assessments')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fitness_assessments')
    assessed_at = models.DateField(default=timezone.now)
    weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    chest_cm = models.FloatField(null=True, blank=True)
    waist_cm = models.FloatField(null=True, blank=True)
    hips_cm = models.FloatField(null=True, blank=True)
    arms_cm = models.FloatField(null=True, blank=True)
    thighs_cm = models.FloatField(null=True, blank=True)
    fitness_goals = models.CharField(max_length=200, blank=True, default='')
    strength_observations = models.TextField(blank=True, default='')
    endurance_observations = models.TextField(blank=True, default='')
    muscle_group_performance = models.TextField(blank=True, default='')
    mobility_observations = models.TextField(blank=True, default='')
    assessment_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at', '-created_at']

    def save(self, *args, **kwargs):
        if self.weight_kg and self.height_cm:
            h_m = self.height_cm / 100.0
            self.bmi = round(self.weight_kg / (h_m * h_m), 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.username} assessment on {self.assessed_at}"


class InstructorNote(models.Model):
    """Coaching notes, progress feedback, and recommendations for an assigned member."""
    NOTE_TYPE_CHOICES = [
        ('coaching', 'Coaching Note'),
        ('progress', 'Progress Feedback'),
        ('recommendation', 'Recommendation'),
    ]

    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='member_notes')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='instructor_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='coaching')
    title = models.CharField(max_length=150)
    content = models.TextField()
    visible_to_member = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.member.username})"


class Notification(models.Model):
    """In-app notifications for members, instructors, and admins."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=40, default='booking')
    link_url = models.CharField(max_length=200, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
