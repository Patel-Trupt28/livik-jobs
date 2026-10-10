from django.urls import path
from .views import employeeregistration, employeelogin, employerregistration, employerlogin, employer_logout, employee_logout, smtp_settings

app_name = 'account'

urlpatterns = [
    path('register/', employeeregistration, name='register'),
    path('login/', employeelogin, name='login'),
    path('emp_register/', employerregistration, name='emp_register'),
    path('emp_login/', employerlogin, name='emp_login'),
    path('smtp_settings/', smtp_settings, name='smtp_settings'),
    path('emp_logout/', employer_logout),
    path('emp1_logout/',employee_logout),
]
