from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Employee(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_employee = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='profiles/employees/', blank=True, null=True)

class Employer(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_employer = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='profiles/employers/', blank=True, null=True)


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.CharField(max_length=50, blank=True)
    education = models.CharField(max_length=100, blank=True)
    highest_education = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.CharField(max_length=10, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    categories = models.CharField(max_length=200, blank=True)
    current_salary = models.CharField(max_length=50, blank=True)
    expected_salary = models.CharField(max_length=50, blank=True)
    expected_ctc = models.CharField(max_length=50, blank=True)
    notice_period = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    map_address = models.CharField(max_length=255, blank=True)
    latitude = models.CharField(max_length=50, blank=True)
    longitude = models.CharField(max_length=50, blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    skills = models.CharField(max_length=500, blank=True)
    preferred_locations = models.CharField(max_length=300, blank=True)
    preferred_job_titles = models.CharField(max_length=300, blank=True)
    preferred_job_types = models.CharField(max_length=200, blank=True)
    preferred_industries = models.CharField(max_length=300, blank=True)
    open_to_remote = models.BooleanField(default=False)
    open_to_hybrid = models.BooleanField(default=False)
    open_to_onsite = models.BooleanField(default=False)
    open_to_relocate = models.BooleanField(default=False)


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.CharField(max_length=50, blank=True)
    education = models.CharField(max_length=100, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    categories = models.CharField(max_length=200, blank=True)
    current_salary = models.CharField(max_length=50, blank=True)
    expected_salary = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    map_address = models.CharField(max_length=255, blank=True)
    latitude = models.CharField(max_length=50, blank=True)
    longitude = models.CharField(max_length=50, blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    skills = models.CharField(max_length=500, blank=True)


class UserSettings(models.Model):
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('recruiters', 'Recruiters only'),
        ('private', 'Private'),
    )

    THEME_CHOICES = (
        ('system', 'System'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_settings')
    notify_email_jobs = models.BooleanField(default=True)
    notify_email_applications = models.BooleanField(default=True)
    notify_email_news = models.BooleanField(default=False)
    notify_sms = models.BooleanField(default=False)
    notify_browser = models.BooleanField(default=True)
    profile_visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    show_email = models.BooleanField(default=True)
    allow_search_index = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    theme_preference = models.CharField(max_length=20, choices=THEME_CHOICES, default='system')
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    account_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Settings({self.user.username})'


class AppEmailConfig(models.Model):
    host = models.CharField(max_length=120, default='smtp.gmail.com')
    port = models.PositiveIntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    username = models.EmailField(blank=True)
    app_password = models.CharField(max_length=255, blank=True)
    from_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'AppEmailConfig(active={self.is_active})'

