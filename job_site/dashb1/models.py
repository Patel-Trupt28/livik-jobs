from django.db import models


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )
    
    job = models.ForeignKey('dashb2.Job', on_delete=models.CASCADE, related_name='applications')
    applicant_user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='job_applications',
        null=True,
        blank=True
    )
    applicant_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    current_location = models.CharField(max_length=150, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='applications/resumes/', blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=20)
    is_shortlisted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'applicant_user'],
                name='unique_job_application_per_user',
                condition=models.Q(applicant_user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['job', 'email'],
                name='unique_job_application_per_email'
            ),
        ]

    def __str__(self):
        return f'{self.applicant_name} - {self.job.job_title}'
