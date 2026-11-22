from django.db import migrations


def seed_workouts(apps, schema_editor):
    Workout = apps.get_model('planner', 'Workout')
    defaults = [
        ('Morning Run', 'Steady cardio to start the day.', 30),
        ('Full Body Strength', 'Compound lifts: squats, presses, rows.', 45),
        ('HIIT Circuit', 'High-intensity intervals with short rest.', 25),
        ('Yoga & Mobility', 'Stretching and core stability.', 40),
        ('Cycling Session', 'Indoor or outdoor moderate ride.', 35),
    ]
    for name, description, duration_min in defaults:
        Workout.objects.get_or_create(
            name=name,
            defaults={'description': description, 'duration_min': duration_min},
        )


def unseed_workouts(apps, schema_editor):
    Workout = apps.get_model('planner', 'Workout')
    names = [
        'Morning Run',
        'Full Body Strength',
        'HIIT Circuit',
        'Yoga & Mobility',
        'Cycling Session',
    ]
    Workout.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_workouts, unseed_workouts),
    ]
