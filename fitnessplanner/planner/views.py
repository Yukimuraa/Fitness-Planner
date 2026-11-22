from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Meal,
    MealItem,
    Workout,
    WorkoutSchedule,
    MembershipPackage,
    UserMembership,
    Instructor,
    InstructorBooking,
    InstructorAssignment,
    InstructorAvailability,
    InstructorUnavailableDate,
    SessionCreditTransaction,
    WorkoutPlan,
    FitnessAssessment,
    InstructorNote,
    Notification,
)
from .forms import MealForm, WorkoutForm, ScheduleForm, InstructorBookingForm, InstructorForm
from fitnessplanner.accounts.models import UserProfile, ProgressEntry
from fitnessplanner.accounts.forms import ProgressEntryForm
from fitnessplanner.planner.meal_generator import generate_meal_plan
from fitnessplanner.planner.fitness_engine import (
    analyze_workout_imbalance,
    generate_fitness_recommendation,
    analyze_meal_health,
)


def _sync_expired_memberships(user=None):
    """Automatically mark active memberships past their end_date as expired."""
    qs = UserMembership.objects.filter(status='active', end_date__lt=date.today())
    if user is not None:
        qs = qs.filter(user=user)
    qs.update(status='expired')


def index(request):
    """Landing / dashboard page.

    Authenticated users see their personalized dashboard with health metrics,
    personalized meal recommendations, and weight logs.
    Anonymous users see a marketing-style landing page.
    """
    if not request.user.is_authenticated:
        return render(request, 'planner/landing.html')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_instructor_role() and not request.user.is_staff:
        return redirect('planner:instructor_dashboard')

    # Handle inline progress weight logging
    progress_form = None
    if request.method == 'POST' and 'log_weight' in request.POST:
        progress_form = ProgressEntryForm(request.POST)
        if progress_form.is_valid():
            entry = progress_form.save(commit=False)
            entry.user = request.user
            entry.save()
            
            # Update user profile's current weight to keep it in sync
            profile.weight_kg = entry.weight_kg
            profile.save()
            return redirect('planner:index')
    else:
        progress_form = ProgressEntryForm(initial={'recorded_at': date.today()})

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    upcoming = (
        WorkoutSchedule.objects
        .filter(user=request.user, date__gte=today)
        .order_by('date')[:5]
    )
    week_schedules = WorkoutSchedule.objects.filter(
        user=request.user,
        date__gte=week_start,
        date__lte=week_end,
    )

    completed_count = week_schedules.filter(completed=True).count()
    total_count = week_schedules.count()
    completion_pct = int((completed_count / total_count) * 100) if total_count else 0
    week_minutes = sum(s.workout.duration_min for s in week_schedules.filter(completed=True))

    meals = Meal.objects.all()[:6]
    meal_calories = (
        MealItem.objects.aggregate(total=Sum('calories'))['total'] or 0
    )

    # Health & Meal Recommendation Metrics
    meal_plan_data = generate_meal_plan(profile)
    recent_progress = ProgressEntry.objects.filter(user=request.user).order_by('-recorded_at', '-created_at')[:5]

    # Calculate weight change progress
    starting_entry = ProgressEntry.objects.filter(user=request.user).order_by('recorded_at', 'created_at').first()
    starting_weight = starting_entry.weight_kg if starting_entry else profile.weight_kg
    current_weight = profile.weight_kg
    
    weight_change = None
    if starting_weight and current_weight:
        weight_change = round(current_weight - starting_weight, 1)

    _sync_expired_memberships(request.user)
    active_membership = (
        UserMembership.objects
        .filter(user=request.user, status='active', end_date__gte=today)
        .select_related('package')
        .first()
    )
    upcoming_bookings = (
        InstructorBooking.objects
        .filter(user=request.user, status__in=['pending', 'confirmed', 'reschedule_requested'], session_date__gte=today)
        .select_related('instructor')[:5]
    )
    assigned_workout_plans = (
        WorkoutPlan.objects
        .filter(member=request.user, is_active=True)
        .select_related('instructor')
        .prefetch_related('exercises')[:3]
    )
    instructor_notes = (
        InstructorNote.objects
        .filter(member=request.user, visible_to_member=True)
        .select_related('instructor')[:5]
    )
    member_assessments = (
        FitnessAssessment.objects
        .filter(member=request.user)
        .select_related('instructor')[:3]
    )
    notifications = Notification.objects.filter(user=request.user)[:6]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    imbalance_report = analyze_workout_imbalance(request.user, profile)
    fitness_suggestion = generate_fitness_recommendation(request.user, profile)

    context = {
        'profile': profile,
        'bmi_score': profile.bmi(),
        'bmi_category': profile.bmi_category(),
        'calorie_recommendation': profile.daily_calorie_recommendation(),
        'water_liters': profile.water_recommendation_liters(),
        'water_glasses': profile.water_recommendation_glasses(),
        'meal_plan': meal_plan_data,
        'recent_progress': recent_progress,
        'starting_weight': starting_weight,
        'current_weight': current_weight,
        'weight_change': weight_change,
        'progress_form': progress_form,
        'active_membership': active_membership,
        'upcoming_bookings': upcoming_bookings,
        'assigned_workout_plans': assigned_workout_plans,
        'instructor_notes': instructor_notes,
        'member_assessments': member_assessments,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'imbalance_report': imbalance_report,
        'fitness_suggestion': fitness_suggestion,
        
        'upcoming': upcoming,
        'completed_count': completed_count,
        'total_count': total_count,
        'completion_pct': completion_pct,
        'week_minutes': week_minutes,
        'meals': meals,
        'workouts': Workout.objects.all()[:6],
        'meal_calories': meal_calories,
    }
    return render(request, 'planner/index.html', context)


