
from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='dashb1_index'),
    path('api/stats/', views.dashboard_stats, name='dashb1_stats'),
    path('login/', views.login, name='dashb1_login'),
    path('profile/', views.dprofile, name='dashb1_profile'),
    path('recruiters/', views.recruiters, name='dashb1_recruiters'),
    path('my_job_grid/', views.my_job_grid, name='dashb1_my_job_grid'),
    path('settings/', views.settings, name='dashb1_settings'),
]

