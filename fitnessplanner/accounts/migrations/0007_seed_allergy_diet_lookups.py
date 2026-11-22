from django.db import migrations


def seed_lookups(apps, schema_editor):
    Allergen = apps.get_model('accounts', 'Allergen')
    FoodIntolerance = apps.get_model('accounts', 'FoodIntolerance')
    DietaryPreferenceOption = apps.get_model('accounts', 'DietaryPreferenceOption')

    allergens = [
        ('peanuts', 'Peanuts', 1),
        ('tree_nuts', 'Tree nuts', 2),
        ('seafood', 'Seafood', 3),
        ('milk_dairy', 'Milk / Dairy', 4),
        ('eggs', 'Eggs', 5),
        ('soy', 'Soy', 6),
        ('wheat', 'Wheat', 7),
        ('sesame', 'Sesame', 8),
        ('other', 'Other', 9),
    ]
    for slug, name, order in allergens:
        Allergen.objects.get_or_create(slug=slug, defaults={'name': name, 'display_order': order})

    intolerances = [
        ('lactose', 'Lactose intolerance', 1),
        ('gluten', 'Gluten sensitivity', 2),
        ('other', 'Other', 3),
    ]
    for slug, name, order in intolerances:
        FoodIntolerance.objects.get_or_create(slug=slug, defaults={'name': name, 'display_order': order})

    diet_prefs = [
        ('none', 'No specific preference', 1),
        ('vegetarian', 'Vegetarian', 2),
        ('vegan', 'Vegan', 3),
        ('pescatarian', 'Pescatarian', 4),
        ('halal', 'Halal', 5),
        ('gluten_free', 'Gluten-free', 6),
        ('dairy_free', 'Dairy-free', 7),
    ]
    for slug, name, order in diet_prefs:
        DietaryPreferenceOption.objects.get_or_create(slug=slug, defaults={'name': name, 'display_order': order})


def unseed_lookups(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_allergen_dietarypreferenceoption_foodintolerance_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_lookups, unseed_lookups),
    ]
