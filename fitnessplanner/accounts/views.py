from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import (
    UserProfile,
    ProgressEntry,
    Allergen,
    MemberAllergy,
    FoodIntolerance,
    MemberIntolerance,
    DietaryPreferenceOption,
    MemberDietaryProfile,
)
from .forms import RegistrationForm, ProgressEntryForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    recent_progress = ProgressEntry.objects.filter(user=request.user)[:5]
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'recent_progress': recent_progress,
    })


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:select_goal')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def select_goal(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        goal = request.POST.get('fitness_goal')
        valid_goals = [choice[0] for choice in UserProfile.FITNESS_GOAL_CHOICES if choice[0]]
        if goal in valid_goals:
            profile.fitness_goal = goal
            profile.save()
            if goal == 'build_muscle':
                return redirect('accounts:select_muscle_groups')
            return redirect('accounts:allergy_assessment')
        else:
            error = "Please select a valid fitness goal."
            return render(request, 'accounts/select_goal.html', {
                'profile': profile,
                'error': error,
                'goals': UserProfile.FITNESS_GOAL_CHOICES[1:]
            })
            
    return render(request, 'accounts/select_goal.html', {
        'profile': profile,
        'goals': UserProfile.FITNESS_GOAL_CHOICES[1:]
    })


@login_required
def select_muscle_groups(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Enforce that fitness goal is build_muscle
    if profile.fitness_goal != 'build_muscle':
        return redirect('accounts:select_goal')
        
    if request.method == 'POST':
        selected_muscles = request.POST.getlist('muscle_groups')
        valid_slugs = list(UserProfile.MUSCLE_GROUPS.keys())
        cleaned_selections = [m for m in selected_muscles if m in valid_slugs]
        
        if cleaned_selections:
            profile.focused_muscles = ",".join(cleaned_selections)
            profile.save()
            return redirect('accounts:allergy_assessment')
        else:
            error = "Please select at least one muscle group to focus on."
            # Render with error
            muscle_list = []
            for slug, info in UserProfile.MUSCLE_GROUPS.items():
                muscle_list.append({
                    'slug': slug,
                    'name': info['name'],
                    'subtitle': info['subtitle'],
                    'desc': info['desc'],
                    'image': info['image'],
                    'is_selected': False
                })
            return render(request, 'accounts/select_muscle_groups.html', {
                'profile': profile,
                'muscle_groups': muscle_list,
                'error': error,
            })
            
    # GET: render selection list
    current_selected = profile.get_focused_muscles_list()
    muscle_list = []
    for slug, info in UserProfile.MUSCLE_GROUPS.items():
        muscle_list.append({
            'slug': slug,
            'name': info['name'],
            'subtitle': info['subtitle'],
            'desc': info['desc'],
            'image': info['image'],
            'is_selected': slug in current_selected
        })
        
    return render(request, 'accounts/select_muscle_groups.html', {
        'profile': profile,
        'muscle_groups': muscle_list,
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if user.is_staff or user.is_superuser or profile.role == 'admin':
                return redirect('planner:admin_dashboard')
            if profile.role == 'instructor' or hasattr(user, 'instructor_profile'):
                if profile.must_change_password:
                    return redirect('accounts:force_password_change')
                return redirect('planner:instructor_dashboard')
            return redirect('planner:index')
    else:
        form = AuthenticationForm(request)
    return render(request, 'registration/login.html', {'form': form})


@login_required
def force_password_change(request):
    """Require instructors (or flagged users) to change their temporary password on first login."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            profile.must_change_password = False
            profile.save()
            messages.success(request, 'Password updated! Welcome to your FitLife dashboard.')
            if profile.is_instructor_role():
                return redirect('planner:instructor_dashboard')
            if profile.is_admin_role():
                return redirect('planner:admin_dashboard')
            return redirect('planner:index')
    else:
        form = SetPasswordForm(request.user)
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    return render(request, 'accounts/force_password_change.html', {'form': form})


@login_required
def edit_profile(request):
    from .forms import ProfileForm, UserProfileForm
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        uform = ProfileForm(request.POST, instance=user)
        pform = UserProfileForm(request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            return redirect('accounts:profile')
    else:
        uform = ProfileForm(instance=user)
        pform = UserProfileForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {'uform': uform, 'pform': pform})


@login_required
def progress_list(request):
    entries = ProgressEntry.objects.filter(user=request.user)
    if request.method == 'POST':
        form = ProgressEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect('accounts:progress')
    else:
        form = ProgressEntryForm(initial={'recorded_at': date.today()})
    return render(request, 'accounts/progress.html', {
        'entries': entries,
        'form': form,
    })


@login_required
def progress_delete(request, pk):
    entry = get_object_or_404(ProgressEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect('accounts:progress')


@login_required
def allergy_assessment(request):
    """Step 4 of 5: Allergy & Dietary Assessment (also editable later from Profile)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    diet_profile, _ = MemberDietaryProfile.objects.get_or_create(user=request.user)

    all_allergens = list(Allergen.objects.all())
    all_intolerances = list(FoodIntolerance.objects.all())
    all_diet_prefs = list(DietaryPreferenceOption.objects.all())

    edit_mode = request.GET.get('from') == 'profile' or request.POST.get('from') == 'profile'
    back_url = 'accounts:profile' if edit_mode else (
        'accounts:select_muscle_groups' if profile.fitness_goal == 'build_muscle' else 'accounts:select_goal'
    )

    error = None
    if request.method == 'POST':
        no_allergies = request.POST.get('no_known_allergies') == 'on'
        selected_allergen_slugs = request.POST.getlist('allergens')
        other_allergy_name = request.POST.get('other_allergy_name', '').strip()[:120]
        allergy_severity = request.POST.get('allergy_severity', '').strip()[:255]

        no_intolerances = request.POST.get('no_known_intolerances') == 'on'
        selected_intolerance_slugs = request.POST.getlist('intolerances')
        other_intolerance_name = request.POST.get('other_intolerance_name', '').strip()[:120]

        selected_diet_slugs = request.POST.getlist('dietary_preferences')
        other_restrictions = request.POST.get('other_restrictions', '').strip()[:1000]

        # Validation
        if no_allergies and selected_allergen_slugs:
            error = 'Please either select "No known food allergies" OR choose specific allergies, not both.'
        elif not no_allergies and not selected_allergen_slugs:
            error = 'Please select your food allergies or check "No known food allergies".'
        elif 'other' in selected_allergen_slugs and not other_allergy_name:
            error = 'Please specify your additional allergy in the "Other allergy" field.'
        elif no_intolerances and selected_intolerance_slugs:
            error = 'Please either select "None / Not sure" for intolerances OR choose specific intolerances, not both.'
        elif 'other' in selected_intolerance_slugs and not other_intolerance_name:
            error = 'Please specify your additional food intolerance.'

        if not error:
            # Save normalized MemberAllergy records
            MemberAllergy.objects.filter(user=request.user).delete()
            diet_profile.no_known_allergies = no_allergies
            if not no_allergies:
                valid_allergens = {a.slug: a for a in all_allergens}
                for slug in selected_allergen_slugs:
                    if slug in valid_allergens:
                        MemberAllergy.objects.create(
                            user=request.user,
                            allergen=valid_allergens[slug],
                            custom_name=other_allergy_name if slug == 'other' else '',
                            severity_notes=allergy_severity,
                        )

            # Save normalized MemberIntolerance records
            MemberIntolerance.objects.filter(user=request.user).delete()
            diet_profile.no_known_intolerances = no_intolerances
            if not no_intolerances:
                valid_intols = {i.slug: i for i in all_intolerances}
                for slug in selected_intolerance_slugs:
                    if slug in valid_intols:
                        MemberIntolerance.objects.create(
                            user=request.user,
                            intolerance=valid_intols[slug],
                            custom_name=other_intolerance_name if slug == 'other' else '',
                        )

            # Save Dietary Preferences & Other Restrictions
            valid_prefs = {p.slug: p for p in all_diet_prefs}
            if 'none' in selected_diet_slugs and len(selected_diet_slugs) > 1:
                selected_diet_slugs = [s for s in selected_diet_slugs if s != 'none']
            chosen_pref_objs = [valid_prefs[s] for s in selected_diet_slugs if s in valid_prefs]
            diet_profile.dietary_preferences.set(chosen_pref_objs)
            diet_profile.other_restrictions = other_restrictions
            diet_profile.save()

            # Sync UserProfile legacy/summary fields for seamless compatibility
            slug_map = {
                'peanuts': 'nuts',
                'tree_nuts': 'nuts',
                'seafood': 'shellfish',
                'milk_dairy': 'dairy',
                'eggs': 'eggs',
                'soy': 'soy',
                'wheat': 'gluten',
            }
            synced_allergies = []
            if not no_allergies:
                for slug in selected_allergen_slugs:
                    mapped = slug_map.get(slug)
                    if mapped and mapped not in synced_allergies:
                        synced_allergies.append(mapped)
            profile.allergies = ','.join(synced_allergies)
            profile.custom_allergies = other_allergy_name if ('other' in selected_allergen_slugs and not no_allergies) else ''
            if chosen_pref_objs:
                first_slug = chosen_pref_objs[0].slug
                if first_slug in dict(UserProfile.DIETARY_PREFERENCE_CHOICES):
                    profile.dietary_preference = first_slug
            profile.save()

            if edit_mode:
                messages.success(request, 'Allergy & dietary assessment updated.')
                return redirect('accounts:profile')
            return redirect('accounts:onboarding_review')

    # Pre-populate current selections
    existing_allergies = list(MemberAllergy.objects.filter(user=request.user).select_related('allergen'))
    selected_allergen_slugs = [ma.allergen.slug for ma in existing_allergies]
    other_allergy_name = next((ma.custom_name for ma in existing_allergies if ma.allergen.slug == 'other'), '')
    allergy_severity = next((ma.severity_notes for ma in existing_allergies if ma.severity_notes), '')

    existing_intolerances = list(MemberIntolerance.objects.filter(user=request.user).select_related('intolerance'))
    selected_intolerance_slugs = [mi.intolerance.slug for mi in existing_intolerances]
    other_intolerance_name = next((mi.custom_name for mi in existing_intolerances if mi.intolerance.slug == 'other'), '')

    selected_diet_slugs = list(diet_profile.dietary_preferences.values_list('slug', flat=True))

    return render(request, 'accounts/allergy_assessment.html', {
        'profile': profile,
        'diet_profile': diet_profile,
        'all_allergens': all_allergens,
        'all_intolerances': all_intolerances,
        'all_diet_prefs': all_diet_prefs,
        'selected_allergen_slugs': selected_allergen_slugs,
        'other_allergy_name': other_allergy_name,
        'allergy_severity': allergy_severity,
        'selected_intolerance_slugs': selected_intolerance_slugs,
        'other_intolerance_name': other_intolerance_name,
        'selected_diet_slugs': selected_diet_slugs,
        'back_url': back_url,
        'edit_mode': edit_mode,
        'error': error,
    })


@login_required
def onboarding_review(request):
    """Step 5 of 5: Review & Complete onboarding before entering the dashboard."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    diet_profile, _ = MemberDietaryProfile.objects.get_or_create(user=request.user)
    member_allergies = MemberAllergy.objects.filter(user=request.user).select_related('allergen')
    member_intolerances = MemberIntolerance.objects.filter(user=request.user).select_related('intolerance')
    dietary_prefs = diet_profile.dietary_preferences.all()

    if request.method == 'POST':
        diet_profile.assessment_completed = True
        diet_profile.save()
        messages.success(request, 'Onboarding complete! Your personalized FitLife dashboard is ready.')
        return redirect('planner:index')

    return render(request, 'accounts/onboarding_review.html', {
        'profile': profile,
        'diet_profile': diet_profile,
        'member_allergies': member_allergies,
        'member_intolerances': member_intolerances,
        'dietary_prefs': dietary_prefs,
    })
