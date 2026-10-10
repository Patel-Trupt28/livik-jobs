from django.urls import path
from . import views

urlpatterns = [
    path('', views.emp_index),
    path('emp/', views.emp_index),
    path('emp_about_us/', views.emp_about_us),
    path('emp_companies/', views.emp_companies),
    path('emp_dlogin/', views.emp_dlogin),
    path('emp_register/', views.emp_register),
    path('emp_blog_classic/', views.emp_blog_classic),
    path('emp_search/', views.emp_search),
    path('profile/employee/<str:username>/', views.emp_public_employee_profile),
    path('profile/employer/<str:username>/', views.emp_public_employer_profile),
    path('emp_browse_job_list/', views.emp_browse_job_list),
]