@login_required
def meal_list(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    meals = Meal.objects.all().order_by('meal_type', 'name')
    meal_rows = []
    for meal in meals:
        analysis = analyze_meal_health(meal, profile)
        meal_rows.append({'meal': meal, 'analysis': analysis})
    return render(request, 'planner/meals_list.html', {
        'meals': meals,
        'meal_rows': meal_rows,
        'profile': profile,
    })


@login_required
def meal_create(request):
    if request.method == 'POST':
        form = MealForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('planner:meal_list')
    else:
        form = MealForm()
    return render(request, 'planner/meal_form.html', {'form': form, 'title': 'Add Meal'})


@login_required
def meal_edit(request, pk):
    meal = get_object_or_404(Meal, pk=pk)
    if request.method == 'POST':
        form = MealForm(request.POST, instance=meal)
        if form.is_valid():
            form.save()
            return redirect('planner:meal_list')
    else:
        form = MealForm(instance=meal)
    return render(request, 'planner/meal_form.html', {'form': form, 'title': 'Edit Meal'})


@login_required
def meal_delete(request, pk):
    meal = get_object_or_404(Meal, pk=pk)
    if request.method == 'POST':
        meal.delete()
        return redirect('planner:meal_list')
    return render(request, 'planner/confirm_delete.html', {'object': meal, 'type': 'Meal'})


@login_required
def workout_list(request):
    workouts = Workout.objects.all()
    return render(request, 'planner/workouts_list.html', {'workouts': workouts})


@login_required
def workout_create(request):
    if request.method == 'POST':
        form = WorkoutForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('planner:workout_list')
    else:
        form = WorkoutForm()
    return render(request, 'planner/workout_form.html', {'form': form, 'title': 'Add Workout'})


@login_required
def workout_edit(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == 'POST':
        form = WorkoutForm(request.POST, instance=workout)
        if form.is_valid():
            form.save()
            return redirect('planner:workout_list')
    else:
        form = WorkoutForm(instance=workout)
    return render(request, 'planner/workout_form.html', {'form': form, 'title': 'Edit Workout'})


@login_required
def workout_delete(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == 'POST':
        workout.delete()
        return redirect('planner:workout_list')
    return render(request, 'planner/confirm_delete.html', {'object': workout, 'type': 'Workout'})


@login_required
def schedule_list(request):
    schedules = WorkoutSchedule.objects.filter(user=request.user).order_by('date')
    return render(request, 'planner/schedule_list.html', {'schedules': schedules})


@login_required
def schedule_create(request):
    has_workouts = Workout.objects.exists()
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            sched = form.save(commit=False)
            sched.user = request.user
            sched.save()
            return redirect('planner:schedule_list')
    else:
        form = ScheduleForm()
    return render(request, 'planner/schedule_form.html', {
        'form': form,
        'title': 'Schedule Workout',
        'has_workouts': has_workouts,
    })


@login_required
def schedule_toggle(request, pk):
    """Mark a scheduled workout as complete / incomplete."""
    sched = get_object_or_404(WorkoutSchedule, pk=pk, user=request.user)
    if request.method == 'POST':
        sched.completed = not sched.completed
        sched.save()
    return redirect('planner:schedule_list')


def admin_login(request):
    """Dedicated login page for staff/admin users — goes straight to Admin Dashboard."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('planner:admin_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                return redirect('planner:admin_dashboard')
            else:
                error = 'This account does not have admin/staff permissions.'
        else:
            error = 'Invalid admin username or password.'

    return render(request, 'planner/admin_login.html', {'error': error})


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_dashboard(request):
    """Custom admin dashboard for staff members — user statistics and directory."""
    from django.db.models import Avg, Count

    all_profiles = UserProfile.objects.select_related('user').all()

    # Annotate each profile with computed properties
    user_rows = []
    for p in all_profiles:
        user_rows.append({
            'user': p.user,
            'profile': p,
            'bmi': p.bmi(),
            'bmi_category': p.bmi_category(),
            'calories': p.daily_calorie_recommendation(),
        })

    # Aggregate stats
    total_users = len(user_rows)
    ages = [p.age for p in all_profiles if p.age]
    weights = [p.weight_kg for p in all_profiles if p.weight_kg]
    bmis = [p.bmi() for p in all_profiles if p.bmi()]

    avg_age = round(sum(ages) / len(ages), 1) if ages else None
    avg_weight = round(sum(weights) / len(weights), 1) if weights else None
    avg_bmi = round(sum(bmis) / len(bmis), 1) if bmis else None

    # Goal breakdown
    goal_choices = [
        ('lose_weight', 'Lose Weight'),
        ('build_muscle', 'Build Muscle'),
        ('maintain_weight', 'Maintain Weight'),
        ('improve_fitness', 'Improve Fitness'),
        ('', 'Not Selected'),
    ]
    goal_counts = {}
    for code, label in goal_choices:
        count = sum(1 for p in all_profiles if p.fitness_goal == code)
        goal_counts[label] = count

    # BMI category breakdown
    bmi_labels = ['Underweight', 'Normal Weight', 'Overweight', 'Obese', '\u2014']
    bmi_counts = {}
    for label in bmi_labels:
        if label == '\u2014':
            count = sum(1 for p in all_profiles if p.bmi() is None)
        else:
            count = sum(1 for p in all_profiles if p.bmi_category() == label)
        bmi_counts[label] = count

    _sync_expired_memberships()
    pending_memberships = (
        UserMembership.objects
        .filter(status='pending')
        .select_related('user', 'package')
        .order_by('-created_at')
    )
    all_memberships = (
        UserMembership.objects
        .select_related('user', 'package')
        .order_by('-created_at')[:25]
    )

    members_list = User.objects.filter(is_staff=False, is_superuser=False).exclude(
        userprofile__role='instructor'
    ).order_by('username')
    assignments = InstructorAssignment.objects.filter(is_active=True).select_related('instructor', 'member')
    all_bookings = InstructorBooking.objects.select_related('instructor', 'user').order_by('-session_date', '-created_at')[:20]

    context = {
        'user_rows': user_rows,
        'total_users': total_users,
        'avg_age': avg_age,
        'avg_weight': avg_weight,
        'avg_bmi': avg_bmi,
        'goal_counts': goal_counts,
        'bmi_counts': bmi_counts,
        'instructors': Instructor.objects.select_related('user').all().order_by('-is_active', 'name'),
        'instructor_form': InstructorForm(),
        'pending_memberships': pending_memberships,
        'all_memberships': all_memberships,
        'members_list': members_list,
        'assignments': assignments,
        'all_bookings': all_bookings,
        'instructors_count': Instructor.objects.count(),
        'pending_memberships_count': pending_memberships.count(),
        'assignments_count': assignments.count(),
    }
    return render(request, 'planner/admin_dashboard.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_analytics(request):
    """Dedicated Admin page: Goals & BMI Analytics."""
    all_profiles = UserProfile.objects.select_related('user').all()
    total_users = all_profiles.count()
    goal_choices = [
        ('lose_weight', 'Lose Weight'),
        ('build_muscle', 'Build Muscle'),
        ('maintain_weight', 'Maintain Weight'),
        ('improve_fitness', 'Improve Fitness'),
        ('', 'Not Selected'),
    ]
    goal_counts = {label: sum(1 for p in all_profiles if p.fitness_goal == code) for code, label in goal_choices}
    bmi_labels = ['Underweight', 'Normal Weight', 'Overweight', 'Obese', '\u2014']
    bmi_counts = {}
    for label in bmi_labels:
        if label == '\u2014':
            bmi_counts[label] = sum(1 for p in all_profiles if p.bmi() is None)
        else:
            bmi_counts[label] = sum(1 for p in all_profiles if p.bmi_category() == label)
    return render(request, 'planner/admin_analytics.html', {
        'total_users': total_users,
        'goal_counts': goal_counts,
        'bmi_counts': bmi_counts,
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_users(request):
    """Dedicated Admin page: User Directory."""
    all_profiles = UserProfile.objects.select_related('user').all().order_by('user__username')
    user_rows = [{
        'user': p.user,
        'profile': p,
        'bmi': p.bmi(),
        'bmi_category': p.bmi_category(),
        'calories': p.daily_calorie_recommendation(),
    } for p in all_profiles]
    return render(request, 'planner/admin_users.html', {
        'user_rows': user_rows,
        'total_users': len(user_rows),
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_memberships(request):
    """Dedicated Admin page: Membership & Payment Requests."""
    _sync_expired_memberships()
    pending_memberships = UserMembership.objects.filter(status='pending').select_related('user', 'package').order_by('-created_at')
    all_memberships = UserMembership.objects.select_related('user', 'package').order_by('-created_at')[:50]
    return render(request, 'planner/admin_memberships.html', {
        'pending_memberships': pending_memberships,
        'all_memberships': all_memberships,
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructor_new(request):
    """Dedicated Admin page: Add New Instructor."""
    return render(request, 'planner/admin_instructor_add.html', {
        'instructor_form': InstructorForm(),
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructors(request):
    """Dedicated Admin page: Manage Instructors."""
    instructors = Instructor.objects.select_related('user').all().order_by('-is_active', 'name')
    return render(request, 'planner/admin_instructors.html', {
        'instructors': instructors,
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_assignments(request):
    """Dedicated Admin page: Member-to-Instructor Assignments."""
    members_list = User.objects.filter(is_staff=False, is_superuser=False).exclude(
        userprofile__role='instructor'
    ).order_by('username')
    instructors = Instructor.objects.filter(status='active').order_by('name')
    assignments = InstructorAssignment.objects.filter(is_active=True).select_related('instructor', 'member')
    return render(request, 'planner/admin_assignments.html', {
        'members_list': members_list,
        'instructors': instructors,
        'assignments': assignments,
    })


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_membership_approve(request, pk):
    """Approve a pending paid membership request and activate its features."""
    if request.method == 'POST':
        req = get_object_or_404(UserMembership, pk=pk)
        if req.status != 'pending':
            messages.info(request, f'Membership request #{req.pk} is already {req.get_status_display()}.')
            return redirect('planner:admin_dashboard')

        today = date.today()
        # Cancel any prior active membership for this user when activating the approved one
        UserMembership.objects.filter(user=req.user, status='active').exclude(pk=req.pk).update(status='cancelled')
        req.status = 'active'
        req.payment_status = 'approved'
        req.start_date = today
        req.end_date = today + timedelta(days=req.package.duration_days)
        req.sessions_remaining = req.package.included_instructor_sessions
        req.reviewed_at = timezone.now()
        req.admin_notes = request.POST.get('admin_notes', '').strip()[:255]
        req.save()
        messages.success(
            request,
            f'Approved {req.package.name} (₱{req.amount_php:,.0f}) for {req.user.username}.'
        )
    return redirect('planner:admin_memberships')


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_membership_reject(request, pk):
    """Reject a pending paid membership request without unlocking premium features."""
    if request.method == 'POST':
        req = get_object_or_404(UserMembership, pk=pk)
        if req.status != 'pending':
            messages.info(request, f'Membership request #{req.pk} is already {req.get_status_display()}.')
            return redirect('planner:admin_dashboard')

        req.status = 'rejected'
        req.payment_status = 'rejected'
        req.sessions_remaining = 0
        req.reviewed_at = timezone.now()
        req.admin_notes = request.POST.get('admin_notes', '').strip()[:255]
        req.save()
        messages.warning(request, f'Rejected {req.package.name} request for {req.user.username}.')
    return redirect('planner:admin_memberships')


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructor_create(request):
    """Admin creates an Instructor account + secure login credentials (temporary password)."""
    if request.method == 'POST':
        import secrets
        from datetime import datetime as dt
        form = InstructorForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            raw_username = form.cleaned_data.get('username', '').strip()
            if not raw_username:
                base = ''.join(ch for ch in inst.name.lower() if ch.isalnum())[:12] or 'instructor'
                raw_username = f"{base}_{secrets.token_hex(2)}"
            if User.objects.filter(username=raw_username).exists():
                messages.error(request, f'Username "{raw_username}" is already taken.')
                return redirect('planner:admin_dashboard')

            temp_password = form.cleaned_data.get('temporary_password', '').strip() or secrets.token_urlsafe(8)
            user = User.objects.create_user(
                username=raw_username,
                email=inst.email,
                password=temp_password,
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'instructor'
            profile.must_change_password = True
            profile.save()

            inst.user = user
            inst.save()

            # Seed default Mon/Wed/Fri morning/afternoon slots so instructor is immediately bookable
            for day in (0, 2, 4):
                for s_str, e_str, label in InstructorAvailability.DEFAULT_SLOTS[:6]:
                    InstructorAvailability.objects.get_or_create(
                        instructor=inst,
                        day_of_week=day,
                        start_time=dt.strptime(s_str, '%H:%M').time(),
                        end_time=dt.strptime(e_str, '%H:%M').time(),
                        defaults={'time_slot_label': label, 'is_active': True},
                    )

            messages.success(
                request,
                f'Instructor "{inst.name}" created! Login Username: {raw_username} | Temporary Password: {temp_password}'
            )
            return redirect('planner:admin_instructors')
        else:
            messages.error(request, 'Please check the instructor details and try again.')
    return redirect('planner:admin_instructor_new')


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructor_edit(request, pk):
    """Admin edits an existing Instructor's details and status."""
    inst = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            updated = form.save()
            if updated.user:
                updated.user.email = updated.email
                updated.user.is_active = (updated.status == 'active')
                updated.user.save()
            messages.success(request, f'Updated instructor "{updated.name}".')
            return redirect('planner:admin_instructors')
    else:
        form = InstructorForm(instance=inst)
    return render(request, 'planner/admin_instructor_edit.html', {'form': form, 'instructor': inst})


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructor_toggle(request, pk):
    """Toggle an instructor's active/inactive status from the admin dashboard."""
    if request.method == 'POST':
        inst = get_object_or_404(Instructor, pk=pk)
        inst.status = 'inactive' if inst.status == 'active' else 'active'
        inst.save()
        if inst.user:
            inst.user.is_active = (inst.status == 'active')
            inst.user.save()
        status_text = 'activated' if inst.status == 'active' else 'deactivated'
        messages.info(request, f'Instructor "{inst.name}" {status_text}.')
    return redirect('planner:admin_instructors')


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_assign_member(request):
    """Admin assigns or reassigns a Member to an Instructor."""
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        instructor_id = request.POST.get('instructor_id')
        notes = request.POST.get('notes', '').strip()[:300]
        member = get_object_or_404(User, pk=member_id)
        instructor = get_object_or_404(Instructor, pk=instructor_id)

        # Deactivate prior active assignments for this member if reassigning
        InstructorAssignment.objects.filter(member=member, is_active=True).update(is_active=False)
        InstructorAssignment.objects.create(
            instructor=instructor,
            member=member,
            assigned_by=request.user,
            notes=notes,
            is_active=True,
        )
        if instructor.user:
            Notification.objects.create(
                user=instructor.user,
                title='New Member Assigned',
                message=f'Admin assigned member {member.username} to you.',
                notification_type='assignment',
                link_url='/instructor/members/',
            )
        Notification.objects.create(
            user=member,
            title='Instructor Assigned',
            message=f'You have been assigned to {instructor.name} ({instructor.specialty}).',
            notification_type='assignment',
            link_url='/instructors/',
        )
        messages.success(request, f'Assigned {member.username} to {instructor.name}.')
    return redirect('planner:admin_assignments')


@user_passes_test(lambda u: u.is_staff, login_url='planner:admin_login')
def admin_instructor_delete(request, pk):
    """Delete an instructor from the admin dashboard."""
    if request.method == 'POST':
        inst = get_object_or_404(Instructor, pk=pk)
        name = inst.name
        inst.delete()
        messages.info(request, f'Instructor "{name}" removed.')
    return redirect('planner:admin_instructors')


@login_required
def meal_health_check(request, pk=None):
    """Analyze a chosen meal for allergies, health conditions, and goal fit."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    all_meals = Meal.objects.all().order_by('meal_type', 'name')

    selected_meal = None
    if pk is not None:
        selected_meal = get_object_or_404(Meal, pk=pk)
    elif request.GET.get('meal_id'):
        selected_meal = Meal.objects.filter(pk=request.GET.get('meal_id')).first()
    if selected_meal is None:
        selected_meal = all_meals.first()

    analysis = analyze_meal_health(selected_meal, profile) if selected_meal else None

    return render(request, 'planner/meal_health_check.html', {
        'profile': profile,
        'all_meals': all_meals,
        'selected_meal': selected_meal,
        'analysis': analysis,
    })


@login_required
def membership_list(request):
    """Browse membership & bundle packages and manage active/pending subscriptions."""
    today = date.today()
    _sync_expired_memberships(request.user)
    packages = MembershipPackage.objects.filter(is_active=True)
    active_membership = (
        UserMembership.objects
        .filter(user=request.user, status='active', end_date__gte=today)
        .select_related('package')
        .first()
    )
    pending_membership = (
        UserMembership.objects
        .filter(user=request.user, status='pending')
        .select_related('package')
        .first()
    )
    history = (
        UserMembership.objects
        .filter(user=request.user)
        .select_related('package')[:15]
    )
    return render(request, 'planner/memberships.html', {
        'packages': packages,
        'active_membership': active_membership,
        'pending_membership': pending_membership,
        'history': history,
    })


@login_required
def membership_subscribe(request, pk):
    """Activate Starter Basic immediately, or submit a pending payment request for paid packages."""
    if request.method == 'POST':
        package = get_object_or_404(MembershipPackage, pk=pk, is_active=True)
        today = date.today()
        _sync_expired_memberships(request.user)

        # Prevent duplicate active subscription for the same package
        existing_active = UserMembership.objects.filter(
            user=request.user,
            package=package,
            status='active',
            end_date__gte=today,
        ).first()
        if existing_active:
            messages.info(request, f'You already have an active {package.name} membership.')
            return redirect('planner:membership_list')

        # Prevent duplicate pending payment request from repeated clicks
        existing_pending = UserMembership.objects.filter(
            user=request.user,
            package=package,
            status='pending',
        ).first()
        if existing_pending:
            messages.info(request, f'You already have a pending payment request for {package.name}.')
            return redirect('planner:membership_list')

        if package.price == 0:
            # Starter Basic activates immediately
            UserMembership.objects.filter(user=request.user, status='active').update(status='cancelled')
            UserMembership.objects.create(
                user=request.user,
                package=package,
                start_date=today,
                end_date=today + timedelta(days=package.duration_days),
                status='active',
                payment_status='not_required',
                amount_php=0,
                sessions_remaining=package.included_instructor_sessions,
            )
            messages.success(request, f'{package.name} activated for {package.duration_days} days!')
        else:
            # Paid package creates a pending payment request; premium features stay locked until approved
            ref = request.POST.get('payment_reference', '').strip()[:120]
            UserMembership.objects.create(
                user=request.user,
                package=package,
                start_date=today,
                end_date=today + timedelta(days=package.duration_days),
                status='pending',
                payment_status='pending',
                amount_php=package.price,
                payment_reference=ref or f'REQ-{request.user.id}-{today.strftime("%Y%m%d")}',
                sessions_remaining=0,
            )
            messages.info(
                request,
                f'Payment request for {package.name} (₱{package.price:,.0f}) submitted! '
                'Premium features will unlock once an admin approves your payment.'
            )
    return redirect('planner:membership_list')


@login_required
def membership_cancel(request, pk):
    """Cancel an active or pending membership."""
    membership = get_object_or_404(UserMembership, pk=pk, user=request.user)
    if request.method == 'POST' and membership.status in ('active', 'pending'):
        membership.status = 'cancelled'
        membership.save()
        messages.info(request, f'Your {membership.package.name} membership has been cancelled.')
    return redirect('planner:membership_list')


@login_required
def instructor_list(request):
    """Browse instructors, submit Pending coaching booking requests, and manage bookings."""
    today = timezone.localdate()
    _sync_expired_memberships(request.user)
    instructors = Instructor.objects.filter(status='active').prefetch_related('availability_slots').order_by('-rating', 'name')
    active_membership = (
        UserMembership.objects
        .filter(user=request.user, status='active', end_date__gte=today)
        .select_related('package')
        .first()
    )

    if request.method == 'POST':
        form = InstructorBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            inst = booking.instructor
            s_date = booking.session_date
            t_slot = booking.time_slot

            # 1. Validate date is not in the past
            if s_date < today:
                messages.error(request, 'Booking date cannot be in the past.')
                return redirect('planner:instructor_list')

            # 2. Validate membership eligibility & coaching credits
            if not active_membership or active_membership.sessions_remaining <= 0:
                messages.error(
                    request,
                    'You need an active membership with remaining coaching session credits to book an instructor.'
                )
                return redirect('planner:instructor_list')

            # 3. Validate instructor unavailable dates / blocked times
            blocked = InstructorUnavailableDate.objects.filter(instructor=inst, date=s_date)
            if blocked.filter(is_full_day=True).exists() or blocked.filter(blocked_time_slot=t_slot).exists():
                messages.error(request, f'{inst.name} is unavailable on {s_date} ({t_slot}). Please pick another date or time.')
                return redirect('planner:instructor_list')

            # 4. Validate instructor weekly availability if configured
            weekday = s_date.weekday()
            inst_slots = InstructorAvailability.objects.filter(instructor=inst, is_active=True)
            if inst_slots.exists():
                day_slots = inst_slots.filter(day_of_week=weekday)
                if not day_slots.exists() or not day_slots.filter(time_slot_label=t_slot).exists():
                    messages.error(
                        request,
                        f'{inst.name} does not have "{t_slot}" open on {s_date.strftime("%A")}s. Please check their schedule.'
                    )
                    return redirect('planner:instructor_list')

            # 5. Prevent overlapping / duplicate bookings (same instructor+slot OR same member+slot)
            inst_conflict = InstructorBooking.objects.filter(
                instructor=inst,
                session_date=s_date,
                time_slot=t_slot,
                status__in=['pending', 'confirmed'],
            ).exists()
            if inst_conflict:
                messages.error(request, f'{inst.name} already has a booking for {s_date} at {t_slot}.')
                return redirect('planner:instructor_list')

            member_conflict = InstructorBooking.objects.filter(
                user=request.user,
                session_date=s_date,
                time_slot=t_slot,
                status__in=['pending', 'confirmed'],
            ).exists()
            if member_conflict:
                messages.error(request, f'You already have a booking on {s_date} at {t_slot}.')
                return redirect('planner:instructor_list')

            # 6. Save with Pending status (do NOT deduct credit until confirmed/completed)
            booking.status = 'pending'
            booking.membership = active_membership
            booking.used_package_session = True
            booking.credit_reserved = False
            booking.credit_deducted = False
            booking.save()

            if inst.user:
                Notification.objects.create(
                    user=inst.user,
                    title='New Coaching Booking Request',
                    message=f'{request.user.username} requested a session on {s_date} ({t_slot}).',
                    notification_type='booking_request',
                    link_url='/instructor/appointments/',
                )
            messages.success(
                request,
                f'Booking request sent to {inst.name} for {s_date} ({t_slot})! '
                'Status is Pending — credits are reserved only once the instructor accepts.'
            )
            return redirect('planner:instructor_list')
    else:
        initial = {'session_date': today + timedelta(days=1)}
        if request.GET.get('instructor_id'):
            initial['instructor'] = request.GET.get('instructor_id')
        form = InstructorBookingForm(initial=initial)

    bookings = (
        InstructorBooking.objects
        .filter(user=request.user)
        .select_related('instructor')
        .order_by('-session_date', '-created_at')
    )
    return render(request, 'planner/instructors.html', {
        'instructors': instructors,
        'form': form,
        'bookings': bookings,
        'active_membership': active_membership,
    })


@login_required
def instructor_booking_cancel(request, pk):
    """Cancel a pending, confirmed, or reschedule-requested session and release any reserved credit."""
    booking = get_object_or_404(InstructorBooking, pk=pk, user=request.user)
    if request.method == 'POST' and booking.status in ('pending', 'confirmed', 'reschedule_requested'):
        if booking.credit_reserved and not booking.credit_deducted and booking.membership:
            mem = booking.membership
            mem.sessions_remaining += 1
            mem.save()
            booking.credit_reserved = False
            SessionCreditTransaction.objects.create(
                user=request.user,
                membership=mem,
                booking=booking,
                action='release',
                credits_delta=1,
                balance_after=mem.sessions_remaining,
                note=f'Released reserved credit (cancelled by member)',
            )
        booking.status = 'cancelled'
        booking.save()
        if booking.instructor.user:
            Notification.objects.create(
                user=booking.instructor.user,
                title='Booking Cancelled',
                message=f'{request.user.username} cancelled their booking for {booking.session_date} ({booking.time_slot}).',
                notification_type='booking_cancelled',
                link_url='/instructor/appointments/',
            )
        messages.info(request, 'Coaching session cancelled.')
    return redirect('planner:instructor_list')


@login_required
def smart_suggestions(request):
    """Smart Fitness Coach: Workout Imbalance Detector & Profile-Based Fitness System."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    imbalance_report = analyze_workout_imbalance(request.user, profile)
    fitness_suggestion = generate_fitness_recommendation(request.user, profile)
    return render(request, 'planner/suggestions.html', {
        'profile': profile,
        'imbalance_report': imbalance_report,
        'fitness_suggestion': fitness_suggestion,
    })


@login_required
def quick_schedule_workout(request, workout_id):
    """1-click schedule a recommended workout for today or tomorrow."""
    if request.method == 'POST':
        workout = get_object_or_404(Workout, pk=workout_id)
        target_date = date.today() + timedelta(days=1)
        WorkoutSchedule.objects.create(
            user=request.user,
            workout=workout,
            date=target_date,
        )
        messages.success(request, f'Added "{workout.name}" to your schedule for {target_date.strftime("%b %d, %Y")}!')
    next_url = request.POST.get('next') or 'planner:smart_suggestions'
    return redirect(next_url)

