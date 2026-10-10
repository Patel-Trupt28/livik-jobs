from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Contact
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import os
import urllib.request
import urllib.error
import time
from dashb2.models import Job
from dashb1.models import JobApplication
from django.db import models
from django.db.models import Q
from account.models import EmployeeProfile, EmployerProfile, Employee, Employer

def index(request):
    recent_jobs = Job.objects.filter(is_published=True, is_closed=False).order_by('-created_at')[:5]
    total_jobs = Job.objects.filter(is_published=True).count()
    total_employees = Employee.objects.count()
    total_employers = Employer.objects.count()
    total_applications = JobApplication.objects.count()

    latest_employee_profiles = (
        EmployeeProfile.objects.select_related('user').order_by('-id')[:3]
    )
    latest_employer_profiles = (
        EmployerProfile.objects.select_related('user').order_by('-id')[:3]
    )

    employee_photo_map = {}
    if latest_employee_profiles:
        employee_users = [profile.user for profile in latest_employee_profiles]
        for emp in Employee.objects.filter(username__in=employee_users).select_related('username'):
            if emp.photo:
                employee_photo_map[emp.username_id] = emp.photo.url

    employer_photo_map = {}
    if latest_employer_profiles:
        employer_users = [profile.user for profile in latest_employer_profiles]
        for emp in Employer.objects.filter(username__in=employer_users).select_related('username'):
            if emp.photo:
                employer_photo_map[emp.username_id] = emp.photo.url

    for profile in latest_employee_profiles:
        profile.photo_url = employee_photo_map.get(profile.user_id)
    for profile in latest_employer_profiles:
        profile.photo_url = employer_photo_map.get(profile.user_id)

    testimonials = []
    for profile in EmployeeProfile.objects.exclude(bio='').order_by('-id')[:2]:
        testimonials.append({
            'name': profile.full_name or profile.user.username,
            'role': 'Employee',
            'bio': profile.bio,
            'photo_url': employee_photo_map.get(profile.user_id),
        })
    for profile in EmployerProfile.objects.exclude(bio='').order_by('-id')[:2]:
        testimonials.append({
            'name': profile.full_name or profile.user.username,
            'role': 'Employer',
            'bio': profile.bio,
            'photo_url': employer_photo_map.get(profile.user_id),
        })
    testimonials = testimonials[:3]

    return render(request, 'index.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'total_employees': total_employees,
        'total_employers': total_employers,
        'total_applications': total_applications,
        'latest_employee_profiles': latest_employee_profiles,
        'latest_employer_profiles': latest_employer_profiles,
        'testimonials': testimonials,
    })

def job_my_resume(request):
    return render(request, 'job_my_resume.html')

def job_cv_manager(request):
    return render(request, 'job_cv_manager.html')

def about_us(request):
    return render(request, 'about_us.html')

def companies(request):
    companies = (
        Job.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name__exact='')
        .values_list('company_name', flat=True)
        .distinct()
        .order_by('company_name')
    )
    return render(request, 'companies.html', {'companies': companies})

