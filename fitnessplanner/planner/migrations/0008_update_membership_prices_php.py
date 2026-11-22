from django.db import migrations


def update_prices_to_php(apps, schema_editor):
    MembershipPackage = apps.get_model('planner', 'MembershipPackage')
    php_prices = {
        'starter-basic': ('0.00', 30),
        'pro-fitness': ('499.00', 30),
        'elite-transformation': ('999.00', 30),
        '90-day-bundle-package': ('2499.00', 90),
    }
    for slug, (price, duration) in php_prices.items():
        MembershipPackage.objects.filter(slug=slug).update(
            price=price,
            duration_days=duration,
        )


def revert_prices(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0007_usermembership_admin_notes_usermembership_amount_php_and_more'),
    ]

    operations = [
        migrations.RunPython(update_prices_to_php, revert_prices),
    ]
