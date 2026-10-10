from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_employeeprofile_employerprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='expected_ctc',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='graduation_year',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='highest_education',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='institution',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='notice_period',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='open_to_hybrid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='open_to_onsite',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='open_to_relocate',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='open_to_remote',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='preferred_industries',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='preferred_job_titles',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='preferred_job_types',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='preferred_locations',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
