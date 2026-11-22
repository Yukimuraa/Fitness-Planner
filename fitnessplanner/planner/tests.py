from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from fitnessplanner.accounts.models import (
    UserProfile,
    Allergen,
    MemberAllergy,
    FoodIntolerance,
    MemberIntolerance,
    DietaryPreferenceOption,
    MemberDietaryProfile,
)
from fitnessplanner.planner.models import (
    Meal,
    Workout,
    WorkoutSchedule,
    MembershipPackage,
    UserMembership,
    Instructor,
    InstructorBooking,
    InstructorAssignment,
    InstructorAvailability,
    SessionCreditTransaction,
    WorkoutPlan,
    FitnessAssessment,
    Notification,
)
from fitnessplanner.planner.fitness_engine import (
    analyze_workout_imbalance,
    generate_fitness_recommendation,
    analyze_meal_health,
)


class FitnessSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='Password123!')
        self.profile = self.user.userprofile
        self.profile.age = 28
        self.profile.gender = 'male'
        self.profile.height_cm = 175
        self.profile.weight_kg = 75.0
        self.profile.fitness_goal = 'build_muscle'
        self.profile.focused_muscles = 'chest,back'
        self.profile.activity_level = 'moderate'
        self.profile.allergies = 'nuts,dairy'
        self.profile.health_conditions = 'hypertension'
        self.profile.save()
        MemberDietaryProfile.objects.create(user=self.user, assessment_completed=True)
        self.client.login(username='testuser', password='Password123!')

    def test_membership_subscribe_and_cancel(self):
        # Verify PHP prices
        starter = MembershipPackage.objects.get(slug='starter-basic')
        pro = MembershipPackage.objects.get(slug='pro-fitness')
        elite = MembershipPackage.objects.get(slug='elite-transformation')
        bundle = MembershipPackage.objects.get(slug='90-day-bundle-package')
        self.assertEqual(float(starter.price), 0.0)
        self.assertEqual(float(pro.price), 499.0)
        self.assertEqual(float(elite.price), 999.0)
        self.assertEqual(float(bundle.price), 2499.0)

        resp = self.client.get(reverse('planner:membership_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '₱499')
        self.assertContains(resp, '₱2,499')
        self.assertNotContains(resp, '$499')

        # 1. Starter Basic activates immediately
        self.client.post(reverse('planner:membership_subscribe', args=[starter.pk]))
        active_starter = UserMembership.objects.filter(user=self.user, status='active').first()
        self.assertIsNotNone(active_starter)
        self.assertEqual(active_starter.payment_status, 'not_required')

        # 2. Paid membership creates a pending request without overwriting existing active Starter Basic
        self.client.post(reverse('planner:membership_subscribe', args=[pro.pk]), {
            'payment_reference': 'GCASH-123456',
        })
        pending = UserMembership.objects.filter(user=self.user, status='pending', package=pro).first()
        self.assertIsNotNone(pending)
        self.assertEqual(pending.payment_status, 'pending')
        self.assertEqual(float(pending.amount_php), 499.0)
        self.assertEqual(pending.sessions_remaining, 0)  # Locked until approved
        active_starter.refresh_from_db()
        self.assertEqual(active_starter.status, 'active')  # Existing active preserved

        # Duplicate click does not create a second pending request
        self.client.post(reverse('planner:membership_subscribe', args=[pro.pk]))
        self.assertEqual(UserMembership.objects.filter(user=self.user, status='pending', package=pro).count(), 1)

        # 3. Admin approves the pending request -> unlocks sessions and cancels old active
        self.user.is_staff = True
        self.user.save()
        self.client.post(reverse('planner:admin_membership_approve', args=[pending.pk]))
        pending.refresh_from_db()
        active_starter.refresh_from_db()
        self.assertEqual(pending.status, 'active')
        self.assertEqual(pending.payment_status, 'approved')
        self.assertEqual(pending.sessions_remaining, pro.included_instructor_sessions)
        self.assertEqual(active_starter.status, 'cancelled')

        # 4. Admin rejects a pending Elite request
        self.client.post(reverse('planner:membership_subscribe', args=[elite.pk]))
        elite_req = UserMembership.objects.get(user=self.user, status='pending', package=elite)
        self.client.post(reverse('planner:admin_membership_reject', args=[elite_req.pk]))
        elite_req.refresh_from_db()
        self.assertEqual(elite_req.status, 'rejected')
        self.assertEqual(elite_req.payment_status, 'rejected')

        # 5. Membership expiration check
        pending.end_date = date.today() - timedelta(days=1)
        pending.save()
        self.client.get(reverse('planner:membership_list'))
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'expired')

    def test_instructor_booking_uses_and_refunds_package_session(self):
        pkg = MembershipPackage.objects.get(slug='pro-fitness')
        membership = UserMembership.objects.create(
            user=self.user,
            package=pkg,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='active',
            payment_status='approved',
            sessions_remaining=2,
        )
        inst = Instructor.objects.first()
        booking_date = date.today() + timedelta(days=2)
        resp = self.client.post(reverse('planner:instructor_list'), {
            'instructor': inst.pk,
            'session_date': booking_date.isoformat(),
            'time_slot': '09:00 AM - 10:00 AM',
            'focus_area': 'Imbalance fix',
            'notes': 'Focus on posture',
        })
        self.assertEqual(resp.status_code, 302)
        # Pending booking does NOT deduct credits yet
        membership.refresh_from_db()
        self.assertEqual(membership.sessions_remaining, 2)

        booking = InstructorBooking.objects.get(user=self.user)
        self.assertEqual(booking.status, 'pending')

        # Duplicate booking on same date & time is prevented
        self.client.post(reverse('planner:instructor_list'), {
            'instructor': inst.pk,
            'session_date': booking_date.isoformat(),
            'time_slot': '09:00 AM - 10:00 AM',
        })
        self.assertEqual(InstructorBooking.objects.filter(user=self.user).count(), 1)

        # Member cancels pending booking
        self.client.post(reverse('planner:instructor_booking_cancel', args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        membership.refresh_from_db()
        self.assertEqual(membership.sessions_remaining, 2)

    def test_imbalance_detection_and_fitness_recommendation(self):
        chest_w = Workout.objects.filter(muscle_group='chest').first()
        for i in range(3):
            WorkoutSchedule.objects.create(
                user=self.user,
                workout=chest_w,
                date=date.today() - timedelta(days=i + 1),
            )
        report = analyze_workout_imbalance(self.user, self.profile)
        self.assertLess(report['score'], 85)
        titles = [item['title'] for item in report['imbalances']]
        self.assertTrue(any('Push-Dominant' in t or 'Upper-Body Dominant' in t for t in titles))

        rec = generate_fitness_recommendation(self.user, self.profile)
        self.assertEqual(rec['days_per_week'], 4)
        self.assertTrue(len(rec['safety_notes']) >= 1)
        self.assertTrue(len(rec['recommended_workouts']) >= 1)

        resp = self.client.get(reverse('planner:smart_suggestions'))
        self.assertEqual(resp.status_code, 200)

    def test_meal_allergy_and_health_analysis(self):
        pb_oats = Meal.objects.get(name='Peanut Butter Protein Oats')
        analysis = analyze_meal_health(pb_oats, self.profile)
        self.assertEqual(analysis['verdict_class'], 'danger')
        self.assertIn('nuts', analysis['allergy_conflicts'])
        self.assertIn('dairy', analysis['allergy_conflicts'])
        self.assertTrue(len(analysis['swaps']) >= 2)
        self.assertTrue(len(analysis['safe_alternatives']) >= 1)

        resp = self.client.get(reverse('planner:meal_health_check_detail', args=[pb_oats.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_renders_with_all_new_sections(self):
        resp = self.client.get(reverse('planner:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Smart Fitness')
        self.assertContains(resp, 'Membership')

    def test_admin_can_add_toggle_and_delete_instructor(self):
        # Non-staff user should be redirected away from admin instructor create
        resp = self.client.post(reverse('planner:admin_instructor_create'), {
            'name': 'Unauthorized Coach',
            'specialty': 'Test',
            'experience_years': 2,
            'hourly_rate': '40.00',
            'rating': 4.5,
            'available_days': 'Mon',
            'avatar_emoji': '🏋️',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Instructor.objects.filter(name='Unauthorized Coach').exists())

        # Staff user can access admin dashboard and add/toggle/delete instructor
        self.user.is_staff = True
        self.user.save()
        dash = self.client.get(reverse('planner:admin_dashboard'))
        self.assertEqual(dash.status_code, 200)
        self.assertContains(dash, 'Add New Instructor')
        for page_name in (
            'planner:admin_analytics',
            'planner:admin_users',
            'planner:admin_memberships',
            'planner:admin_instructor_new',
            'planner:admin_instructors',
            'planner:admin_assignments',
        ):
            self.assertEqual(self.client.get(reverse(page_name)).status_code, 200)

        resp = self.client.post(reverse('planner:admin_instructor_create'), {
            'name': 'Coach Alex Rivera',
            'specialty': 'Strength & Mobility',
            'bio': 'Experienced mobility coach.',
            'experience_years': 5,
            'certification': 'NASM-CPT',
            'hourly_rate': '55.00',
            'rating': 4.9,
            'available_days': 'Mon, Wed, Fri',
            'avatar_emoji': '💪',
            'is_active': True,
        })
        self.assertEqual(resp.status_code, 302)
        inst = Instructor.objects.get(name='Coach Alex Rivera')
        self.assertTrue(inst.is_active)

        self.client.post(reverse('planner:admin_instructor_toggle', args=[inst.pk]))
        inst.refresh_from_db()
        self.assertFalse(inst.is_active)

        self.client.post(reverse('planner:admin_instructor_delete', args=[inst.pk]))
        self.assertFalse(Instructor.objects.filter(pk=inst.pk).exists())

    def test_admin_login_skips_goal_selection_and_goes_to_dashboard(self):
        self.client.logout()
        staff = User.objects.create_user(username='admin_only', password='AdminPass123!', is_staff=True)
        # Ensure staff has NO fitness_goal or focused_muscles set
        self.assertEqual(staff.userprofile.fitness_goal, '')

        resp = self.client.get(reverse('planner:admin_login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Enter admin username')
        self.assertNotContains(resp, 'e.g. carinadmin')
        self.assertNotContains(resp, 'Get started')

        # Non-staff user is rejected on admin_login
        bad_resp = self.client.post(reverse('planner:admin_login'), {
            'username': 'testuser',
            'password': 'Password123!',
        })
        self.assertEqual(bad_resp.status_code, 200)
        self.assertContains(bad_resp, 'does not have admin/staff permissions')

        # Staff user logs in and goes straight to admin_dashboard without goal/muscle prompts
        login_resp = self.client.post(reverse('planner:admin_login'), {
            'username': 'admin_only',
            'password': 'AdminPass123!',
        })
        self.assertRedirects(login_resp, reverse('planner:admin_dashboard'))
        dash_resp = self.client.get(reverse('planner:admin_dashboard'))
        self.assertEqual(dash_resp.status_code, 200)

    def test_allergy_assessment_onboarding_and_unverified_meal_safety(self):
        self.client.logout()
        new_user = User.objects.create_user(username='onboard_user', password='Password123!')
        new_user.userprofile.fitness_goal = 'maintain_weight'
        new_user.userprofile.save()
        self.client.login(username='onboard_user', password='Password123!')

        # Middleware redirects to Step 4 allergy assessment before dashboard
        dash_redirect = self.client.get(reverse('planner:index'))
        self.assertRedirects(dash_redirect, reverse('accounts:allergy_assessment'))

        # Conflicting selection fails validation
        bad_post = self.client.post(reverse('accounts:allergy_assessment'), {
            'no_known_allergies': 'on',
            'allergens': ['peanuts'],
        })
        self.assertEqual(bad_post.status_code, 200)
        self.assertContains(bad_post, 'not both')

        # Valid Step 4 submission saves normalized records and redirects to Step 5 review
        ok_post = self.client.post(reverse('accounts:allergy_assessment'), {
            'allergens': ['peanuts', 'sesame'],
            'allergy_severity': 'Severe hives',
            'intolerances': ['lactose'],
            'dietary_preferences': ['vegetarian'],
            'other_restrictions': 'Low sodium per dietitian',
        })
        self.assertRedirects(ok_post, reverse('accounts:onboarding_review'))
        self.assertTrue(MemberAllergy.objects.filter(user=new_user, allergen__slug='peanuts').exists())
        self.assertTrue(MemberIntolerance.objects.filter(user=new_user, intolerance__slug='lactose').exists())

        # Step 5 review completes onboarding
        complete_post = self.client.post(reverse('accounts:onboarding_review'))
        self.assertRedirects(complete_post, reverse('planner:index'))
        self.assertTrue(new_user.dietary_profile.assessment_completed)

        # Unverified meal is NEVER marked safe
        unverified = Meal.objects.create(
            name='Mystery Cafe Bowl',
            description='Chef special',
            ingredients='',
            ingredients_verified=False,
            calories=400,
        )
        res = analyze_meal_health(unverified, new_user.userprofile)
        self.assertEqual(res['verdict'], 'Verification Required')
        self.assertTrue(res['missing_verification'])

    def test_complete_instructor_portal_and_credit_lifecycle(self):
        # 1. Member cannot access Instructor Portal (403)
        self.assertEqual(self.client.get(reverse('planner:instructor_dashboard')).status_code, 403)

        # 2. Admin creates Instructor account with temporary password
        self.user.is_staff = True
        self.user.save()
        self.client.post(reverse('planner:admin_instructor_create'), {
            'name': 'Coach Sam Santos',
            'email': 'sam@fitlife.ph',
            'contact_number': '09171234567',
            'specialty': 'Strength Training',
            'experience_years': 6,
            'certification': 'NSCA-CPT',
            'hourly_rate': '500.00',
            'available_days': 'Mon, Wed, Fri',
            'avatar_emoji': '🏋️',
            'status': 'active',
            'bio': 'Strength coach.',
            'username': 'coach_sam',
            'temporary_password': 'TempPass123!',
        })
        inst = Instructor.objects.get(name='Coach Sam Santos')
        self.assertIsNotNone(inst.user)
        self.assertTrue(inst.user.userprofile.must_change_password)

        # Admin assigns a regular member to Coach Sam
        member = User.objects.create_user(username='assigned_member', password='Password123!')
        member.userprofile.fitness_goal = 'build_muscle'
        member.userprofile.focused_muscles = 'chest,back'
        member.userprofile.save()
        MemberDietaryProfile.objects.create(user=member, assessment_completed=True)

        pkg = MembershipPackage.objects.get(slug='pro-fitness')
        mem_ship = UserMembership.objects.create(
            user=member,
            package=pkg,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='active',
            payment_status='approved',
            sessions_remaining=2,
        )
        self.client.post(reverse('planner:admin_assign_member'), {
            'member_id': member.id,
            'instructor_id': inst.id,
            'notes': 'Strength focus',
        })
        self.assertTrue(InstructorAssignment.objects.filter(instructor=inst, member=member, is_active=True).exists())

        # 3. Member submits a Pending booking request on an open Monday slot
        self.client.logout()
        self.client.login(username='assigned_member', password='Password123!')
        # Find next Monday
        days_ahead = (0 - date.today().weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = date.today() + timedelta(days=days_ahead)

        self.client.post(reverse('planner:instructor_list'), {
            'instructor': inst.pk,
            'session_date': next_monday.isoformat(),
            'time_slot': '09:00 AM - 10:00 AM',
            'focus_area': 'Squat form',
        })
        booking = InstructorBooking.objects.get(user=member, instructor=inst)
        self.assertEqual(booking.status, 'pending')
        self.assertTrue(Notification.objects.filter(user=inst.user, notification_type='booking_request').exists())

        # 4. Instructor logs in -> forced to change temporary password -> accesses dashboard
        self.client.logout()
        login_resp = self.client.post(reverse('login'), {
            'username': 'coach_sam',
            'password': 'TempPass123!',
        })
        self.assertRedirects(login_resp, reverse('accounts:force_password_change'))
        pw_resp = self.client.post(reverse('accounts:force_password_change'), {
            'new_password1': 'NewCoachPass123!',
            'new_password2': 'NewCoachPass123!',
        })
        self.assertRedirects(pw_resp, reverse('planner:instructor_dashboard'))

        # Instructor cannot access unassigned member (403)
        self.assertEqual(
            self.client.get(reverse('planner:instructor_member_detail', args=[self.user.id])).status_code,
            403,
        )
        # Instructor CAN access assigned member
        self.assertEqual(
            self.client.get(reverse('planner:instructor_member_detail', args=[member.id])).status_code,
            200,
        )

        # 5. Instructor accepts booking (reserves 1 credit) then marks Completed (deducts permanently)
        self.client.post(reverse('planner:instructor_booking_action', args=[booking.pk, 'accept']))
        booking.refresh_from_db()
        mem_ship.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertTrue(booking.credit_reserved)
        self.assertEqual(mem_ship.sessions_remaining, 1)

        self.client.post(reverse('planner:instructor_booking_action', args=[booking.pk, 'complete']))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'completed')
        self.assertTrue(booking.credit_deducted)
        self.assertEqual(SessionCreditTransaction.objects.filter(booking=booking).count(), 2)

        # 6. Instructor creates WorkoutPlan and FitnessAssessment for assigned member
        self.client.post(reverse('planner:instructor_workout_plans'), {
            'member': member.id,
            'title': 'Coach Sam Upper Strength',
            'fitness_goal': 'Build Muscle',
            'target_muscle_groups': 'Chest, Back',
            'frequency_per_week': 3,
        })
        self.assertTrue(WorkoutPlan.objects.filter(instructor=inst, member=member).exists())

        self.client.post(reverse('planner:instructor_assessments'), {
            'member': member.id,
            'assessed_at': date.today().isoformat(),
            'weight_kg': 72.5,
            'height_cm': 175,
            'assessment_notes': 'Good baseline mobility.',
        })
        assessment = FitnessAssessment.objects.get(instructor=inst, member=member)
        self.assertEqual(assessment.bmi, 23.7)

        # Verify all 8 Instructor Portal navigation routes render HTTP 200
        for inst_route in (
            'planner:instructor_dashboard',
            'planner:instructor_members',
            'planner:instructor_appointments',
            'planner:instructor_schedule',
            'planner:instructor_workout_plans',
            'planner:instructor_assessments',
            'planner:instructor_progress',
            'planner:instructor_profile_settings',
        ):
            self.assertEqual(self.client.get(reverse(inst_route)).status_code, 200)

        # 7. Member sees Coach Plan & Notifications on Member Dashboard
        self.client.logout()
        self.client.login(username='assigned_member', password='Password123!')
        dash = self.client.get(reverse('planner:index'))
        self.assertEqual(dash.status_code, 200)
        self.assertContains(dash, 'Coach Sam Upper Strength')
