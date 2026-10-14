import os
import sys
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_site.settings')
django.setup()

from django.contrib.auth.models import User
from account.models import Employee, Employer, EmployeeProfile, EmployerProfile, UserSettings
from dashb2.models import Job

def seed():
    print("[*] Seeding database with clean, default accounts and sample data...")

    # 1. Admin Superuser
    admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@livikjobs.com'})
    admin_user.first_name = 'Admin'
    admin_user.last_name = 'Livik'
    admin_user.email = 'admin@livikjobs.com'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password('Admin@123')
    admin_user.save()
    
    Employee.objects.get_or_create(username=admin_user, defaults={'first_name': 'Admin', 'last_name': 'Livik', 'is_employee': True})
    Employer.objects.get_or_create(username=admin_user, defaults={'first_name': 'Admin', 'last_name': 'Livik', 'is_employer': True})
    EmployeeProfile.objects.get_or_create(user=admin_user, defaults={'full_name': 'Site Administrator', 'email': 'admin@livikjobs.com'})
    EmployerProfile.objects.get_or_create(user=admin_user, defaults={'full_name': 'Livik Administration', 'email': 'admin@livikjobs.com'})
    UserSettings.objects.get_or_create(user=admin_user)
    print("  [+] Admin superuser created/updated: admin / Admin@123")

    # 2. Candidate: Trupt Patel
    trupt_user, created = User.objects.get_or_create(username='trupt', defaults={'email': 'pateltrupt30@gmail.com'})
    trupt_user.first_name = 'Trupt'
    trupt_user.last_name = 'Patel'
    trupt_user.email = 'pateltrupt30@gmail.com'
    trupt_user.is_staff = False
    trupt_user.is_superuser = False
    trupt_user.set_password('Password@123')
    trupt_user.save()

    emp_trupt, _ = Employee.objects.get_or_create(
        username=trupt_user,
        defaults={'first_name': 'Trupt', 'last_name': 'Patel', 'is_employee': True}
    )
    prof_trupt, _ = EmployeeProfile.objects.get_or_create(
        user=trupt_user,
        defaults={
            'full_name': 'Trupt Patel',
            'email': 'pateltrupt30@gmail.com',
            'phone': '+91 9876543210',
            'bio': 'Full Stack Python & Django Developer specialized in high-performance web applications, cloud deployment, and database design.',
            'skills': 'Python, Django, React, PostgreSQL, REST APIs, Git, Docker, WhiteNoise',
            'experience_years': '3 Years',
            'highest_education': 'Bachelor of Technology',
            'institution': 'Gujarat Technological University',
            'graduation_year': '2024',
            'city': 'Ahmedabad',
            'country': 'India',
            'open_to_remote': True,
            'open_to_hybrid': True,
        }
    )
    UserSettings.objects.get_or_create(user=trupt_user)
    print("  [+] Candidate account created/updated: trupt (or pateltrupt30@gmail.com) / Password@123")

    # 3. Generic Candidate: Candidate
    cand_user, created = User.objects.get_or_create(username='candidate', defaults={'email': 'candidate@livikjobs.com'})
    cand_user.first_name = 'Alex'
    cand_user.last_name = 'Morgan'
    cand_user.email = 'candidate@livikjobs.com'
    cand_user.set_password('Password@123')
    cand_user.save()

    Employee.objects.get_or_create(username=cand_user, defaults={'first_name': 'Alex', 'last_name': 'Morgan', 'is_employee': True})
    EmployeeProfile.objects.get_or_create(
        user=cand_user,
        defaults={
            'full_name': 'Alex Morgan',
            'email': 'candidate@livikjobs.com',
            'bio': 'Frontend Developer & UI/UX enthusiast crafting accessible and responsive user experiences.',
            'skills': 'JavaScript, TypeScript, React, HTML5, CSS3, Tailwind CSS',
            'experience_years': '2 Years',
            'city': 'Mumbai',
            'country': 'India',
            'open_to_remote': True,
        }
    )
    UserSettings.objects.get_or_create(user=cand_user)
    print("  [+] Candidate demo account created/updated: candidate / Password@123")

    # 4. Employer Account: Employer
    empr_user, created = User.objects.get_or_create(username='employer', defaults={'email': 'employer@livikjobs.com'})
    empr_user.first_name = 'Livik'
    empr_user.last_name = 'Technologies'
    empr_user.email = 'employer@livikjobs.com'
    empr_user.set_password('Password@123')
    empr_user.save()

    Employer.objects.get_or_create(username=empr_user, defaults={'first_name': 'Livik', 'last_name': 'Technologies', 'is_employer': True})
    EmployerProfile.objects.get_or_create(
        user=empr_user,
        defaults={
            'full_name': 'Livik Technologies Inc.',
            'email': 'employer@livikjobs.com',
            'website': 'https://livikjobs.com',
            'bio': 'Fast-growing tech company building modern enterprise software and developer tooling.',
            'city': 'Bangalore',
            'country': 'India',
        }
    )
    UserSettings.objects.get_or_create(user=empr_user)
    print("  [+] Employer account created/updated: employer / Password@123")

    # 5. Sample Jobs
    deadline = date.today() + timedelta(days=45)
    sample_jobs = [
        {
            'job_title': 'Senior Python / Django Architect',
            'description': 'We are looking for a Senior Python Developer with deep experience in Django, REST APIs, and cloud deployments to lead backend architecture.',
            'tags': 'Python, Django, PostgreSQL, Cloud',
            'location': 'Remote / Hybrid',
            'job_type': 'Fulltime',
            'salary': 'Rs 18,00,000 - 24,00,000 / year',
            'company_name': 'Livik Technologies',
            'last_date': deadline,
            'is_published': True,
        },
        {
            'job_title': 'Frontend UI/UX Engineer',
            'description': 'Join our product team to craft state-of-the-art web interfaces using modern CSS, JavaScript, and responsive design systems.',
            'tags': 'React, CSS, JavaScript, UI/UX',
            'location': 'Bangalore, India',
            'job_type': 'Fulltime',
            'salary': 'Rs 12,00,000 - 16,00,000 / year',
            'company_name': 'Livik Technologies',
            'last_date': deadline,
            'is_published': True,
        },
        {
            'job_title': 'Junior Python Developer',
            'description': 'Great entry-level opportunity to work with senior mentors on Django web services, automation scripts, and database optimization.',
            'tags': 'Python, Django, SQLite, Git',
            'location': 'Remote',
            'job_type': 'Parttime',
            'salary': 'Rs 6,00,000 - 9,00,000 / year',
            'company_name': 'Livik Technologies',
            'last_date': deadline,
            'is_published': True,
        },
        {
            'job_title': 'DevOps & Cloud Engineer',
            'description': 'Responsible for CI/CD pipelines, Vercel/AWS serverless infrastructure, monitoring, and automated test deployments.',
            'tags': 'DevOps, Docker, CI/CD, AWS, Vercel',
            'location': 'Remote',
            'job_type': 'Fulltime',
            'salary': 'Rs 15,00,000 - 20,00,000 / year',
            'company_name': 'Livik Technologies',
            'last_date': deadline,
            'is_published': True,
        },
    ]

    for job_data in sample_jobs:
        job, created_job = Job.objects.get_or_create(
            user=empr_user,
            job_title=job_data['job_title'],
            defaults=job_data
        )
        if not created_job:
            for k, v in job_data.items():
                setattr(job, k, v)
            job.save()

    print(f"  [+] Sample jobs seeded: {Job.objects.count()} active job listings")
    print("\nDatabase seeding completed successfully!")

if __name__ == '__main__':
    seed()
