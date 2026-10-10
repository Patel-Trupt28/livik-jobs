from django.urls import path
from . import views

urlpatterns = [
    path('emp_index/', views.index, name='emp_index'),
    path('api/stats/', views.dashboard_stats, name='emp_stats'),
    path('emp_login/', views.login, name='emp_login'),
    path('emp_profile/', views.dprofile, name='emp_profile'),
    path('emp_post_job/', views.post_job, name='emp_post_job'),
    path('emp_recruiters/', views.recruiters, name='emp_recruiters'),
    path('emp_my_job_grid/', views.my_job_grid, name='emp_my_job_grid'),
    path('emp_settings/', views.settings, name='emp_settings'),
    path('emp_google_auth/', views.google_auth_mail, name='emp_google_auth'),
    path('gmail/connect/', views.gmail_oauth_connect, name='gmail_oauth_connect'),
    path('gmail/callback/', views.gmail_oauth_callback, name='gmail_oauth_callback'),
    path('gmail/disconnect/', views.gmail_oauth_disconnect, name='gmail_oauth_disconnect'),
    path('emp_upadte_job/', views.emp_update_job, name='emp_update_job'),
    path('emp_job_applications/', views.emp_job_applications, name='emp_job_applications'),
    # ADD THESE (missing earlier)
    path('edit_job/<int:job_id>/', views.emp_update_job, name='edit_job'),
    path('delete_job/<int:job_id>/', views.delete_job, name='delete_job'),
]
