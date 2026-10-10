from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company_name', 'location', 'job_type', 'user', 'last_date', 'is_published']
    list_filter = ['job_type', 'is_published', 'is_closed']
    search_fields = ['job_title', 'company_name', 'location']