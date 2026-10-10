from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F


def dedupe_existing(apps, schema_editor):
    JobApplication = apps.get_model('dashb1', 'JobApplication')

    # Remove duplicate by (job, email) keeping lowest id (earliest)
    seen = set()
    for app in JobApplication.objects.order_by('id').values('id', 'job_id', 'email'):
        key = (app['job_id'], app['email'].lower() if app['email'] else '')
        if key in seen:
            JobApplication.objects.filter(id=app['id']).delete()
        else:
            seen.add(key)

    # Remove duplicate by (job, applicant_user) where user is set
    seen_user = set()
    for app in JobApplication.objects.filter(applicant_user__isnull=False).order_by('id').values('id', 'job_id', 'applicant_user_id'):
        key = (app['job_id'], app['applicant_user_id'])
        if key in seen_user:
            JobApplication.objects.filter(id=app['id']).delete()
        else:
            seen_user.add(key)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('dashb1', '0002_jobapplication_is_shortlisted_jobapplication_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='applicant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_applications', to='auth.user'),
        ),
        migrations.RunPython(dedupe_existing, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(condition=models.Q(('applicant_user__isnull', False)), fields=('job', 'applicant_user'), name='unique_job_application_per_user'),
        ),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(fields=('job', 'email'), name='unique_job_application_per_email'),
        ),
    ]
