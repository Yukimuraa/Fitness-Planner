from datetime import date, timedelta
from .models import Meal, Workout, WorkoutSchedule


ALLERGEN_KEYWORDS = {
    'nuts': ['peanut', 'almond', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio', 'nut'],
    'peanuts': ['peanut', 'peanut butter'],
    'tree_nuts': ['almond', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio', 'tree nut'],
    'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'whey', 'parmesan', 'feta', 'cottage'],
    'milk_dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'whey', 'parmesan', 'feta', 'cottage', 'dairy'],
    'gluten': ['wheat', 'bread', 'pasta', 'penne', 'flour', 'sourdough', 'wrap', 'tortilla', 'cracker', 'oats', 'granola'],
    'wheat': ['wheat', 'bread', 'pasta', 'penne', 'flour', 'sourdough', 'wrap', 'tortilla', 'cracker'],
    'eggs': ['egg', 'eggs', 'frittata', 'omelette', 'mayo'],
    'shellfish': ['shrimp', 'prawn', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop'],
    'seafood': ['shrimp', 'prawn', 'crab', 'lobster', 'salmon', 'tuna', 'cod', 'fish', 'shellfish', 'finfish'],
    'soy': ['soy', 'tofu', 'edamame', 'tempeh', 'teriyaki', 'miso'],
    'fish': ['salmon', 'tuna', 'cod', 'tilapia', 'trout', 'fish', 'anchovy', 'finfish'],
    'sesame': ['sesame', 'tahini'],
}

ALLERGEN_SWAPS = {
    'nuts': 'Swap peanut/almond butter for sunflower seed butter or pumpkin seeds.',
    'peanuts': 'Swap peanut butter for sunflower seed butter or pumpkin seed butter.',
    'tree_nuts': 'Swap almonds/tree nuts for toasted pumpkin seeds or sunflower seeds.',
    'dairy': 'Swap cow milk/yogurt/cheese for unsweetened oat milk, coconut yogurt, or plant-based protein.',
    'milk_dairy': 'Swap cow milk/yogurt/cheese for unsweetened oat milk or coconut yogurt.',
    'gluten': 'Swap wheat bread/pasta for quinoa, brown rice, sweet potato, or certified gluten-free oats.',
    'wheat': 'Swap wheat bread/pasta for quinoa, brown rice, or sweet potato.',
    'eggs': 'Swap eggs for scrambled tofu, chickpea flour frittata, or flax-egg in baking.',
    'shellfish': 'Swap shrimp/shellfish for grilled chicken breast, white beans, or firm tofu.',
    'seafood': 'Swap seafood for grilled chicken breast, lentils, or organic tofu.',
    'soy': 'Swap soy sauce/tofu for coconut aminos and grilled chicken, lentils, or chickpeas.',
    'fish': 'Swap fish for chicken breast, turkey, or hemp/chia seeds for omega-3s.',
    'sesame': 'Swap sesame/tahini for olive oil or sunflower seed paste.',
}


def analyze_workout_imbalance(user, profile):
    """Analyze the user's recent & upcoming WorkoutSchedule for muscle/modality imbalances."""
    today = date.today()
    window_start = today - timedelta(days=30)
    window_end = today + timedelta(days=7)

    schedules = (
        WorkoutSchedule.objects
        .filter(user=user, date__gte=window_start, date__lte=window_end)
        .select_related('workout')
    )

    muscle_counts = {
        'chest': 0,
        'back': 0,
        'legs': 0,
        'shoulders': 0,
        'arms': 0,
        'core': 0,
        'cardio': 0,
        'full_body': 0,
    }
    type_counts = {'strength': 0, 'cardio': 0, 'hiit': 0, 'flexibility': 0}

    total_sessions = schedules.count()
    for s in schedules:
        mg = s.workout.muscle_group
        wt = s.workout.workout_type
        if mg in muscle_counts:
            muscle_counts[mg] += 1
        if wt in type_counts:
            type_counts[wt] += 1

    # Distribute full_body partially across major groups for balance visualization
    effective_upper_push = muscle_counts['chest'] + muscle_counts['shoulders'] + muscle_counts['arms'] + muscle_counts['full_body'] * 0.5
    effective_upper_pull = muscle_counts['back'] + muscle_counts['full_body'] * 0.5
    effective_lower = muscle_counts['legs'] + muscle_counts['full_body'] * 0.5
    effective_core = muscle_counts['core'] + type_counts['flexibility']

    imbalances = []
    penalty = 0

    if total_sessions == 0:
        imbalances.append({
            'severity': 'info',
            'title': 'No Recent Workouts Scheduled',
            'detail': 'You have 0 workouts logged in the last 30 days. Schedule a balanced starter week so the system can track your muscle symmetry.',
            'recommendation': 'Start with Full Body Strength, Morning Run, and Core & Posture Stability.',
            'suggested_workouts': list(Workout.objects.filter(name__in=[
                'Full Body Strength', 'Morning Run', 'Core & Posture Stability'
            ])),
        })
        score = 65
    else:
        # 1. Push vs Pull imbalance
        if effective_upper_push > effective_upper_pull + 1.5:
            penalty += 18
            imbalances.append({
                'severity': 'high',
                'title': 'Push-Dominant Imbalance (Chest/Arms > Back)',
                'detail': f'You have more push-focused sessions ({int(effective_upper_push)}) than back/pull sessions ({int(effective_upper_pull)}). Over time this can cause rounded shoulders and neck strain.',
                'recommendation': 'Add Back & Biceps Pull workouts to restore shoulder and posture balance.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group='back')[:2]),
            })
        elif effective_upper_pull > effective_upper_push + 2:
            penalty += 10
            imbalances.append({
                'severity': 'medium',
                'title': 'Pull-Heavy Split (Back > Chest/Shoulders)',
                'detail': 'Your pulling volume is noticeably higher than pressing volume.',
                'recommendation': 'Balance with Chest & Triceps Power or Shoulder Sculpt & Mobility.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group__in=['chest', 'shoulders'])[:2]),
            })

        # 2. Upper vs Lower body imbalance
        total_upper = effective_upper_push + effective_upper_pull
        if total_upper >= 2 and effective_lower == 0:
            penalty += 22
            imbalances.append({
                'severity': 'high',
                'title': 'Upper-Body Dominant (Missing Leg Training)',
                'detail': f'You have {int(total_upper)} upper-body sessions but 0 leg-focused sessions. Skipping legs limits metabolic output and lower-body stability.',
                'recommendation': 'Schedule Leg Day Foundation or Cycling Session this week.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group='legs')[:2]),
            })
        elif effective_lower >= 3 and total_upper == 0:
            penalty += 15
            imbalances.append({
                'severity': 'medium',
                'title': 'Lower-Body Heavy (Missing Upper Body)',
                'detail': 'Your schedule is heavily focused on legs/cardio with no dedicated upper-body strength work.',
                'recommendation': 'Add Full Body Strength or Back & Biceps Pull.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group__in=['back', 'chest'])[:2]),
            })

        # 3. Core & Mobility deficit
        if total_sessions >= 3 and effective_core == 0:
            penalty += 12
            imbalances.append({
                'severity': 'medium',
                'title': 'Core & Mobility Deficit',
                'detail': 'No core stability or flexibility/mobility sessions found in your recent schedule.',
                'recommendation': 'Add Core & Posture Stability or Yoga & Mobility at least once a week.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group='core')[:2]),
            })

        # 4. Goal vs Modality mismatch
        cardio_total = type_counts['cardio'] + type_counts['hiit']
        strength_total = type_counts['strength']
        if profile.fitness_goal == 'build_muscle' and cardio_total > strength_total + 1:
            penalty += 15
            imbalances.append({
                'severity': 'medium',
                'title': 'Cardio-Heavy for a Muscle-Building Goal',
                'detail': f'Your goal is Build Muscle, but cardio/HIIT ({cardio_total}) outweighs strength training ({strength_total}).',
                'recommendation': 'Shift toward resistance sessions like Full Body Strength, Chest & Triceps Power, or Leg Day Foundation.',
                'suggested_workouts': list(Workout.objects.filter(workout_type='strength')[:3]),
            })
        elif profile.fitness_goal == 'lose_weight' and cardio_total == 0 and total_sessions >= 2:
            penalty += 12
            imbalances.append({
                'severity': 'medium',
                'title': 'No Cardio/HIIT Scheduled for Fat Loss',
                'detail': 'Your goal is Lose Weight, but your schedule currently has 0 cardio or HIIT sessions.',
                'recommendation': 'Include 1–2 cardio or HIIT sessions alongside strength training to boost calorie expenditure.',
                'suggested_workouts': list(Workout.objects.filter(workout_type__in=['cardio', 'hiit'])[:2]),
            })

        # 5. Focused muscle gap check
        focused = profile.get_focused_muscles_list()
        missing_focused = []
        for m in focused:
            mapped = 'legs' if m in ('glutes', 'calves', 'legs') else m
            if muscle_counts.get(mapped, 0) == 0 and muscle_counts['full_body'] == 0:
                missing_focused.append(m)
        if missing_focused:
            penalty += 10
            imbalances.append({
                'severity': 'info',
                'title': f'Selected Focus Areas Not Scheduled ({", ".join(m.title() for m in missing_focused)})',
                'detail': 'You selected these muscle groups in your profile, but they are not yet in your 30-day schedule.',
                'recommendation': 'Add targeted workouts for your chosen focus muscles.',
                'suggested_workouts': list(Workout.objects.filter(muscle_group__in=missing_focused)[:3]),
            })

        score = max(25, 100 - penalty)

    if score >= 85:
        status = 'Well Balanced'
        status_class = 'success'
    elif score >= 65:
        status = 'Mild Imbalance'
        status_class = 'warning'
    else:
        status = 'Needs Attention'
        status_class = 'danger'

    # Distribution percentages for UI bars
    max_count = max(muscle_counts.values()) if any(muscle_counts.values()) else 1
    distribution = []
    labels = dict(Workout.MUSCLE_GROUP_CHOICES)
    for key, count in muscle_counts.items():
        distribution.append({
            'key': key,
            'label': labels.get(key, key.title()),
            'count': count,
            'pct': int((count / max_count) * 100) if max_count else 0,
        })

    return {
        'score': score,
        'status': status,
        'status_class': status_class,
        'total_sessions': total_sessions,
        'imbalances': imbalances,
        'distribution': distribution,
        'type_counts': type_counts,
    }


def generate_fitness_recommendation(user, profile):
    """Generate a personalized fitness plan based on user's profile details & health conditions."""
    goal = profile.fitness_goal or 'maintain_weight'
    activity = profile.activity_level or 'moderate'
    bmi_val = profile.bmi()
    bmi_cat = profile.bmi_category()
    age = profile.age or 28
    conditions = profile.get_health_conditions_list()
    focused = profile.get_focused_muscles_list()

    max_hr = max(130, 220 - int(age))
    hr_fat_burn = (int(max_hr * 0.60), int(max_hr * 0.72))
    hr_cardio = (int(max_hr * 0.72), int(max_hr * 0.85))

    # Determine weekly frequency & session length from activity level + age
    freq_map = {
        'sedentary': (3, 30, 'Beginner / Low-Impact'),
        'light': (3, 35, 'Beginner–Intermediate'),
        'moderate': (4, 45, 'Intermediate'),
        'active': (5, 50, 'Intermediate–Advanced'),
        'very_active': (6, 55, 'Advanced'),
    }
    days_per_week, mins_per_session, intensity_label = freq_map.get(activity, (4, 40, 'Intermediate'))

    # Safety adjustments for BMI or health conditions
    safety_notes = []
    prefer_low_impact = False
    if 'joint_pain' in conditions or (bmi_val and bmi_val >= 30):
        prefer_low_impact = True
        safety_notes.append('Low-impact workouts prioritized (Cycling, Yoga & Mobility, Controlled Strength) to protect your joints.')
    if 'hypertension' in conditions:
        safety_notes.append(f'Keep heart rate in moderate steady-state zone ({hr_fat_burn[0]}–{hr_fat_burn[1]} bpm) and avoid breath-holding during heavy lifts.')
    if 'diabetes' in conditions:
        safety_notes.append('Consistent post-meal movement (30–40 min moderate cardio + strength) helps stabilize blood glucose.')
    if age >= 50:
        safety_notes.append('Include a 5–10 minute warm-up and extra mobility/core stability work for joint longevity.')

    # Goal-based split
    if goal == 'lose_weight':
        split_title = 'Fat Loss & Metabolic Conditioning Split'
        split_summary = f'{days_per_week} days/week: 2 Strength + {max(1, days_per_week - 3)} Cardio/HIIT + 1 Mobility'
        preferred_types = ['cardio', 'strength', 'flexibility'] if prefer_low_impact else ['hiit', 'cardio', 'strength']
    elif goal == 'build_muscle':
        split_title = 'Hypertrophy & Progressive Strength Split'
        split_summary = f'{days_per_week} days/week: {max(2, days_per_week - 1)} Strength + 1 Mobility/Light Cardio'
        preferred_types = ['strength', 'flexibility']
    elif goal == 'improve_fitness':
        split_title = 'Endurance, Stamina & Functional Split'
        split_summary = f'{days_per_week} days/week: 2 Cardio + 2 Functional Strength + 1 Mobility'
        preferred_types = ['cardio', 'strength', 'flexibility'] if prefer_low_impact else ['cardio', 'hiit', 'strength', 'flexibility']
    else:
        split_title = 'Balanced Health & Longevity Split'
        split_summary = f'{days_per_week} days/week: 2 Full-Body Strength + 1–2 Cardio + 1 Core/Yoga'
        preferred_types = ['strength', 'cardio', 'flexibility']

    # Match workouts from DB
    all_workouts = list(Workout.objects.all())
    scored_workouts = []
    mapped_focused = set('legs' if m in ('glutes', 'calves') else m for m in focused)

    for w in all_workouts:
        score = 0
        if w.workout_type in preferred_types:
            score += 3
        if w.muscle_group in mapped_focused:
            score += 4
        if prefer_low_impact and w.workout_type == 'hiit':
            score -= 5
        if activity in ('sedentary', 'light') and w.difficulty == 'advanced':
            score -= 2
        if activity in ('sedentary', 'light') and w.difficulty == 'beginner':
            score += 2
        scored_workouts.append((score, w))

    scored_workouts.sort(key=lambda x: x[0], reverse=True)
    recommended_workouts = [w for _, w in scored_workouts[:4]]

    return {
        'split_title': split_title,
        'split_summary': split_summary,
        'days_per_week': days_per_week,
        'mins_per_session': mins_per_session,
        'intensity_label': intensity_label,
        'max_hr': max_hr,
        'hr_fat_burn': hr_fat_burn,
        'hr_cardio': hr_cardio,
        'bmi_val': bmi_val,
        'bmi_cat': bmi_cat,
        'safety_notes': safety_notes,
        'recommended_workouts': recommended_workouts,
    }


def analyze_meal_health(meal, profile):
    """Deterministic ingredient-based allergy, intolerance & dietary filtering for a chosen Meal."""
    from fitnessplanner.accounts.models import MemberAllergy, MemberIntolerance, MemberDietaryProfile

    user = profile.user
    user_allergies = list(profile.get_allergies_list())
    member_allergies = list(MemberAllergy.objects.filter(user=user).select_related('allergen'))
    for ma in member_allergies:
        slug = ma.allergen.slug
        if slug == 'other' and ma.custom_name:
            val = ma.custom_name.strip().lower()
        else:
            val = slug
        if val and val not in user_allergies:
            user_allergies.append(val)

    member_intolerances = list(MemberIntolerance.objects.filter(user=user).select_related('intolerance'))
    diet_prof = MemberDietaryProfile.objects.filter(user=user).first()
    diet_pref_slugs = list(diet_prof.dietary_preferences.values_list('slug', flat=True)) if diet_prof else []
    if not diet_pref_slugs and profile.dietary_preference and profile.dietary_preference != 'none':
        diet_pref_slugs = [profile.dietary_preference]

    conditions = profile.get_health_conditions_list()
    meal_allergens = set(meal.get_allergens_list())
    meal_tags = set(meal.get_dietary_tags_list())

    # Scan meal ingredients, cross-contact notes, name, description, and items
    text_blob = (
        f"{meal.name} {meal.description} {meal.ingredients} {meal.cross_contact_notes} "
        + " ".join(i.name for i in meal.items.all())
    )
    text_lower = text_blob.lower()

    detected_allergens = set(meal_allergens)
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected_allergens.add(allergen)

    # Check user allergy conflicts (CRITICAL: runs before any recommendation)
    allergy_conflicts = []
    swaps = []
    for ua in user_allergies:
        kws = ALLERGEN_KEYWORDS.get(ua, [ua])
        if ua in detected_allergens or any(kw in text_lower for kw in kws):
            allergy_conflicts.append(ua)
            if ua in ALLERGEN_SWAPS and ALLERGEN_SWAPS[ua] not in swaps:
                swaps.append(ALLERGEN_SWAPS[ua])

    # Check ingredient & cross-contact verification
    missing_verification = not meal.ingredients_verified or not meal.ingredients.strip()

    # Check Food Intolerances separately from allergies
    health_alerts = []
    meal_cal = meal.total_calories
    meal_carbs = meal.total_carbs
    meal_fat = meal.total_fat

    intol_slugs = [mi.intolerance.slug for mi in member_intolerances]
    if ('lactose' in intol_slugs or 'lactose_intolerant' in conditions) and (
        'dairy' in detected_allergens or 'milk_dairy' in detected_allergens
    ):
        health_alerts.append({
            'level': 'warning',
            'title': 'Lactose Intolerance Note',
            'message': 'This meal contains dairy ingredients that may trigger lactose sensitivity.',
        })
        if ALLERGEN_SWAPS['dairy'] not in swaps:
            swaps.append(ALLERGEN_SWAPS['dairy'])

    if ('gluten' in intol_slugs or 'celiac' in conditions) and (
        'gluten' in detected_allergens or 'wheat' in detected_allergens
    ):
        health_alerts.append({
            'level': 'warning',
            'title': 'Gluten Sensitivity Note',
            'message': 'This meal contains wheat or gluten-bearing ingredients.',
        })
        if ALLERGEN_SWAPS['gluten'] not in swaps:
            swaps.append(ALLERGEN_SWAPS['gluten'])

    if 'diabetes' in conditions and meal_carbs > 50:
        health_alerts.append({
            'level': 'warning',
            'title': 'Carbohydrate Note',
            'message': f'Contains {meal_carbs}g carbs. Consider pairing with fiber or adjusting portion size.',
        })

    if 'hypertension' in conditions and 'low_sodium' not in meal_tags:
        if any(w in text_lower for w in ['soy', 'teriyaki', 'parmesan', 'feta', 'deli', 'cured']):
            health_alerts.append({
                'level': 'warning',
                'title': 'Sodium Note',
                'message': 'Ingredients like soy sauce or aged cheese can be higher in sodium.',
            })

    if 'high_cholesterol' in conditions and meal_fat > 20:
        health_alerts.append({
            'level': 'warning',
            'title': 'Fat Intake Note',
            'message': f'Contains {meal_fat}g total fat.',
        })

    # Dietary preference compatibility
    diet_alerts = []
    if 'vegan' in diet_pref_slugs and ('vegan' not in meal_tags) and any(
        a in detected_allergens for a in ['dairy', 'milk_dairy', 'eggs', 'fish', 'shellfish', 'seafood']
    ):
        diet_alerts.append('May not fit a strict Vegan diet (contains animal-derived ingredients).')
    if 'vegetarian' in diet_pref_slugs and any(
        w in text_lower for w in ['chicken', 'beef', 'turkey', 'salmon', 'shrimp', 'tuna', 'cod', 'pork']
    ):
        diet_alerts.append('Contains meat/seafood — conflicts with your Vegetarian preference.')
    if 'pescatarian' in diet_pref_slugs and any(
        w in text_lower for w in ['chicken', 'beef', 'turkey', 'pork']
    ):
        diet_alerts.append('Contains poultry/meat — conflicts with your Pescatarian preference.')
    if 'dairy_free' in diet_pref_slugs and ('dairy' in detected_allergens or 'milk_dairy' in detected_allergens):
        diet_alerts.append('Contains dairy — conflicts with your Dairy-free preference.')
    if 'gluten_free' in diet_pref_slugs and ('gluten' in detected_allergens or 'wheat' in detected_allergens):
        diet_alerts.append('Contains wheat/gluten — conflicts with your Gluten-free preference.')
    if 'keto' in diet_pref_slugs and meal_carbs > 25:
        diet_alerts.append(f'Contains {meal_carbs}g carbs, which is above a typical Keto per-meal target (<25g).')

    # Calorie & Goal Fit (BMR / TDEE / Fitness Goal)
    daily_cal = profile.daily_calorie_recommendation()
    goal_fit = 'Good fit for your daily target.'
    if daily_cal and meal_cal:
        target_per_meal = int(daily_cal * 0.30)
        if meal_cal > target_per_meal * 1.35:
            goal_fit = f'High calorie ({meal_cal} kcal vs ~{target_per_meal} kcal ideal per meal). Consider a slightly smaller portion.'
        elif meal_cal < target_per_meal * 0.55 and profile.fitness_goal == 'build_muscle':
            goal_fit = f'Light calorie ({meal_cal} kcal vs ~{target_per_meal} kcal target). Add extra protein or complex carbs for muscle growth.'
        else:
            goal_fit = f'Great calorie match ({meal_cal} kcal vs ~{target_per_meal} kcal target per meal).'

    # Overall Verdict (CRITICAL SAFETY: never mark unverified meals as safe)
    if allergy_conflicts:
        verdict = 'Excluded — Allergen Detected'
        verdict_class = 'danger'
        verdict_summary = 'This meal contains an allergen from your registered profile and is excluded for your safety.'
    elif missing_verification:
        verdict = 'Verification Required'
        verdict_class = 'warning'
        verdict_summary = 'Ingredients or cross-contact information are unknown. Verify before consuming.'
    elif health_alerts or diet_alerts:
        verdict = 'Caution / Adjust'
        verdict_class = 'warning'
        verdict_summary = 'Free of registered allergens, with intolerance or dietary preference notes.'
    else:
        verdict = 'Safe & Recommended'
        verdict_class = 'success'
        verdict_summary = 'Verified ingredients — no registered allergy, intolerance, or dietary conflicts!'

    # Find safe, verified alternative meals from DB
    safe_alternatives = []
    for candidate in Meal.objects.exclude(pk=meal.pk).filter(ingredients_verified=True):
        if not candidate.ingredients.strip():
            continue
        cand_blob = f"{candidate.name} {candidate.description} {candidate.ingredients} {candidate.cross_contact_notes}".lower()
        cand_allergens = set(candidate.get_allergens_list())
        for allergen, kws in ALLERGEN_KEYWORDS.items():
            if any(kw in cand_blob for kw in kws):
                cand_allergens.add(allergen)
        has_allergy = any(
            ua in cand_allergens or any(kw in cand_blob for kw in ALLERGEN_KEYWORDS.get(ua, [ua]))
            for ua in user_allergies
        )
        if not has_allergy:
            safe_alternatives.append(candidate)
        if len(safe_alternatives) >= 3:
            break

    return {
        'verdict': verdict,
        'verdict_class': verdict_class,
        'verdict_summary': verdict_summary,
        'missing_verification': missing_verification,
        'detected_allergens': sorted(detected_allergens),
        'allergy_conflicts': allergy_conflicts,
        'health_alerts': health_alerts,
        'diet_alerts': diet_alerts,
        'goal_fit': goal_fit,
        'swaps': swaps,
        'safe_alternatives': safe_alternatives,
    }
