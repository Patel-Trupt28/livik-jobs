from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from dashb2.models import Job
from dashb1.models import JobApplication
from django.db import models
from django.db.models import Q
from account.models import EmployeeProfile, EmployerProfile, Employee, Employer

def emp_index(request):
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

    return render(request, 'emp_index.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'total_employees': total_employees,
        'total_employers': total_employers,
        'total_applications': total_applications,
        'latest_employee_profiles': latest_employee_profiles,
        'latest_employer_profiles': latest_employer_profiles,
        'testimonials': testimonials,
    })

def emp_about_us(request):
    return render(request, 'emp_about_us.html')

def emp_companies(request):
    companies = (
        Job.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name__exact='')
        .values_list('company_name', flat=True)
        .distinct()
        .order_by('company_name')
    )
    return render(request, 'emp_companies.html', {'companies': companies})

def emp_dlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)  # Django's login
            messages.success(request, "Login successful")
            return redirect('/')  # change if needed
        else:
            messages.error(request, "Invalid password")
            # return render(request, 'login.html')
            return redirect('/login')
    return render(request, 'emp_login.html')

def emp_register(request):
    if request.method == 'POST':
        fname = request.POST['dzName']
        lname = request.POST['dzLname']
        username = request.POST['username']
        password = request.POST['dzPassword']


        user = User.objects.create_user(username=username, password=password)
        user.first_name = fname
        user.last_name = lname
        user.save()

        # messages.success(request, "Account created successfully")
        return redirect('/login')
    return render(request, 'emp_register.html')

def emp_blog_classic(request):
    return render(request, 'emp_blog_classic.html')

@login_required(login_url='/account/emp_login/')
def emp_search(request):
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

    return render(request, 'emp_search_results.html', {
        'query': query,
        'employee_profiles': employee_profiles,
        'employer_profiles': employer_profiles,
        'companies': companies,
    })

@login_required(login_url='/account/emp_login/')
def emp_public_employee_profile(request, username):
    profile = get_object_or_404(EmployeeProfile, user__username=username)
    employee = Employee.objects.filter(username=profile.user).first()
    photo_url = employee.photo.url if employee and employee.photo else None
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]
    return render(request, 'emp_public_employee_profile.html', {
        'profile': profile,
        'photo_url': photo_url,
        'skill_list': skill_list,
    })

@login_required(login_url='/account/emp_login/')
def emp_public_employer_profile(request, username):
    profile = get_object_or_404(EmployerProfile, user__username=username)
    employer = Employer.objects.filter(username=profile.user).first()
    photo_url = employer.photo.url if employer and employer.photo else None
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]
    return render(request, 'emp_public_employer_profile.html', {
        'profile': profile,
        'photo_url': photo_url,
        'skill_list': skill_list,
    })

def Logout(request):
    logout(request)
    messages.success(request, 'Logged Out Successfully!')
    return redirect('/')

def emp_browse_job_list(request):
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
    return render(request, 'emp_browse_job_list.html', {
        'jobs': jobs,
        'search_query': search_query,
        'search_location': search_location,
    })
