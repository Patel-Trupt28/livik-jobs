from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.utils import timezone

from dashb2.models import Job
from account.models import Employee, EmployeeProfile, UserSettings

from .models import JobApplication

# Create your views here.
def index(request):
    return render(request, 'index1.html')

@login_required
def dprofile(request):
    profile, _ = EmployeeProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
        },
    )
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]

    if request.method == 'POST':
        photo = request.FILES.get('profile_photo')
        if photo:
            employee = Employee.objects.filter(username=request.user).first()
            if employee:
                employee.photo = photo
                employee.save(update_fields=['photo'])
                messages.success(request, 'Profile photo updated.')
            else:
                messages.error(request, 'Employee profile not found.')

        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.email = request.POST.get('email', profile.email)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.website = request.POST.get('website', profile.website)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.experience_years = request.POST.get('experience_years', profile.experience_years)
        profile.education = request.POST.get('education', profile.education)
        profile.highest_education = request.POST.get('highest_education', profile.highest_education)
        profile.institution = request.POST.get('institution', profile.institution)
        profile.graduation_year = request.POST.get('graduation_year', profile.graduation_year)
        profile.languages = request.POST.get('languages', profile.languages)
        profile.categories = request.POST.get('categories', profile.categories)
        profile.current_salary = request.POST.get('current_salary', profile.current_salary)
        profile.expected_salary = request.POST.get('expected_salary', profile.expected_salary)
        profile.expected_ctc = request.POST.get('expected_ctc', profile.expected_ctc)
        profile.notice_period = request.POST.get('notice_period', profile.notice_period)
        profile.country = request.POST.get('country', profile.country)
        profile.city = request.POST.get('city', profile.city)
        profile.address = request.POST.get('address', profile.address)
        profile.map_address = request.POST.get('map_address', profile.map_address)
        profile.latitude = request.POST.get('latitude', profile.latitude)
        profile.longitude = request.POST.get('longitude', profile.longitude)
        profile.facebook = request.POST.get('facebook', profile.facebook)
        profile.twitter = request.POST.get('twitter', profile.twitter)
        profile.instagram = request.POST.get('instagram', profile.instagram)
        profile.skills = request.POST.get('skills', profile.skills)
        profile.preferred_locations = request.POST.get('preferred_locations', profile.preferred_locations)
        profile.preferred_job_titles = request.POST.get('preferred_job_titles', profile.preferred_job_titles)
        profile.preferred_job_types = request.POST.get('preferred_job_types', profile.preferred_job_types)
        profile.preferred_industries = request.POST.get('preferred_industries', profile.preferred_industries)
        profile.open_to_remote = request.POST.get('open_to_remote') == 'on'
        profile.open_to_hybrid = request.POST.get('open_to_hybrid') == 'on'
        profile.open_to_onsite = request.POST.get('open_to_onsite') == 'on'
        profile.open_to_relocate = request.POST.get('open_to_relocate') == 'on'
        profile.save()

        messages.success(request, 'Profile details saved.')
        return redirect('/dashboard1/profile/')

    return render(request, 'profile.html', {'profile': profile, 'skill_list': skill_list})

def login(request):
    return render(request, 'login.html')

def recruiters(request):
    jobs = (
        Job.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .order_by('company_name', '-created_at')
    )

    company_map = {}
    for job in jobs:
        company = company_map.get(job.company_name)
        if company is None:
            company = {
                'name': job.company_name,
                'location': job.location or '',
                'logo': job.file_upload,
                'open_jobs': 0,
            }
            company_map[job.company_name] = company

        if not job.is_closed:
            company['open_jobs'] += 1

        if not company['logo'] and job.file_upload:
            company['logo'] = job.file_upload

        if not company['location'] and job.location:
            company['location'] = job.location

    companies = list(company_map.values())
    return render(request, 'recruiters.html', {'companies': companies})