@csrf_exempt
def chat_response(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    use_ollama = os.environ.get('USE_OLLAMA', '').strip().lower() in {'1', 'true', 'yes'}
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    messages = payload.get('messages', [])
    if isinstance(payload.get('use_ollama'), bool):
        use_ollama = payload['use_ollama']
    if not api_key and not use_ollama:
        # Fall back to Ollama when no OpenAI key is configured.
        use_ollama = True
    if not isinstance(messages, list):
        return JsonResponse({'error': 'Invalid messages'}, status=400)

    # Cap conversation size to reduce latency/cost.
    messages = messages[-8:]

    model = os.environ.get('OLLAMA_MODEL', 'llama2') if use_ollama else os.environ.get('OPENAI_MODEL', 'gpt-5')
    system_prompt = 'You are a helpful job portal assistant. Be concise and practical.'

    # Add lightweight DB context for job/company queries.
    latest_user_text = ''
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            latest_user_text = msg.get('content', '')
            break
    if isinstance(latest_user_text, str):
        query_lower = latest_user_text.lower()
    else:
        query_lower = ''

    if any(token in query_lower for token in ('job', 'jobs', 'company', 'companies', 'openings', 'vacancy', 'vacancies', 'list')):
        try:
            recent_jobs = (
                Job.objects
                .filter(is_published=True, is_closed=False)
                .order_by('-created_at')[:10]
            )
            company_names = (
                Job.objects
                .filter(is_published=True)
                .exclude(company_name__isnull=True)
                .exclude(company_name__exact='')
                .values_list('company_name', flat=True)
                .distinct()[:10]
            )
            job_lines = []
            for job in recent_jobs:
                job_lines.append(
                    f'- {job.job_title} | {job.company_name or "Unknown company"} | {job.location or "Location not set"} | {job.job_type} | {job.salary or "Salary not set"}'
                )
            companies_line = ', '.join(company_names) if company_names else 'No companies found.'
            context_block = (
                'Current database snapshot:\n'
                'Jobs:\n' + ('\n'.join(job_lines) if job_lines else 'No open jobs found.') + '\n'
                'Companies:\n' + companies_line
            )
            system_prompt = system_prompt + '\n' + context_block
        except Exception:
            pass

    if use_ollama:
        ollama_messages = [{'role': 'system', 'content': system_prompt}]
        ollama_messages.extend(messages)
        request_body = json.dumps({
            'model': model,
            'messages': ollama_messages,
            'stream': False,
            'options': {
                'num_predict': 128
            }
        }).encode('utf-8')
    else:
        request_body = json.dumps({
            'model': model,
            'input': [
                {'role': 'system', 'content': system_prompt},
                *messages
            ]
        }).encode('utf-8')

    if use_ollama:
        req = urllib.request.Request(
            'http://localhost:11434/api/chat',
            data=request_body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
    else:
        req = urllib.request.Request(
            'https://api.openai.com/v1/responses',
            data=request_body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST'
        )

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            timeout_seconds = 120 if use_ollama else 20
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if use_ollama:
                text = (data.get('message') or {}).get('content', '')
            else:
                output_items = data.get('output') or []
                text = ''
                for item in output_items:
                    if item.get('type') != 'message':
                        continue
                    for content_item in item.get('content') or []:
                        if content_item.get('type') == 'output_text':
                            text = content_item.get('text', '')
                            break
                    if text:
                        break
            return JsonResponse({'text': text.strip()})
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = exc.headers.get('Retry-After')
                try:
                    retry_after = int(retry_after) if retry_after else 5
                except ValueError:
                    retry_after = 5
                if attempt < max_retries:
                    time.sleep(retry_after)
                    continue
                return JsonResponse({'error': f'Rate limited. Please wait {retry_after} seconds and try again.'}, status=429)
            try:
                error_body = exc.read().decode('utf-8')
            except Exception:
                error_body = ''
            return JsonResponse({'error': f'Upstream error: {exc} {error_body}'.strip()}, status=502)
        except Exception as exc:
            return JsonResponse({'error': f'Upstream error: {exc}'}, status=502)

@login_required(login_url='/account/login/')
def global_search(request):
    query = (request.GET.get('q') or '').strip()
    employee_profiles = EmployeeProfile.objects.none()
    employer_profiles = EmployerProfile.objects.none()
    companies = []

    if query:
        employee_profiles = (
            EmployeeProfile.objects
            .filter(
                Q(full_name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            )
            .select_related('user')
            .order_by('full_name')[:20]
        )
        employer_profiles = (
            EmployerProfile.objects
            .filter(
                Q(full_name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            )
            .select_related('user')
            .order_by('full_name')[:20]
        )
        companies = (
            Job.objects
            .filter(company_name__icontains=query)
            .exclude(company_name__isnull=True)
            .exclude(company_name__exact='')
            .values_list('company_name', flat=True)
            .distinct()
            .order_by('company_name')[:20]
        )

    employee_photo_map = {}
    employer_photo_map = {}
    if employee_profiles:
        employee_users = [profile.user for profile in employee_profiles]
        for emp in Employee.objects.filter(username__in=employee_users).select_related('username'):
            if emp.photo:
                employee_photo_map[emp.username_id] = emp.photo.url
    if employer_profiles:
        employer_users = [profile.user for profile in employer_profiles]
        for emp in Employer.objects.filter(username__in=employer_users).select_related('username'):
            if emp.photo:
                employer_photo_map[emp.username_id] = emp.photo.url

    for profile in employee_profiles:
        profile.photo_url = employee_photo_map.get(profile.user_id)

    for profile in employer_profiles:
        profile.photo_url = employer_photo_map.get(profile.user_id)

    return render(request, 'search_results.html', {
        'query': query,
        'employee_profiles': employee_profiles,
        'employer_profiles': employer_profiles,
        'companies': companies,
    })

def browse_job_list(request):
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
            return redirect('/browse_job_list/')

        duplicate_qs = JobApplication.objects.filter(job=job).filter(
            models.Q(applicant_user=request.user) |
            models.Q(email__iexact=email)
        )
        if duplicate_qs.exists():
            messages.warning(request, f'You have already applied for "{job.job_title}".')
            return redirect('/browse_job_list/')

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

        applied_session = set(request.session.get('applied_jobs', []))
        applied_session.add(job.id)
        request.session['applied_jobs'] = list(applied_session)
        request.session['last_applicant_email'] = email

        messages.success(request, f'Application submitted for "{job.job_title}".')
        return redirect('/browse_job_list/')

    jobs = Job.objects.filter(is_published=True)
    search_query = (request.GET.get('q') or '').strip()
    search_location = (request.GET.get('location') or '').strip()
    if search_query:
        jobs = jobs.filter(
            models.Q(job_title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(company_name__icontains=search_query)
        )
    if search_location:
        jobs = jobs.filter(location__icontains=search_location)
    jobs = jobs.order_by('-created_at')

    applied_job_ids = set()
    if request.user.is_authenticated:
        applied_job_ids |= set(
            JobApplication.objects.filter(applicant_user=request.user).values_list('job_id', flat=True)
        )
        if request.user.email:
            applied_job_ids |= set(
                JobApplication.objects.filter(email__iexact=request.user.email).values_list('job_id', flat=True)
            )
    applied_job_ids |= set(request.session.get('applied_jobs', []))
    last_email = request.session.get('last_applicant_email')
    if last_email:
        applied_job_ids |= set(
            JobApplication.objects.filter(email__iexact=last_email).values_list('job_id', flat=True)
        )

    return render(request, 'browse_job_list.html', {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'search_query': search_query,
        'search_location': search_location,
    })

@login_required(login_url='/account/login/')
def public_employee_profile(request, username):
    profile = get_object_or_404(EmployeeProfile, user__username=username)
    employee = Employee.objects.filter(username=profile.user).first()
    photo_url = employee.photo.url if employee and employee.photo else None
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]
    return render(request, 'public_employee_profile.html', {
        'profile': profile,
        'photo_url': photo_url,
        'skill_list': skill_list,
    })

@login_required(login_url='/account/login/')
def public_employer_profile(request, username):
    profile = get_object_or_404(EmployerProfile, user__username=username)
    employer = Employer.objects.filter(username=profile.user).first()
    photo_url = employer.photo.url if employer and employer.photo else None
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]
    return render(request, 'public_employer_profile.html', {
        'profile': profile,
        'photo_url': photo_url,
        'skill_list': skill_list,
    })




# def dlogin(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#
#         user = authenticate(username=username, password=password)
#
#         if user is not None:
#             login(request, user)  # Django's login
#             messages.success(request, "Login successful")
#             return redirect('/')  # change if needed
#         else:
#             messages.error(request, "Invalid password")
#             # return render(request, 'login.html')
#             return redirect('/login')
#     return render(request, 'login.html')

# def register(request):
#     if request.method == 'POST':
#         fname = request.POST['dzName']
#         lname = request.POST['dzLname']
#         username = request.POST['username']
#         password = request.POST['dzPassword']
#
#
#         user = User.objects.create_user(username=username, password=password)
#         user.first_name = fname
#         user.last_name = lname
#         user.save()
#
#         # messages.success(request, "Account created successfully")
#         return redirect('/login')
#     return render(request, 'register.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST['dzName']
        email = request.POST['dzEmail']
        message = request.POST['dzMessage']

        c = Contact.objects.create(
            name=name,
            email=email,
            message=message
        )
        return HttpResponse("<h1>Success!</h1>")

    return render(request, 'contact.html')

def blog_classic(request):
    return render(request, 'blog_classic.html')

def Logout(request):
    logout(request)
    messages.success(request, 'Logged Out Successfully!')
    return redirect('/')
