
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('index/', views.index),
    path('search/', views.global_search),
    path('job_my_resume/', views.job_my_resume),
    path('job_cv_manager/', views.job_cv_manager),
    path('about_us/', views.about_us),
    path('companies/', views.companies),
    path('browse_job_list/', views.browse_job_list),
    path('chat/', views.chat_response),
    path('profile/employee/<str:username>/', views.public_employee_profile),
    path('profile/employer/<str:username>/', views.public_employer_profile),
    # path('login/', views.dlogin),
    # path('register/', views.register),
    path('contact/', views.contact),
    path('blog_classic/', views.blog_classic),
    path('logout/',views.Logout),

]

