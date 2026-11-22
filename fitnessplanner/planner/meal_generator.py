def generate_meal_plan(profile):
    """
    Generates a personalized daily meal plan scaled to the user's calorie needs,
    with protein, carb, and fat breakdowns, plus custom tips based on goal,
    BMI category, age, gender, and activity level.
    """
    calories = profile.daily_calorie_recommendation()
    if not calories:
        return None

    goal = profile.fitness_goal
    bmi_cat = profile.bmi_category()
    age = profile.age
    gender = profile.gender
    activity = profile.activity_level

    # 1. Define Macro Splits based on fitness goal
    # splits: (protein_pct, carb_pct, fat_pct)
    if goal == 'lose_weight':
        # High protein to maintain lean mass, moderate carbs, moderate-low fat
        p_pct, c_pct, f_pct = 0.35, 0.35, 0.30
    elif goal == 'build_muscle':
        # Moderate-high protein, high carbs to fuel hypertrophy, moderate fat
        p_pct, c_pct, f_pct = 0.30, 0.45, 0.25
    elif goal == 'improve_fitness':
        # High carb for endurance/energy, moderate protein and fat
        p_pct, c_pct, f_pct = 0.25, 0.50, 0.25
    else:  # maintain_weight or empty
        # Balanced zone
        p_pct, c_pct, f_pct = 0.25, 0.45, 0.30

    # Total macro grams
    total_protein_g = (calories * p_pct) / 4.0
    total_carbs_g = (calories * c_pct) / 4.0
    total_fat_g = (calories * f_pct) / 9.0

    # 2. Meal distribution (Breakfast: 25%, Lunch: 35%, Dinner: 30%, Snack: 10%)
    meal_allocations = {
        'Breakfast': 0.25,
        'Lunch': 0.35,
        'Dinner': 0.30,
        'Snack': 0.10
    }

    # 3. Base dishes based on goal
    if goal == 'lose_weight':
        meals_db = {
            'Breakfast': {
                'title': 'Egg White & Spinach Frittata',
                'description': 'Egg whites cooked with fresh baby spinach, cherry tomatoes, sliced mushrooms, and a sprinkle of low-fat feta cheese. Served with 1 slice of toasted whole wheat bread.',
                'image': '🍳'
            },
            'Lunch': {
                'title': 'Grilled Chicken & Quinoa Garden Salad',
                'description': 'Sliced grilled chicken breast over a bed of mixed baby greens, cucumbers, cherry tomatoes, and red onions, tossed with fluffy quinoa and a light lemon-olive oil dressing.',
                'image': '🥗'
            },
            'Dinner': {
                'title': 'Baked Garlic Herb Salmon',
                'description': 'Oven-baked salmon fillet seasoned with garlic, dill, and lemon juice. Served with a side of steamed asparagus and a serving of cauliflower mash.',
                'image': '🐟'
            },
            'Snack': {
                'title': 'Greek Yogurt & Blueberry Parfait',
                'description': 'Fat-free plain Greek yogurt topped with a handful of fresh blueberries, chia seeds, and a light dusting of cinnamon.',
                'image': '🥛'
            }
        }
    elif goal == 'build_muscle':
        meals_db = {
            'Breakfast': {
                'title': 'Power Protein Oatmeal Bowl',
                'description': 'Whole rolled oats cooked in almond milk, stirred with a scoop of whey protein powder. Topped with banana slices, a spoonful of peanut butter, and chia seeds.',
                'image': '🥣'
            },
            'Lunch': {
                'title': 'Lean Beef & Sweet Potato Mash',
                'description': 'Lean ground beef seasoned with garlic and onion, served alongside roasted mashed sweet potato and a generous side of steamed green broccoli.',
                'image': '🥩'
            },
            'Dinner': {
                'title': 'Teriyaki Turkey & Brown Rice Bowl',
                'description': 'Sautéed lean ground turkey breast with red bell peppers, snap peas, and carrots in a light low-sodium teriyaki sauce. Served over steamed brown rice.',
                'image': '🍲'
            },
            'Snack': {
                'title': 'Cottage Cheese & Whole Grain Crackers',
                'description': 'High-protein low-fat cottage cheese served with crisp whole-grain crackers and a small handful of raw sliced almonds.',
                'image': '🧀'
            }
        }
    elif goal == 'improve_fitness':
        meals_db = {
            'Breakfast': {
                'title': 'Berry-Spinach Performance Smoothie Bowl',
                'description': 'Smoothie blended with mixed berries, spinach, plant protein, rolled oats, and flaxseeds. Served in a bowl topped with toasted pumpkin seeds and sugar-free granola.',
                'image': '🍧'
            },
            'Lunch': {
                'title': 'Tuna, Chickpea, & Spinach Salad',
                'description': 'Canned tuna in water flakes mixed with chickpeas, diced cucumber, cherry tomatoes, red onion, and baby spinach leaves, dressed with extra-virgin olive oil and red wine vinegar.',
                'image': '🥗'
            },
            'Dinner': {
                'title': 'Baked Cod with Roasted Mediterranean Veggies',
                'description': 'Fresh cod fillet baked with herbs, served alongside roasted eggplant, zucchini, bell peppers, and tomatoes, with a side portion of red quinoa.',
                'image': '🐟'
            },
            'Snack': {
                'title': 'Antioxidant Nut & Fruit Mix',
                'description': 'A nutritious raw mix of almonds, walnuts, pumpkin seeds, and unsweetened dried apricots or cranberries.',
                'image': '🥜'
            }
        }
    else:  # maintain_weight or general
        meals_db = {
            'Breakfast': {
                'title': 'Avocado Toast with Poached Eggs',
                'description': 'Two poached eggs served on toasted whole grain sourdough bread spread with mashed ripe avocado, sprinkled with red pepper flakes and black pepper.',
                'image': '🥑'
            },
            'Lunch': {
                'title': 'Turkey Breast & Creamy Hummus Wrap',
                'description': 'Sliced deli turkey breast, creamy hummus, baby spinach leaves, and sliced tomatoes rolled tightly in a whole wheat wrap tortilla.',
                'image': '🌯'
            },
            'Dinner': {
                'title': 'Shrimp Pesto Whole Wheat Pasta',
                'description': 'Pan-seared shrimp tossed with whole wheat penne pasta, basil pesto sauce, sautéed cherry tomatoes, and diced zucchini, topped with grated parmesan.',
                'image': '🍝'
            },
            'Snack': {
                'title': 'Apple Slices with Natural Almond Butter',
                'description': 'One medium crisp apple sliced and served with a side of natural, unsalted almond butter for dipping.',
                'image': '🍎'
            }
        }

    # 4. Generate final output with portions scaled to target calories & allergy/health check
    from fitnessplanner.planner.fitness_engine import ALLERGEN_KEYWORDS, ALLERGEN_SWAPS
    from fitnessplanner.accounts.models import MemberAllergy
    user_allergies = list(profile.get_allergies_list()) if hasattr(profile, 'get_allergies_list') else []
    if hasattr(profile, 'user'):
        for ma in MemberAllergy.objects.filter(user=profile.user).select_related('allergen'):
            val = ma.custom_name.strip().lower() if (ma.allergen.slug == 'other' and ma.custom_name) else ma.allergen.slug
            if val and val not in user_allergies:
                user_allergies.append(val)
    user_conditions = profile.get_health_conditions_list() if hasattr(profile, 'get_health_conditions_list') else []

    meal_plan = []
    for meal_name, allocation in meal_allocations.items():
        meal_cal = int(round(calories * allocation))
        meal_p = round(total_protein_g * allocation, 1)
        meal_c = round(total_carbs_g * allocation, 1)
        meal_f = round(total_fat_g * allocation, 1)
        
        base_info = meals_db[meal_name]
        
        # Calculate portion guide dynamically based on calories
        # For UI layout, show scaling guidance
        portion_scale = round(meal_cal / 350.0, 2)
        if portion_scale < 0.6:
            portion_desc = "Light portion (e.g., small single serving/smaller sizing)."
        elif portion_scale > 1.4:
            portion_desc = "Generous portion (e.g., double size or large serving + extra greens)."
        else:
            portion_desc = "Standard single serving size."

        # Check allergy / health compatibility
        text_lower = f"{base_info['title']} {base_info['description']}".lower()
        conflicts = []
        swaps = []
        for ua in user_allergies:
            kws = ALLERGEN_KEYWORDS.get(ua, [ua])
            if any(kw in text_lower for kw in kws):
                conflicts.append(ua.title())
                if ua in ALLERGEN_SWAPS:
                    swaps.append(ALLERGEN_SWAPS[ua])
        if 'lactose_intolerant' in user_conditions and any(kw in text_lower for kw in ALLERGEN_KEYWORDS['dairy']):
            if 'Dairy' not in conflicts:
                conflicts.append('Lactose/Dairy')
                swaps.append(ALLERGEN_SWAPS['dairy'])
        if 'celiac' in user_conditions and any(kw in text_lower for kw in ALLERGEN_KEYWORDS['gluten']):
            if 'Gluten' not in conflicts:
                conflicts.append('Gluten')
                swaps.append(ALLERGEN_SWAPS['gluten'])

        meal_plan.append({
            'type': meal_name,
            'title': base_info['title'],
            'description': base_info['description'],
            'image': base_info['image'],
            'calories': meal_cal,
            'protein': meal_p,
            'carbs': meal_c,
            'fat': meal_f,
            'portion_guide': portion_desc,
            'allergy_conflicts': conflicts,
            'safe_swaps': swaps,
        })

    # 5. Personalized physiological notes
    personalized_notes = []
    
    # BMI category notes
    if bmi_cat == 'Obese':
        personalized_notes.append("💡 **Satiety Tip**: Because your BMI indicates obesity, focus on eating high-volume, low-calorie foods. Consider starting lunch and dinner with a large leafy green salad or broth-based soup to increase fullness naturally.")
    elif bmi_cat == 'Overweight':
        personalized_notes.append("💡 **Portion Control**: Your BMI falls in the overweight range. Focus on precise portions. Avoid liquid calories (juices, sodas) and stay consistent with the recommended snack sizing.")
    elif bmi_cat == 'Underweight':
        personalized_notes.append("💡 **Nutrient Density**: Your BMI indicates you are underweight. Consider adding nutrient-dense healthy fats like a tablespoon of extra olive oil to salads or a tablespoon of honey to oatmeal/smoothies to help build strength.")
    else:
        personalized_notes.append("💡 **Maintenance Zones**: Your BMI is in the normal, healthy range. Focus on nutrient quality, raw energy levels, and maintaining metabolic health.")

    # Age notes
    if age and age >= 50:
        personalized_notes.append("💡 **Bone & Muscle Health (Age 50+)**: Prioritize calcium-rich foods (Greek yogurt, cottage cheese) and maintain steady protein intake to support bone density and prevent age-related muscle loss.")
    elif age and age < 20:
        personalized_notes.append("💡 **Growth Support (Under 20)**: Your body is still growing. Do not severely restrict carbohydrates, as they are crucial for cognitive function and active development. Ensure plenty of calcium and hydration.")

    # Gender notes
    if gender == 'female':
        personalized_notes.append("💡 **Micronutrient Focus**: Ensure you get adequate iron (found in baby spinach, lentils, seeds) and pair it with Vitamin C (lemon dressing, berries) for optimal absorption.")
    elif gender == 'male':
        personalized_notes.append("💡 **Strength Recovery**: Ensure sufficient hydration and magnesium levels to support testosterone production and muscle repair after intensive workouts.")

    # Activity level notes
    if activity in ['active', 'very_active']:
        personalized_notes.append("💡 **Athlete Fueling**: Since you are highly active, try to consume your complex carbohydrates (oatmeal, sweet potatoes, brown rice) in the 2-3 hours surrounding your workout windows to maximize performance and speed up recovery.")
    else:
        personalized_notes.append("💡 **Sedentary Movement**: For moderate/light activity, focus on staying active throughout the day (e.g. 10,000 steps). Avoid over-consuming carbs on days you do not exercise.")

    return {
        'calories': calories,
        'macros': {
            'protein': round(total_protein_g, 1),
            'carbs': round(total_carbs_g, 1),
            'fat': round(total_fat_g, 1),
            'protein_pct': int(p_pct * 100),
            'carbs_pct': int(c_pct * 100),
            'fat_pct': int(f_pct * 100)
        },
        'meals': meal_plan,
        'notes': personalized_notes
    }
