from django.shortcuts import redirect
from django.urls import resolve, Resolver404


class GoalSelectionMiddleware:
    """
    Middleware that:
    1. Enforces temporary password change on first login (e.g. admin-created instructors).
    2. Enforces member onboarding (fitness goal, muscle groups, allergy assessment)
       for regular members only — skipping Admin and Instructor roles.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'userprofile', None)
            try:
                resolved = resolve(request.path_info)
                full_view_name = resolved.view_name
            except Resolver404:
                full_view_name = ""

            is_static_or_admin = (
                request.path.startswith('/admin/')
                or request.path.startswith('/static/')
                or request.path.startswith('/media/')
            )
            if is_static_or_admin:
                return self.get_response(request)

            # 1. Force password change if flagged on first login
            if profile and profile.must_change_password:
                if full_view_name not in ('accounts:force_password_change', 'accounts:logout', 'logout'):
                    return redirect('accounts:force_password_change')
                return self.get_response(request)

            # 2. Skip member onboarding for Admin & Instructor roles
            is_admin_or_instructor = (
                request.user.is_staff
                or request.user.is_superuser
                or (profile and profile.role in ('admin', 'instructor'))
                or hasattr(request.user, 'instructor_profile')
            )
            if is_admin_or_instructor:
                return self.get_response(request)

            # 3. Member onboarding enforcement
            if profile:
                exempt_views = [
                    'accounts:select_goal',
                    'accounts:select_muscle_groups',
                    'accounts:allergy_assessment',
                    'accounts:onboarding_review',
                    'accounts:force_password_change',
                    'accounts:logout',
                    'logout',
                    'accounts:login',
                    'login',
                    'accounts:register',
                    'register',
                    'planner:admin_login',
                    'planner:admin_dashboard',
                ]
                if full_view_name not in exempt_views:
                    if not profile.fitness_goal:
                        return redirect('accounts:select_goal')
                    elif profile.fitness_goal == 'build_muscle' and not profile.focused_muscles:
                        return redirect('accounts:select_muscle_groups')
                    else:
                        from .models import MemberDietaryProfile
                        diet_prof = MemberDietaryProfile.objects.filter(user=request.user).first()
                        if not diet_prof or not diet_prof.assessment_completed:
                            return redirect('accounts:allergy_assessment')

        return self.get_response(request)