def my_job_grid(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in or register to apply for a job.')
            return redirect('/account/login/')

        job_id = request.POST.get('job_id')
        job = get_object_or_404(Job, id=job_id, is_closed=False)

        applicant_name = request.POST.get('applicant_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not applicant_name or not email or not phone:
            messages.error(request, 'Name, email, and phone are required.')
            return redirect('/dashboard1/my_job_grid/')

        # Prevent duplicate applications by the same logged-in user or email
        duplicate_qs = JobApplication.objects.filter(job=job).filter(
            models.Q(applicant_user=request.user) |
            models.Q(email__iexact=email)
        )
        if duplicate_qs.exists():
            messages.warning(request, f'You have already applied for "{job.job_title}".')
            return redirect('/dashboard1/my_job_grid/')

        JobApplication.objects.create(
            job=job,
            applicant_user=request.user,
            applicant_name=applicant_name,
            email=email,
            phone=phone,
            current_location=request.POST.get('current_location', '').strip(),
            experience_years=request.POST.get('experience_years') or 0,
            cover_letter=request.POST.get('cover_letter', '').strip(),
            resume=request.FILES.get('resume')
        )

        # Track applied jobs in session for immediate UI disable (covers anonymous users)
        applied_session = set(request.session.get('applied_jobs', []))
        applied_session.add(job.id)
        request.session['applied_jobs'] = list(applied_session)
        request.session['last_applicant_email'] = email

        messages.success(request, f'Application submitted for "{job.job_title}".')
        return redirect('/dashboard1/my_job_grid/')

    jobs_list = Job.objects.filter(is_closed=False).order_by('-created_at')
    for job in jobs_list:
        job.tag_list = [tag.strip() for tag in (job.tags or '').split(',') if tag.strip()]

    paginator = Paginator(jobs_list, 12)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    applied_job_ids = set()
    if request.user.is_authenticated:
        applied_job_ids |= set(
            JobApplication.objects.filter(applicant_user=request.user).values_list('job_id', flat=True)
        )
        # Also respect prior applications made with this user's email
        if request.user.email:
            applied_job_ids |= set(
                JobApplication.objects.filter(email__iexact=request.user.email).values_list('job_id', flat=True)
            )
    # Include session-tracked applied jobs (anonymous or immediate feedback)
    applied_job_ids |= set(request.session.get('applied_jobs', []))
    # Include jobs applied with the last email used in this session
    last_email = request.session.get('last_applicant_email')
    if last_email:
        applied_job_ids |= set(
            JobApplication.objects.filter(email__iexact=last_email).values_list('job_id', flat=True)
        )
    for job in jobs:
        job.has_applied = job.id in applied_job_ids

    return render(request, 'my_job_grid.html', {
        'jobs': jobs,
        'total_jobs': jobs_list.count(),
    })


@login_required
def settings(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'all')

        if action == 'security':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New password and confirmation do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            else:
                request.user.set_password(new_password)
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password updated successfully.')

            settings_obj.two_factor_enabled = request.POST.get('two_factor_enabled') == 'on'
            settings_obj.save(update_fields=['two_factor_enabled'])

        elif action == 'notifications':
            settings_obj.notify_email_jobs = request.POST.get('notify_email_jobs') == 'on'
            settings_obj.notify_email_applications = request.POST.get('notify_email_applications') == 'on'
            settings_obj.notify_email_news = request.POST.get('notify_email_news') == 'on'
            settings_obj.notify_sms = request.POST.get('notify_sms') == 'on'
            settings_obj.notify_browser = request.POST.get('notify_browser') == 'on'
            settings_obj.save(update_fields=[
                'notify_email_jobs',
                'notify_email_applications',
                'notify_email_news',
                'notify_sms',
                'notify_browser',
            ])
            messages.success(request, 'Notification settings saved.')

        elif action == 'privacy':
            settings_obj.profile_visibility = request.POST.get('profile_visibility', settings_obj.profile_visibility)
            settings_obj.show_email = request.POST.get('show_email') == 'yes'
            settings_obj.allow_search_index = request.POST.get('allow_search_index') == 'on'
            settings_obj.save(update_fields=[
                'profile_visibility',
                'show_email',
                'allow_search_index',
            ])
            messages.success(request, 'Privacy settings saved.')

        elif action == 'preferences':
            settings_obj.theme_preference = request.POST.get('theme_preference', settings_obj.theme_preference)
            settings_obj.language = request.POST.get('language', settings_obj.language)
            settings_obj.timezone = request.POST.get('timezone', settings_obj.timezone)
            settings_obj.save(update_fields=['theme_preference', 'language', 'timezone'])
            messages.success(request, 'Preferences saved.')

        elif action == 'account':
            settings_obj.account_active = request.POST.get('account_active') == 'on'
            settings_obj.save(update_fields=['account_active'])
            messages.success(request, 'Account settings saved.')

        return redirect('/dashboard1/settings/')

    return render(request, 'settings.html', {'settings_obj': settings_obj})


def _month_start(value):
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_range(end, count=12):
    end_month = _month_start(end)
    start_month = _add_months(end_month, -(count - 1))
    months = []
    for offset in range(count):
        months.append(_add_months(start_month, offset))
    return months


def _series_for(qs, date_field, months):
    if not months:
        return []
    start = months[0]
    data = (
        qs.filter(**{f'{date_field}__gte': start})
        .annotate(month=TruncMonth(date_field))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    index = {item['month']: item['total'] for item in data}
    return [index.get(month, 0) for month in months]


def dashboard_stats(request):
    now = timezone.now()
    months = _month_range(now, 12)
    labels = [month.strftime('%b') for month in months]

    jobs_qs = Job.objects.all()
    applications_qs = JobApplication.objects.all()

    metrics = {
        'total_jobs': jobs_qs.count(),
        'open_jobs': jobs_qs.filter(is_closed=False).count(),
        'closed_jobs': jobs_qs.filter(is_closed=True).count(),
        'total_applications': applications_qs.count(),
        'pending_applications': applications_qs.filter(status='pending').count(),
        'shortlisted_applications': applications_qs.filter(status='shortlisted').count(),
        'hired_applications': applications_qs.filter(status='hired').count(),
        'rejected_applications': applications_qs.filter(status='rejected').count(),
    }

    chart = {
        'labels': labels,
        'series': {
            'Jobs': _series_for(jobs_qs, 'created_at', months),
            'Applications': _series_for(applications_qs, 'created_at', months),
            'Hires': _series_for(applications_qs.filter(status='hired'), 'created_at', months),
        },
    }

    return JsonResponse({'metrics': metrics, 'chart': chart})
