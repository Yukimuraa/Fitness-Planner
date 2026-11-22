from django.db import migrations


def seed_meal_ingredients(apps, schema_editor):
    Meal = apps.get_model('planner', 'Meal')
    updates = {
        'Peanut Butter Protein Oats': (
            'rolled oats, cow milk, whey protein, banana, peanut butter',
            'Processed in a facility that handles tree nuts.',
            True,
        ),
        'Grilled Salmon & Quinoa Bowl': (
            'atlantic salmon, quinoa, broccoli, olive oil, lemon juice, herbs',
            'Prepared on dedicated grill; contains finfish.',
            True,
        ),
        'Greek Yogurt & Almond Parfait': (
            'greek yogurt, blueberries, honey, sliced almonds',
            'Contains milk and tree nuts.',
            True,
        ),
        'Vegan Chickpea & Spinach Curry': (
            'chickpeas, baby spinach, tomatoes, coconut milk, brown rice, turmeric, cumin',
            'Prepared in an allergen-controlled kitchen.',
            True,
        ),
        'Egg & Whole Wheat Avocado Toast': (
            'eggs, whole wheat sourdough bread, avocado, chili flakes',
            'Contains eggs and wheat.',
            True,
        ),
        'Garlic Shrimp Whole Wheat Pasta': (
            'shrimp, whole wheat penne pasta, garlic, olive oil, parmesan cheese',
            'Contains crustacean shellfish, wheat, and milk.',
            True,
        ),
        'Tofu & Broccoli Soy Stir-Fry': (
            'organic tofu, broccoli, bell peppers, ginger, soy sauce',
            'Contains soy; soy sauce may have trace wheat.',
            True,
        ),
        'Grilled Chicken & Sweet Potato Plate': (
            'chicken breast, sweet potato, green beans, olive oil, rosemary',
            'Prepared in an allergen-controlled kitchen.',
            True,
        ),
    }
    for name, (ingredients, cross_contact, verified) in updates.items():
        Meal.objects.filter(name=name).update(
            ingredients=ingredients,
            cross_contact_notes=cross_contact,
            ingredients_verified=verified,
        )


def unseed_meal_ingredients(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0005_meal_cross_contact_notes_meal_ingredients_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_meal_ingredients, unseed_meal_ingredients),
    ]
