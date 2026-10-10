from django.contrib import admin
from account.models import Employee
from account.models import Employer

# Register your models here.

admin.site.register(Employee)
admin.site.register(Employer)