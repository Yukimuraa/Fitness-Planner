from datetime import date, datetime, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from fitnessplanner.accounts.models import ProgressEntry, UserProfile
from .forms import (
    FitnessAssessmentForm,
    InstructorNoteForm,
    InstructorProfileForm,
    WorkoutPlanForm,
)
from .models import (
    FitnessAssessment,
    Instructor,
    InstructorAssignment,
    InstructorAvailability,
    InstructorBooking,
    InstructorNote,
    InstructorUnavailableDate,
    Notification,
    SessionCreditTransaction,
    UserMembership,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutSchedule,
)


def instructor_required(view_func):
    """Ensure the authenticated user has the Instructor role and an active Instructor profile."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        instructor = getattr(request.user, 'instructor_profile', None)
        is_inst = instructor is not None and (
            (profile and profile.role == 'instructor') or instructor is not None
        )
        if not is_inst or request.user.is_staff:
            raise PermissionDenied('Instructor access only.')
        if instructor.status != 'active':
            raise PermissionDenied('Your instructor account is currently inactive or suspended.')
        request.instructor = instructor
        return view_func(request, *args, **kwargs)
    return _wrapped


def _assigned_member_ids(instructor):
    return list(
        InstructorAssignment.objects
        .filter(instructor=instructor, is_active=True)
        .values_list('member_id', flat=True)
    )


def _get_assigned_member_or_403(instructor, member_id):
    assignment = InstructorAssignment.objects.filter(
        instructor=instructor,
        member_id=member_id,
        is_active=True,
    ).select_related('member').first()
    if not assignment:
        raise PermissionDenied('You can only access members assigned to you.')
    return assignment.member


@instructor_required
def instructor_dashboard(request):
    instructor = request.instructor
    today = timezone.localdate()

    assigned_ids = _assigned_member_ids(instructor)
    bookings_qs = InstructorBooking.objects.filter(instructor=instructor).select_related('user', 'membership__package')

    todays_appointments = bookings_qs.filter(
        session_date=today,
        status='confirmed',
    ).order_by('time_slot')

    pending_requests = bookings_qs.filter(status='pending').order_by('session_date', 'time_slot')
    upcoming_appointments = bookings_qs.filter(
        session_date__gte=today,
        status='confirmed',
    ).order_by('session_date', 'time_slot')[:8]

    completed_count = bookings_qs.filter(status='completed').count()
    active_plans_count = WorkoutPlan.objects.filter(instructor=instructor, is_active=True).count()
    notifications = Notification.objects.filter(user=request.user)[:8]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'instructor/dashboard.html', {
        'instructor': instructor,
        'assigned_count': len(assigned_ids),
        'todays_appointments': todays_appointments,
        'pending_requests': pending_requests,
        'upcoming_appointments': upcoming_appointments,
        'completed_count': completed_count,
        'active_plans_count': active_plans_count,
        'notifications': notifications,
        'unread_count': unread_count,
        'today': today,
    })


@instructor_required
def instructor_members(request):
    instructor = request.instructor
    assignments = (
        InstructorAssignment.objects
        .filter(instructor=instructor, is_active=True)
        .select_related('member', 'member__userprofile')
        .order_by('-assigned_at')
    )
    today = timezone.localdate()
    member_rows = []
    for a in assignments:
        m_user = a.member
        profile = getattr(m_user, 'userprofile', None)
        active_mem = UserMembership.objects.filter(
            user=m_user, status='active', end_date__gte=today
        ).select_related('package').first()
        latest_assessment = FitnessAssessment.objects.filter(
            instructor=instructor, member=m_user
        ).first()
        member_rows.append({
            'assignment': a,
            'member': m_user,
            'profile': profile,
            'active_membership': active_mem,
            'latest_assessment': latest_assessment,
        })
    return render(request, 'instructor/members.html', {
        'instructor': instructor,
        'member_rows': member_rows,
    })


@instructor_required
def instructor_member_detail(request, member_id):
    instructor = request.instructor
    member = _get_assigned_member_or_403(instructor, member_id)
    profile, _ = UserProfile.objects.get_or_create(user=member)
    today = timezone.localdate()

    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = InstructorNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.instructor = instructor
            note.member = member
            note.save()
            messages.success(request, 'Coaching note saved.')
            return redirect('planner:instructor_member_detail', member_id=member.id)
    else:
        note_form = InstructorNoteForm()

    active_membership = UserMembership.objects.filter(
        user=member, status='active', end_date__gte=today
    ).select_related('package').first()
    assessments = FitnessAssessment.objects.filter(instructor=instructor, member=member)[:5]
    workout_history = WorkoutSchedule.objects.filter(user=member).select_related('workout').order_by('-date')[:10]
    progress_entries = ProgressEntry.objects.filter(user=member)[:8]
    workout_plans = WorkoutPlan.objects.filter(instructor=instructor, member=member).prefetch_related('exercises')
    notes = InstructorNote.objects.filter(instructor=instructor, member=member)[:10]

    return render(request, 'instructor/member_detail.html', {
        'instructor': instructor,
        'member': member,
        'profile': profile,
        'active_membership': active_membership,
        'assessments': assessments,
        'workout_history': workout_history,
        'progress_entries': progress_entries,
        'workout_plans': workout_plans,
        'notes': notes,
        'note_form': note_form,
    })


@instructor_required
def instructor_appointments(request):
    instructor = request.instructor
    status_filter = request.GET.get('status', '')
    bookings = InstructorBooking.objects.filter(instructor=instructor).select_related('user', 'membership__package')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    return render(request, 'instructor/appointments.html', {
        'instructor': instructor,
        'bookings': bookings.order_by('-session_date', 'time_slot'),
        'status_filter': status_filter,
        'status_choices': InstructorBooking.STATUS_CHOICES,
    })


@instructor_required
def instructor_booking_action(request, pk, action):
    """Instructor accepts, rejects, requests reschedule, completes, or marks no-show on a booking."""
    instructor = request.instructor
    booking = get_object_or_404(InstructorBooking, pk=pk, instructor=instructor)
    if request.method != 'POST':
        return redirect('planner:instructor_appointments')

    today = timezone.localdate()
    note = request.POST.get('instructor_response_note', '').strip()[:500]

    if action == 'accept' and booking.status == 'pending':
        # Check overlapping confirmed booking
        overlap = InstructorBooking.objects.filter(
            instructor=instructor,
            session_date=booking.session_date,
            time_slot=booking.time_slot,
            status='confirmed',
        ).exclude(pk=booking.pk).exists()
        if overlap:
            messages.error(request, f'You already have a confirmed appointment on {booking.session_date} at {booking.time_slot}.')
            return redirect('planner:instructor_appointments')

        # Reserve 1 coaching credit if booking uses membership
        mem = booking.membership or UserMembership.objects.filter(
            user=booking.user, status='active', end_date__gte=today
        ).select_related('package').first()

        if mem and mem.sessions_remaining > 0:
            if not booking.credit_reserved:
                mem.sessions_remaining -= 1
                mem.save()
                booking.membership = mem
                booking.used_package_session = True
                booking.credit_reserved = True
                SessionCreditTransaction.objects.create(
                    user=booking.user,
                    membership=mem,
                    booking=booking,
                    action='reserve',
                    credits_delta=-1,
                    balance_after=mem.sessions_remaining,
                    note=f'Reserved 1 credit upon confirming session with {instructor.name}',
                )
        else:
            messages.error(request, f'{booking.user.username} does not have enough coaching session credits.')
            return redirect('planner:instructor_appointments')

        booking.status = 'confirmed'
        booking.instructor_response_note = note
        booking.save()
        Notification.objects.create(
            user=booking.user,
            title='Coaching Session Confirmed',
            message=f'{instructor.name} confirmed your session on {booking.session_date} ({booking.time_slot}).',
            notification_type='booking_confirmed',
            link_url='/instructors/',
        )
        messages.success(request, f'Confirmed appointment with {booking.user.username} and reserved 1 credit.')

    elif action == 'reject' and booking.status in ('pending', 'confirmed'):
        if booking.credit_reserved and not booking.credit_deducted and booking.membership:
            mem = booking.membership
            mem.sessions_remaining += 1
            mem.save()
            booking.credit_reserved = False
            SessionCreditTransaction.objects.create(
                user=booking.user,
                membership=mem,
                booking=booking,
                action='release',
                credits_delta=1,
                balance_after=mem.sessions_remaining,
                note=f'Released reserved credit (rejected by {instructor.name})',
            )
        booking.status = 'rejected'
        booking.instructor_response_note = note
        booking.save()
        Notification.objects.create(
            user=booking.user,
            title='Coaching Request Declined',
            message=f'{instructor.name} declined your request for {booking.session_date} ({booking.time_slot}).'
                    + (f' Note: {note}' if note else ''),
            notification_type='booking_rejected',
            link_url='/instructors/',
        )
        messages.info(request, 'Booking request rejected.')

    elif action == 'reschedule' and booking.status in ('pending', 'confirmed'):
        suggested_date_str = request.POST.get('suggested_date', '').strip()
        suggested_slot = request.POST.get('suggested_time_slot', '').strip()
        if suggested_date_str:
            try:
                booking.suggested_date = date.fromisoformat(suggested_date_str)
            except ValueError:
                pass
        if suggested_slot:
            booking.suggested_time_slot = suggested_slot
        if booking.credit_reserved and not booking.credit_deducted and booking.membership:
            mem = booking.membership
            mem.sessions_remaining += 1
            mem.save()
            booking.credit_reserved = False
            SessionCreditTransaction.objects.create(
                user=booking.user,
                membership=mem,
                booking=booking,
                action='release',
                credits_delta=1,
                balance_after=mem.sessions_remaining,
                note='Released reserved credit pending reschedule',
            )
        booking.status = 'reschedule_requested'
        booking.instructor_response_note = note
        booking.save()
        Notification.objects.create(
            user=booking.user,
            title='Reschedule Suggested',
            message=f'{instructor.name} suggested rescheduling to {booking.suggested_date or booking.session_date} ({booking.suggested_time_slot or booking.time_slot}).',
            notification_type='booking_reschedule',
            link_url='/instructors/',
        )
        messages.info(request, 'Reschedule suggestion sent to member.')

    elif action == 'complete' and booking.status == 'confirmed':
        if not booking.credit_deducted and booking.membership:
            mem = booking.membership
            if not booking.credit_reserved and mem.sessions_remaining > 0:
                mem.sessions_remaining -= 1
                mem.save()
                booking.credit_reserved = True
            booking.credit_deducted = True
            SessionCreditTransaction.objects.create(
                user=booking.user,
                membership=mem,
                booking=booking,
                action='deduct',
                credits_delta=0 if booking.credit_reserved else -1,
                balance_after=mem.sessions_remaining,
                note=f'Coaching session completed with {instructor.name}',
            )
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        if note:
            booking.instructor_response_note = note
        booking.save()
        Notification.objects.create(
            user=booking.user,
            title='Coaching Session Completed',
            message=f'Your coaching session with {instructor.name} on {booking.session_date} has been marked completed.',
            notification_type='booking_completed',
            link_url='/instructors/',
        )
        messages.success(request, f'Session with {booking.user.username} marked completed.')

    elif action == 'no_show' and booking.status == 'confirmed':
        booking.status = 'no_show'
        booking.instructor_response_note = note
        booking.save()
        messages.warning(request, 'Marked session as No Show.')

    return redirect('planner:instructor_appointments')


@instructor_required
def instructor_schedule(request):
    """Instructor Schedule Management: weekly availability slots, custom slots, blocked dates, and calendar."""
    instructor = request.instructor
    today = timezone.localdate()

    if request.method == 'POST':
        op = request.POST.get('op')
        if op == 'seed_defaults':
            days = request.POST.getlist('days')
            for d_str in days:
                d_int = int(d_str)
                for s_str, e_str, label in InstructorAvailability.DEFAULT_SLOTS:
                    s_t = datetime.strptime(s_str, '%H:%M').time()
                    e_t = datetime.strptime(e_str, '%H:%M').time()
                    InstructorAvailability.objects.get_or_create(
                        instructor=instructor,
                        day_of_week=d_int,
                        start_time=s_t,
                        end_time=e_t,
                        defaults={'time_slot_label': label, 'is_active': True},
                    )
            messages.success(request, 'Suggested default coaching slots added for selected days.')
            return redirect('planner:instructor_schedule')

        elif op == 'add_slot':
            day = int(request.POST.get('day_of_week', 0))
            start_str = request.POST.get('start_time', '09:00')
            end_str = request.POST.get('end_time', '10:00')
            s_t = datetime.strptime(start_str, '%H:%M').time()
            e_t = datetime.strptime(end_str, '%H:%M').time()
            if e_t <= s_t:
                messages.error(request, 'End time must be after start time.')
            else:
                label = f"{s_t.strftime('%I:%M %p')} - {e_t.strftime('%I:%M %p')}"
                InstructorAvailability.objects.create(
                    instructor=instructor,
                    day_of_week=day,
                    start_time=s_t,
                    end_time=e_t,
                    time_slot_label=label,
                    is_active=True,
                )
                messages.success(request, f'Added custom slot: {label}.')
            return redirect('planner:instructor_schedule')

        elif op == 'toggle_slot':
            slot = get_object_or_404(InstructorAvailability, pk=request.POST.get('slot_id'), instructor=instructor)
            slot.is_active = not slot.is_active
            slot.save()
            return redirect('planner:instructor_schedule')

        elif op == 'delete_slot':
            slot = get_object_or_404(InstructorAvailability, pk=request.POST.get('slot_id'), instructor=instructor)
            slot.delete()
            messages.info(request, 'Time slot deleted.')
            return redirect('planner:instructor_schedule')

        elif op == 'block_date':
            b_date_str = request.POST.get('date', '')
            if b_date_str:
                b_date = date.fromisoformat(b_date_str)
                is_full = request.POST.get('is_full_day') == 'on'
                blocked_slot = request.POST.get('blocked_time_slot', '').strip()
                reason = request.POST.get('reason', '').strip()[:200]
                InstructorUnavailableDate.objects.create(
                    instructor=instructor,
                    date=b_date,
                    is_full_day=is_full or not blocked_slot,
                    blocked_time_slot='' if is_full else blocked_slot,
                    reason=reason,
                )
                messages.success(request, f'Blocked {b_date} on your schedule.')
            return redirect('planner:instructor_schedule')

        elif op == 'delete_block':
            blk = get_object_or_404(InstructorUnavailableDate, pk=request.POST.get('block_id'), instructor=instructor)
            blk.delete()
            messages.info(request, 'Blocked date removed.')
            return redirect('planner:instructor_schedule')

    slots = InstructorAvailability.objects.filter(instructor=instructor)
    unavailable_dates = InstructorUnavailableDate.objects.filter(instructor=instructor, date__gte=today)
    confirmed_bookings = InstructorBooking.objects.filter(
        instructor=instructor,
        session_date__gte=today,
        status='confirmed',
    ).select_related('user').order_by('session_date', 'time_slot')

    return render(request, 'instructor/schedule.html', {
        'instructor': instructor,
        'slots': slots,
        'unavailable_dates': unavailable_dates,
        'confirmed_bookings': confirmed_bookings,
        'day_choices': InstructorAvailability.DAY_CHOICES,
        'default_slots': InstructorAvailability.DEFAULT_SLOTS,
        'today': today,
    })


@instructor_required
def instructor_workout_plans(request):
    instructor = request.instructor
    assigned_ids = _assigned_member_ids(instructor)
    assigned_members = User.objects.filter(id__in=assigned_ids).order_by('username')

    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST)
        form.fields['member'].queryset = assigned_members
        if form.is_valid():
            plan = form.save(commit=False)
            if plan.member_id not in assigned_ids:
                raise PermissionDenied('Member is not assigned to you.')
            plan.instructor = instructor
            plan.save()
            Notification.objects.create(
                user=plan.member,
                title='New Workout Plan Assigned',
                message=f'{instructor.name} created a new workout plan for you: {plan.title}.',
                notification_type='workout_plan',
                link_url='/',
            )
            messages.success(request, f'Workout plan "{plan.title}" created!')
            return redirect('planner:instructor_workout_plan_detail', pk=plan.pk)
    else:
        form = WorkoutPlanForm()
        form.fields['member'].queryset = assigned_members

    plans = WorkoutPlan.objects.filter(instructor=instructor).select_related('member').prefetch_related('exercises')
    return render(request, 'instructor/workout_plans.html', {
        'instructor': instructor,
        'form': form,
        'plans': plans,
        'assigned_members': assigned_members,
    })


@instructor_required
def instructor_workout_plan_detail(request, pk):
    instructor = request.instructor
    plan = get_object_or_404(WorkoutPlan, pk=pk, instructor=instructor)

    if request.method == 'POST':
        op = request.POST.get('op')
        if op == 'add_exercise':
            name = request.POST.get('exercise_name', '').strip()
            if name:
                WorkoutPlanExercise.objects.create(
                    plan=plan,
                    exercise_name=name,
                    sets=int(request.POST.get('sets', 3) or 3),
                    reps=request.POST.get('reps', '10-12').strip() or '10-12',
                    duration_min=int(request.POST.get('duration_min', 0) or 0),
                    rest_seconds=int(request.POST.get('rest_seconds', 60) or 60),
                    instructions=request.POST.get('instructions', '').strip(),
                    order=plan.exercises.count() + 1,
                )
                messages.success(request, f'Added exercise "{name}".')
            return redirect('planner:instructor_workout_plan_detail', pk=plan.pk)
        elif op == 'delete_exercise':
            ex = get_object_or_404(WorkoutPlanExercise, pk=request.POST.get('exercise_id'), plan=plan)
            ex.delete()
            return redirect('planner:instructor_workout_plan_detail', pk=plan.pk)
        elif op == 'update_plan':
            plan.title = request.POST.get('title', plan.title).strip()
            plan.notes = request.POST.get('notes', '').strip()
            plan.recommendations = request.POST.get('recommendations', '').strip()
            plan.save()
            messages.success(request, 'Workout plan updated.')
            return redirect('planner:instructor_workout_plan_detail', pk=plan.pk)

    return render(request, 'instructor/workout_plan_detail.html', {
        'instructor': instructor,
        'plan': plan,
    })


@instructor_required
def instructor_assessments(request):
    instructor = request.instructor
    assigned_ids = _assigned_member_ids(instructor)
    assigned_members = User.objects.filter(id__in=assigned_ids).order_by('username')

    if request.method == 'POST':
        form = FitnessAssessmentForm(request.POST)
        form.fields['member'].queryset = assigned_members
        if form.is_valid():
            assessment = form.save(commit=False)
            if assessment.member_id not in assigned_ids:
                raise PermissionDenied('Member is not assigned to you.')
            assessment.instructor = instructor
            assessment.save()
            messages.success(request, f'Fitness assessment recorded for {assessment.member.username}.')
            return redirect('planner:instructor_assessments')
    else:
        form = FitnessAssessmentForm(initial={'assessed_at': timezone.localdate()})
        form.fields['member'].queryset = assigned_members

    assessments = FitnessAssessment.objects.filter(instructor=instructor).select_related('member')[:25]
    return render(request, 'instructor/assessments.html', {
        'instructor': instructor,
        'form': form,
        'assessments': assessments,
    })


@instructor_required
def instructor_progress(request):
    instructor = request.instructor
    assigned_ids = _assigned_member_ids(instructor)
    assigned_members = User.objects.filter(id__in=assigned_ids).order_by('username')

    selected_member_id = request.GET.get('member_id') or (assigned_members.first().id if assigned_members.exists() else None)
    selected_member = None
    progress_entries = []
    completed_workouts = []
    assessments = []
    notes = []

    if selected_member_id:
        selected_member = _get_assigned_member_or_403(instructor, int(selected_member_id))
        if request.method == 'POST':
            note_form = InstructorNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.instructor = instructor
                note.member = selected_member
                note.save()
                messages.success(request, 'Feedback saved.')
                return redirect(f"{request.path}?member_id={selected_member.id}")
        else:
            note_form = InstructorNoteForm(initial={'note_type': 'progress'})

        progress_entries = ProgressEntry.objects.filter(user=selected_member)[:15]
        completed_workouts = WorkoutSchedule.objects.filter(user=selected_member, completed=True).select_related('workout').order_by('-date')[:15]
        assessments = FitnessAssessment.objects.filter(instructor=instructor, member=selected_member)[:5]
        notes = InstructorNote.objects.filter(instructor=instructor, member=selected_member)[:10]
    else:
        note_form = InstructorNoteForm()

    return render(request, 'instructor/progress.html', {
        'instructor': instructor,
        'assigned_members': assigned_members,
        'selected_member': selected_member,
        'progress_entries': progress_entries,
        'completed_workouts': completed_workouts,
        'assessments': assessments,
        'notes': notes,
        'note_form': note_form,
    })


@instructor_required
def instructor_profile_settings(request):
    instructor = request.instructor
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Instructor profile updated!')
            return redirect('planner:instructor_profile_settings')
    else:
        form = InstructorProfileForm(instance=instructor)
    return render(request, 'instructor/profile_settings.html', {
        'instructor': instructor,
        'form': form,
    })


@login_required
def notifications_mark_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'planner:index')
