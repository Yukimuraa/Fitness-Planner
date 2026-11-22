from django.db import migrations


def seed_initial_data(apps, schema_editor):
    MembershipPackage = apps.get_model('planner', 'MembershipPackage')
    Instructor = apps.get_model('planner', 'Instructor')
    Workout = apps.get_model('planner', 'Workout')
    Meal = apps.get_model('planner', 'Meal')

    # 1. Membership Packages
    packages = [
        {
            'slug': 'starter-basic',
            'name': 'Starter Basic',
            'tier': 'basic',
            'price': '0.00',
            'duration_days': 30,
            'description': 'Essential workout and meal tracking to kickstart your fitness journey.',
            'features': (
                'Personal Fitness Dashboard\n'
                'Workout & Meal Library Access\n'
                'Basic BMI & Calorie Calculator\n'
                'Allergy & Health Meal Checker'
            ),
            'included_instructor_sessions': 0,
            'includes_meal_coaching': False,
            'includes_ai_suggestions': True,
            'is_popular': False,
        },
        {
            'slug': 'pro-fitness',
            'name': 'Pro Fitness',
            'tier': 'pro',
            'price': '29.99',
            'duration_days': 30,
            'description': 'Smart imbalance detection, tailored workout plans, and 2 monthly coaching sessions.',
            'features': (
                'Everything in Starter Basic\n'
                '2 Instructor Coaching Sessions / month\n'
                'Workout Imbalance & Posture Alerts\n'
                'Personalized Meal & Macro Scaling\n'
                'Priority Schedule Recommendations'
            ),
            'included_instructor_sessions': 2,
            'includes_meal_coaching': True,
            'includes_ai_suggestions': True,
            'is_popular': True,
        },
        {
            'slug': 'elite-transformation',
            'name': 'Elite Transformation',
            'tier': 'elite',
            'price': '59.99',
            'duration_days': 30,
            'description': 'Full-service personal coaching, unlimited health-tailored meal plans, and 6 sessions.',
            'features': (
                'Everything in Pro Fitness\n'
                '6 Instructor Coaching Sessions / month\n'
                '1-on-1 Nutrition & Allergy Coaching\n'
                'Weekly Muscle Balance Audits\n'
                'Custom Recovery & Mobility Programming'
            ),
            'included_instructor_sessions': 6,
            'includes_meal_coaching': True,
            'includes_ai_suggestions': True,
            'is_popular': False,
        },
        {
            'slug': '90-day-bundle-package',
            'name': '90-Day Body & Meal Bundle',
            'tier': 'bundle',
            'price': '149.00',
            'duration_days': 90,
            'description': 'Complete 3-month transformation package combining coaching, meal planning, and smart diagnostics.',
            'features': (
                '90 Days Full Elite Access\n'
                '12 Instructor Sessions Included\n'
                'Custom Allergy-Safe Meal Blueprint\n'
                'Bi-Weekly Body Composition & Imbalance Review\n'
                'Save 17% vs Monthly Elite'
            ),
            'included_instructor_sessions': 12,
            'includes_meal_coaching': True,
            'includes_ai_suggestions': True,
            'is_popular': False,
        },
    ]
    for pkg in packages:
        MembershipPackage.objects.get_or_create(slug=pkg['slug'], defaults=pkg)

    # 2. Instructors
    instructors = [
        {
            'name': 'Coach Marcus Vance',
            'specialty': 'Strength & Hypertrophy',
            'bio': 'Former competitive powerlifter specializing in progressive overload, muscle symmetry, and injury-free compound lifting.',
            'experience_years': 8,
            'certification': 'NSCA-CSCS, USAW Level 2',
            'hourly_rate': '55.00',
            'rating': 4.9,
            'available_days': 'Mon, Tue, Thu, Sat',
            'avatar_emoji': '🏋️',
        },
        {
            'name': 'Coach Elena Rostova',
            'specialty': 'HIIT & Fat Loss',
            'bio': 'High-energy conditioning specialist helping clients burn fat, boost VO2 max, and build sustainable cardio habits.',
            'experience_years': 6,
            'certification': 'ACE Certified Personal Trainer, Precision Nutrition L1',
            'hourly_rate': '48.00',
            'rating': 4.8,
            'available_days': 'Mon, Wed, Fri, Sun',
            'avatar_emoji': '⚡',
        },
        {
            'name': 'Coach Maya Lin',
            'specialty': 'Yoga, Mobility & Posture',
            'bio': 'Corrective exercise and mobility coach focused on fixing muscular imbalances, core stability, and joint longevity.',
            'experience_years': 7,
            'certification': 'RYT-500, NASM Corrective Exercise Specialist',
            'hourly_rate': '50.00',
            'rating': 4.9,
            'available_days': 'Tue, Thu, Fri, Sun',
            'avatar_emoji': '🧘',
        },
        {
            'name': 'Coach David Chen',
            'specialty': 'Sports Nutrition & Conditioning',
            'bio': 'Integrates allergy-safe meal strategies with functional athletic conditioning for lean muscle and metabolic health.',
            'experience_years': 5,
            'certification': 'ISSN-SNS, NASM-CPT',
            'hourly_rate': '52.00',
            'rating': 4.7,
            'available_days': 'Wed, Thu, Sat, Sun',
            'avatar_emoji': '🥗',
        },
    ]
    for inst in instructors:
        Instructor.objects.get_or_create(name=inst['name'], defaults=inst)

    # 3. Update existing workouts & seed muscle-specific workouts
    workout_updates = {
        'Morning Run': ('cardio', 'cardio', 'beginner', 280),
        'Full Body Strength': ('full_body', 'strength', 'intermediate', 340),
        'HIIT Circuit': ('cardio', 'hiit', 'advanced', 360),
        'Yoga & Mobility': ('core', 'flexibility', 'beginner', 160),
        'Cycling Session': ('legs', 'cardio', 'intermediate', 310),
    }
    for name, (mg, wt, diff, cal) in workout_updates.items():
        Workout.objects.filter(name=name).update(
            muscle_group=mg,
            workout_type=wt,
            difficulty=diff,
            calories_burned_est=cal,
        )

    extra_workouts = [
        ('Chest & Triceps Power', 'Bench press, incline dumbbell press, dips, and tricep pushdowns.', 45, 'chest', 'strength', 'intermediate', 290),
        ('Back & Biceps Pull', 'Pull-ups, barbell rows, face pulls, and dumbbell curls for posture & pull strength.', 45, 'back', 'strength', 'intermediate', 300),
        ('Leg Day Foundation', 'Squats, Romanian deadlifts, lunges, and calf raises for lower-body power.', 50, 'legs', 'strength', 'intermediate', 380),
        ('Core & Posture Stability', 'Planks, dead bugs, bird-dogs, and anti-rotation presses to protect the spine.', 30, 'core', 'strength', 'beginner', 180),
        ('Shoulder Sculpt & Mobility', 'Overhead press, lateral raises, and rotator cuff stability work.', 35, 'shoulders', 'strength', 'intermediate', 240),
    ]
    for name, desc, dur, mg, wt, diff, cal in extra_workouts:
        Workout.objects.get_or_create(
            name=name,
            defaults={
                'description': desc,
                'duration_min': dur,
                'muscle_group': mg,
                'workout_type': wt,
                'difficulty': diff,
                'calories_burned_est': cal,
            },
        )

    # 4. Seed sample Meals with allergens & nutrition
    meals = [
        {
            'name': 'Peanut Butter Protein Oats',
            'description': 'Rolled oats cooked with milk, whey protein, banana slices, and creamy peanut butter.',
            'meal_type': 'breakfast',
            'allergens': 'nuts, dairy',
            'dietary_tags': 'vegetarian, high_protein',
            'calories': 520,
            'protein_g': 32.0,
            'carbs_g': 58.0,
            'fat_g': 16.0,
        },
        {
            'name': 'Grilled Salmon & Quinoa Bowl',
            'description': 'Herb-baked Atlantic salmon over fluffy quinoa, steamed broccoli, and lemon olive oil.',
            'meal_type': 'dinner',
            'allergens': 'fish',
            'dietary_tags': 'gluten_free, dairy_free, high_protein, low_sodium',
            'calories': 560,
            'protein_g': 42.0,
            'carbs_g': 44.0,
            'fat_g': 22.0,
        },
        {
            'name': 'Greek Yogurt & Almond Parfait',
            'description': 'Creamy Greek yogurt layered with fresh blueberries, honey, and toasted almonds.',
            'meal_type': 'snack',
            'allergens': 'dairy, nuts',
            'dietary_tags': 'vegetarian, gluten_free, high_protein',
            'calories': 290,
            'protein_g': 22.0,
            'carbs_g': 28.0,
            'fat_g': 9.0,
        },
        {
            'name': 'Vegan Chickpea & Spinach Curry',
            'description': 'Spiced chickpeas simmered with baby spinach, tomatoes, coconut milk, and brown rice.',
            'meal_type': 'lunch',
            'allergens': '',
            'dietary_tags': 'vegan, vegetarian, dairy_free, gluten_free, low_sodium',
            'calories': 440,
            'protein_g': 18.0,
            'carbs_g': 62.0,
            'fat_g': 12.0,
        },
        {
            'name': 'Egg & Whole Wheat Avocado Toast',
            'description': 'Two poached eggs over toasted whole wheat sourdough with mashed avocado and chili flakes.',
            'meal_type': 'breakfast',
            'allergens': 'eggs, gluten',
            'dietary_tags': 'vegetarian',
            'calories': 410,
            'protein_g': 20.0,
            'carbs_g': 36.0,
            'fat_g': 21.0,
        },
        {
            'name': 'Garlic Shrimp Whole Wheat Pasta',
            'description': 'Sautéed shrimp tossed with whole wheat penne, garlic, olive oil, and parmesan.',
            'meal_type': 'dinner',
            'allergens': 'shellfish, gluten, dairy',
            'dietary_tags': 'high_protein',
            'calories': 590,
            'protein_g': 38.0,
            'carbs_g': 64.0,
            'fat_g': 18.0,
        },
        {
            'name': 'Tofu & Broccoli Soy Stir-Fry',
            'description': 'Crispy organic tofu stir-fried with broccoli, bell peppers, ginger, and soy glaze.',
            'meal_type': 'lunch',
            'allergens': 'soy',
            'dietary_tags': 'vegan, vegetarian, dairy_free, high_protein',
            'calories': 390,
            'protein_g': 26.0,
            'carbs_g': 34.0,
            'fat_g': 15.0,
        },
        {
            'name': 'Grilled Chicken & Sweet Potato Plate',
            'description': 'Lean herb-grilled chicken breast with roasted sweet potato cubes and green beans.',
            'meal_type': 'lunch',
            'allergens': '',
            'dietary_tags': 'gluten_free, dairy_free, halal, high_protein, low_sodium',
            'calories': 480,
            'protein_g': 44.0,
            'carbs_g': 46.0,
            'fat_g': 11.0,
        },
    ]
    for m in meals:
        Meal.objects.get_or_create(name=m['name'], defaults=m)


def unseed_initial_data(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0003_instructor_membershippackage_meal_allergens_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, unseed_initial_data),
    ]
