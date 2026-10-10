from django.contrib.auth.models import User
from django.db import models


# Create your models here.
JOB_TYPE = (
    ('Fulltime', 'Fulltime'),
    ('Parttime', 'PartTime'),
    ('WorkFromhome', 'WorkFromhome'),
)
class Job(models.Model):
    user = models.ForeignKey(User, related_name='jobs', on_delete=models.CASCADE)  # better related_name
    job_title = models.CharField(max_length=300)
    description = models.TextField()  # Changed to TextField
    tags = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=300, blank=True)
    job_type = models.CharField(choices=JOB_TYPE, max_length=20)
    salary = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=300, blank=True)
    last_date = models.DateField()
    url = models.URLField(blank=True, null=True)  # ADD THIS LINE - make it optional
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    file_upload = models.ImageField(upload_to='job_logo', null=True, blank=True)

    def __str__(self):
        return self.job_title


class EmployerEmailConfig(models.Model):
    PROVIDER_CHOICES = (
        ('smtp', 'SMTP'),
        ('resend', 'Resend API'),
        ('gmail_oauth', 'Gmail OAuth'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_email_config')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='smtp')
    smtp_host = models.CharField(max_length=120, default='smtp.gmail.com')
    smtp_port = models.PositiveIntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    username = models.EmailField(blank=True)
    from_email = models.EmailField(blank=True)
    app_password = models.CharField(max_length=255, blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    google_client_id = models.CharField(max_length=255, blank=True)
    google_client_secret = models.CharField(max_length=255, blank=True)
    google_refresh_token = models.TextField(blank=True)
    google_access_token = models.TextField(blank=True)
    google_token_expiry = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'EmailConfig({self.user.username})'
