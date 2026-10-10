import json
import secrets
import socket
import smtplib
from base64 import urlsafe_b64encode
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from dashb1.models import JobApplication
from account.models import Employer, EmployerProfile, UserSettings

from .models import EmployerEmailConfig, JOB_TYPE, Job


def _send_via_smtp(host, port, username, password, use_tls, from_email, to_email, subject, plain_body, html_body):
    connection = get_connection(
        host=host,
        port=port,
        username=username,
        password=password,
        use_tls=use_tls,
        use_ssl=False,
        timeout=20,
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=[to_email],
        connection=connection,
    )
    message.attach_alternative(html_body, 'text/html')
    return bool(message.send(fail_silently=False))


def _send_via_resend(api_key, from_email, to_email, subject, plain_body, html_body):
    payload = {
        'from': from_email,
        'to': [to_email],
        'subject': subject,
        'text': plain_body,
        'html': html_body,
    }
    encoded = json.dumps(payload).encode('utf-8')
    req = url_request.Request(
        url='https://api.resend.com/emails',
        data=encoded,
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'job-portal/1.0',
        },
    )

    try:
        with url_request.urlopen(req, timeout=20) as response:
            return 200 <= response.getcode() < 300
    except url_error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        lowered = body.lower()

        if exc.code == 401 or 'api key is invalid' in lowered:
            raise RuntimeError('Resend API key is invalid. Generate a new API key and update Settings.')

        # Common Resend setup issue: sender domain not verified / restricted sender.
        if exc.code == 403 and ('1010' in body or 'verify' in lowered or 'sender' in lowered):
            raise RuntimeError(
                'Resend rejected this sender. Use a verified domain sender in Resend, '
                'or use onboarding@resend.dev for test emails.'
            )
        raise RuntimeError(f'Resend API error {exc.code}: {body[:250]}')
    except url_error.URLError as exc:
        raise RuntimeError(f'Resend connection error: {exc.reason}')


def _normalize_smtp_host(host, username):
    normalized_host = (host or '').strip()
    normalized_user = (username or '').strip().lower()

    # Gmail accounts should always use Google's SMTP host.
    if normalized_user.endswith('@gmail.com'):
        return 'smtp.gmail.com'
    return normalized_host


GOOGLE_OAUTH_SCOPE = 'openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.send'
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GMAIL_SEND_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


def _get_google_oauth_credentials(email_config=None):
    # Website-level OAuth credentials are source of truth.
    client_id = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or '').strip()
    client_secret = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '') or '').strip()

    # Fallback to saved employer config if server-level values are not provided.
    if email_config:
        if not client_id:
            client_id = (email_config.google_client_id or '').strip()
        if not client_secret:
            client_secret = (email_config.google_client_secret or '').strip()
    return client_id, client_secret


def _sync_google_oauth_from_server(email_config):
    server_client_id = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or '').strip()
    server_client_secret = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '') or '').strip()

    if not server_client_id or not server_client_secret:
        return False

    update_fields = []
    if email_config.google_client_id != server_client_id:
        email_config.google_client_id = server_client_id
        update_fields.append('google_client_id')
    if email_config.google_client_secret != server_client_secret:
        email_config.google_client_secret = server_client_secret
        update_fields.append('google_client_secret')

    if update_fields:
        email_config.save(update_fields=update_fields + ['updated_at'])
    return True


def _is_google_client_id_format_valid(client_id):
    normalized = (client_id or '').strip()
    return normalized.endswith('.apps.googleusercontent.com')


def _looks_like_placeholder_oauth_values(client_id, client_secret):
    normalized_id = (client_id or '').strip().lower()
    normalized_secret = (client_secret or '').strip().lower()
    placeholder_markers = (
        'abcxyz',
        'example',
        'your_client',
        'replace_me',
        'test',
        'dummy',
    )
    if normalized_id.startswith('123456789012-'):
        return True
    if any(marker in normalized_id for marker in placeholder_markers):
        return True
    if any(marker in normalized_secret for marker in placeholder_markers):
        return True
    return False


def _build_google_auth_url(request, client_id, state):
    redirect_uri = request.build_absolute_uri(reverse('gmail_oauth_callback'))
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': GOOGLE_OAUTH_SCOPE,
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    }
    return f'{GOOGLE_AUTH_URL}?{url_parse.urlencode(params)}'


def _google_token_request(data):
    encoded = url_parse.urlencode(data).encode('utf-8')
    req = url_request.Request(
        GOOGLE_TOKEN_URL,
        data=encoded,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with url_request.urlopen(req, timeout=20) as response:
            payload = response.read().decode('utf-8', errors='ignore')
            return json.loads(payload)
    except url_error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        lowered = body.lower()
        if 'invalid_client' in lowered:
            raise RuntimeError(
                'Google OAuth client is invalid. Admin must fix GOOGLE_OAUTH_CLIENT_ID and '
                'GOOGLE_OAUTH_CLIENT_SECRET in website configuration, then retry.'
            )
        if 'invalid_grant' in lowered:
            raise RuntimeError('Google authorization expired. Please sign in with Google again.')
        raise RuntimeError(f'Google token API error {exc.code}: {body[:250]}')
    except url_error.URLError as exc:
        raise RuntimeError(f'Google token connection error: {exc.reason}')


def _refresh_google_access_token(email_config):
    if not email_config.google_refresh_token:
        raise RuntimeError('Gmail OAuth refresh token missing. Please reconnect Google account.')

    client_id, client_secret = _get_google_oauth_credentials(email_config)
    if not client_id or not client_secret:
        raise RuntimeError('Google OAuth client credentials are missing on server.')

    token_payload = _google_token_request({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': email_config.google_refresh_token,
        'grant_type': 'refresh_token',
    })

    access_token = token_payload.get('access_token')
    if not access_token:
        raise RuntimeError('Google token refresh failed. Please reconnect Google account.')

    expires_in = int(token_payload.get('expires_in', 3600))
    email_config.google_access_token = access_token
    email_config.google_token_expiry = timezone.now() + timedelta(seconds=max(60, expires_in - 30))
    email_config.save(update_fields=['google_access_token', 'google_token_expiry', 'updated_at'])
    return access_token


def _send_via_gmail_oauth(email_config, to_email, subject, plain_body, html_body):
    client_id, client_secret = _get_google_oauth_credentials(email_config)
    if not client_id or not client_secret:
        raise RuntimeError('Google OAuth client credentials are missing on server.')

    if not email_config.google_refresh_token:
        raise RuntimeError('Google account not connected. Use "Sign in with Google" in Settings.')

    access_token = email_config.google_access_token
    if not access_token or not email_config.google_token_expiry or email_config.google_token_expiry <= timezone.now():
        access_token = _refresh_google_access_token(email_config)

    from_email = (email_config.from_email or email_config.username or '').strip()
    if not from_email:
        raise RuntimeError('From Email is required for Gmail OAuth sending.')

    mime = MIMEMultipart('alternative')
    mime['To'] = to_email
    mime['From'] = from_email
    mime['Subject'] = subject
    mime.attach(MIMEText(plain_body, 'plain', 'utf-8'))
    mime.attach(MIMEText(html_body, 'html', 'utf-8'))

    raw_msg = urlsafe_b64encode(mime.as_bytes()).decode('utf-8')
    payload = json.dumps({'raw': raw_msg}).encode('utf-8')

    req = url_request.Request(
        GMAIL_SEND_URL,
        data=payload,
        method='POST',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with url_request.urlopen(req, timeout=20) as response:
            return 200 <= response.getcode() < 300
    except url_error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        lowered = body.lower()
        if exc.code == 403 and (
            'gmail api has not been used' in lowered
            or 'accessnotconfigured' in lowered
            or 'service_disabled' in lowered
            or 'api has not been used' in lowered
        ):
            raise RuntimeError(
                'Gmail API is disabled in your Google Cloud project. '
                'Enable Gmail API for the same project used by your OAuth Client ID, '
                'then wait 1-5 minutes and retry.'
            )
        if exc.code in (401, 403):
            # token revoked/expired; retry once with fresh token
            fresh_token = _refresh_google_access_token(email_config)
            retry_req = url_request.Request(
                GMAIL_SEND_URL,
                data=payload,
                method='POST',
                headers={
                    'Authorization': f'Bearer {fresh_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
            )
            try:
                with url_request.urlopen(retry_req, timeout=20) as retry_response:
                    return 200 <= retry_response.getcode() < 300
            except Exception:
                pass
        raise RuntimeError(f'Gmail API error {exc.code}: {body[:250]}')
    except url_error.URLError as exc:
        raise RuntimeError(f'Gmail API connection error: {exc.reason}')


def _google_fetch_user_email(access_token):
    req = url_request.Request(
        GOOGLE_USERINFO_URL,
        method='GET',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        },
    )
    try:
        with url_request.urlopen(req, timeout=20) as response:
            payload = response.read().decode('utf-8', errors='ignore')
            data = json.loads(payload)
            return (data.get('email') or '').strip()
    except Exception:
        return ''


def index(request):
    return render(request, 'emp_index1.html')


def _is_public_email_domain(email):
    if not email or '@' not in email:
        return False
    domain = email.split('@', 1)[1].lower()
    public_domains = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com',
        'icloud.com', 'aol.com', 'protonmail.com', 'zoho.com', 'yandex.com',
    }
    return domain in public_domains


def _has_strong_password(password):
    if not password:
        return False
    if len(password) < 10:
        return False
    if not any(ch.isupper() for ch in password):
        return False
    if not any(ch.isdigit() for ch in password):
        return False
    if not any(not ch.isalnum() for ch in password):
        return False
    return True


@login_required
def settings(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'all')

        if action == 'security':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            two_factor_enabled = request.POST.get('two_factor_enabled') == 'on'

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New password and confirmation do not match.')
            elif not _has_strong_password(new_password):
                messages.error(request, 'Password must be 10+ chars with uppercase, number, and special character.')
            elif not two_factor_enabled:
                messages.error(request, 'Two-factor authentication is required for employer accounts.')
            else:
                request.user.set_password(new_password)
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password updated successfully.')

            settings_obj.two_factor_enabled = two_factor_enabled
            settings_obj.save(update_fields=['two_factor_enabled'])

        elif action == 'notifications':
            settings_obj.notify_email_jobs = request.POST.get('notify_email_jobs') == 'on'
            settings_obj.notify_email_applications = request.POST.get('notify_email_applications') == 'on'
            settings_obj.notify_email_news = request.POST.get('notify_email_news') == 'on'
            settings_obj.notify_sms = request.POST.get('notify_sms') == 'on'
            settings_obj.notify_browser = request.POST.get('notify_browser') == 'on'
            if not any([
                settings_obj.notify_email_jobs,
                settings_obj.notify_email_applications,
                settings_obj.notify_email_news,
                settings_obj.notify_sms,
                settings_obj.notify_browser,
            ]):
                messages.error(request, 'Enable at least one notification channel.')
                return redirect('/dashboard2/emp_settings/')
            settings_obj.save(update_fields=[
                'notify_email_jobs',
                'notify_email_applications',
                'notify_email_news',
                'notify_sms',
                'notify_browser',
            ])
            messages.success(request, 'Notification settings saved.')

        elif action == 'privacy':
            settings_obj.profile_visibility = request.POST.get('profile_visibility', settings_obj.profile_visibility)
            settings_obj.show_email = request.POST.get('show_email') == 'yes'
            settings_obj.allow_search_index = request.POST.get('allow_search_index') == 'on'
            settings_obj.save(update_fields=[
                'profile_visibility',
                'show_email',
                'allow_search_index',
            ])
            messages.success(request, 'Privacy settings saved.')

        elif action == 'preferences':
            settings_obj.theme_preference = request.POST.get('theme_preference', settings_obj.theme_preference)
            settings_obj.language = request.POST.get('language', settings_obj.language)
            settings_obj.timezone = request.POST.get('timezone', settings_obj.timezone)
            if not settings_obj.timezone:
                messages.error(request, 'Timezone is required for interview scheduling.')
                return redirect('/dashboard2/emp_settings/')
            settings_obj.save(update_fields=['theme_preference', 'language', 'timezone'])
            messages.success(request, 'Preferences saved.')

        elif action == 'account':
            settings_obj.account_active = request.POST.get('account_active') == 'on'
            settings_obj.save(update_fields=['account_active'])
            messages.success(request, 'Account settings saved.')

        return redirect('/dashboard2/emp_settings/')

    return render(request, 'emp_settings.html', {'settings_obj': settings_obj})


def _month_start(value):
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_range(end, count=12):
    end_month = _month_start(end)
    start_month = _add_months(end_month, -(count - 1))
    months = []
    for offset in range(count):
        months.append(_add_months(start_month, offset))
    return months


def _series_for(qs, date_field, months):
    if not months:
        return []
    start = months[0]
    data = (
        qs.filter(**{f'{date_field}__gte': start})
        .annotate(month=TruncMonth(date_field))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    index = {item['month']: item['total'] for item in data}
    return [index.get(month, 0) for month in months]


@login_required
def dashboard_stats(request):
    now = timezone.now()
    months = _month_range(now, 12)
    labels = [month.strftime('%b') for month in months]

    jobs_qs = Job.objects.filter(user=request.user)
    applications_qs = JobApplication.objects.filter(job__user=request.user)

    metrics = {
        'total_jobs': jobs_qs.count(),
        'open_jobs': jobs_qs.filter(is_closed=False).count(),
        'closed_jobs': jobs_qs.filter(is_closed=True).count(),
        'total_applications': applications_qs.count(),
        'pending_applications': applications_qs.filter(status='pending').count(),
        'shortlisted_applications': applications_qs.filter(status='shortlisted').count(),
        'hired_applications': applications_qs.filter(status='hired').count(),
        'rejected_applications': applications_qs.filter(status='rejected').count(),
    }

    chart = {
        'labels': labels,
        'series': {
            'Jobs': _series_for(jobs_qs, 'created_at', months),
            'Applications': _series_for(applications_qs, 'created_at', months),
            'Hires': _series_for(applications_qs.filter(status='hired'), 'created_at', months),
        },
    }

    return JsonResponse({'metrics': metrics, 'chart': chart})


@login_required
def dprofile(request):
    profile, _ = EmployerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
        },
    )
    skill_list = [s.strip() for s in (profile.skills or '').split(',') if s.strip()]

    if request.method == 'POST':
        photo = request.FILES.get('profile_photo')
        if photo:
            employer = Employer.objects.filter(username=request.user).first()
            if employer:
                employer.photo = photo
                employer.save(update_fields=['photo'])
                messages.success(request, 'Profile photo updated.')
            else:
                messages.error(request, 'Employer profile not found.')

        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.email = request.POST.get('email', profile.email)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.website = request.POST.get('website', profile.website)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.experience_years = request.POST.get('experience_years', profile.experience_years)
        profile.education = request.POST.get('education', profile.education)
        profile.languages = request.POST.get('languages', profile.languages)
        profile.categories = request.POST.get('categories', profile.categories)
        profile.current_salary = request.POST.get('current_salary', profile.current_salary)
        profile.expected_salary = request.POST.get('expected_salary', profile.expected_salary)
        profile.country = request.POST.get('country', profile.country)
        profile.city = request.POST.get('city', profile.city)
        profile.address = request.POST.get('address', profile.address)
        profile.map_address = request.POST.get('map_address', profile.map_address)
        profile.latitude = request.POST.get('latitude', profile.latitude)
        profile.longitude = request.POST.get('longitude', profile.longitude)
        profile.facebook = request.POST.get('facebook', profile.facebook)
        profile.twitter = request.POST.get('twitter', profile.twitter)
        profile.instagram = request.POST.get('instagram', profile.instagram)
        profile.skills = request.POST.get('skills', profile.skills)
        profile.save()

        messages.success(request, 'Profile details saved.')
        return redirect('/dashboard2/emp_profile/')

    return render(request, 'emp_profile.html', {'profile': profile, 'skill_list': skill_list})


def login(request):
    return render(request, 'emp_login.html')


def recruiters(request):
    jobs = (
        Job.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .order_by('company_name', '-created_at')
    )

    company_map = {}
    for job in jobs:
        company = company_map.get(job.company_name)
        if company is None:
            company = {
                'name': job.company_name,
                'location': job.location or '',
                'logo': job.file_upload,
                'open_jobs': 0,
            }
            company_map[job.company_name] = company

        if not job.is_closed:
            company['open_jobs'] += 1

        if not company['logo'] and job.file_upload:
            company['logo'] = job.file_upload

        if not company['location'] and job.location:
            company['location'] = job.location

    companies = list(company_map.values())
    return render(request, 'emp_recruiters.html', {'companies': companies})


@login_required
def google_auth_mail(request):
    email_config, _ = EmployerEmailConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'username': request.user.email or '',
            'from_email': request.user.email or '',
        },
    )
    if email_config.provider != 'gmail_oauth':
        email_config.provider = 'gmail_oauth'
        email_config.save(update_fields=['provider', 'updated_at'])

    oauth_synced_from_server = _sync_google_oauth_from_server(email_config)
    connected_now = bool(email_config.google_refresh_token)
    if email_config.is_active != connected_now:
        email_config.is_active = connected_now
        email_config.save(update_fields=['is_active', 'updated_at'])

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'google_oauth_setup':
            if _sync_google_oauth_from_server(email_config):
                messages.success(request, 'Google OAuth credentials loaded automatically from website settings.')
                return redirect('/dashboard2/emp_google_auth/')

            # Fallback mode: allow saving credentials locally when server env is missing.
            google_client_id = request.POST.get('google_client_id', '').strip()
            google_client_secret = request.POST.get('google_client_secret', '').strip()

            if not google_client_id:
                google_client_id = (email_config.google_client_id or '').strip()
            if not google_client_secret:
                google_client_secret = (email_config.google_client_secret or '').strip()

            if not google_client_id or not google_client_secret:
                messages.error(
                    request,
                    'Google OAuth is missing. Add Google Client ID and Client Secret below, then retry.'
                )
                return redirect('/dashboard2/emp_google_auth/')

            if not _is_google_client_id_format_valid(google_client_id):
                messages.error(
                    request,
                    'Invalid Google Client ID format. It must end with ".apps.googleusercontent.com".'
                )
                return redirect('/dashboard2/emp_google_auth/')

            if _looks_like_placeholder_oauth_values(google_client_id, google_client_secret):
                messages.error(
                    request,
                    'These look like sample OAuth values, not real Google credentials. '
                    'Create a real OAuth Web Client in Google Cloud and paste those values.'
                )
                return redirect('/dashboard2/emp_google_auth/')

            email_config.google_client_id = google_client_id
            email_config.google_client_secret = google_client_secret
            email_config.save(update_fields=['google_client_id', 'google_client_secret', 'updated_at'])
            messages.success(request, 'Google OAuth credentials saved. You can now click Sign in with Google.')
            return redirect('/dashboard2/emp_google_auth/')

        if form_type == 'update_sender_email':
            sender_email = request.POST.get('sender_email', '').strip()
            if not sender_email or '@' not in sender_email:
                messages.error(request, 'Please enter a valid sender email.')
                return redirect('/dashboard2/emp_google_auth/')
            if _is_public_email_domain(sender_email):
                messages.error(request, 'Use a company email domain, not a public email address.')
                return redirect('/dashboard2/emp_google_auth/')
            if request.user.email and '@' in request.user.email:
                user_domain = request.user.email.split('@', 1)[1].lower()
                sender_domain = sender_email.split('@', 1)[1].lower()
                if sender_domain != user_domain:
                    messages.error(request, 'Sender email domain must match your account email domain.')
                    return redirect('/dashboard2/emp_google_auth/')

            email_config.from_email = sender_email
            email_config.save(update_fields=['from_email', 'updated_at'])
            messages.success(request, 'Sender email updated successfully.')
            return redirect('/dashboard2/emp_google_auth/')

        if form_type == 'delivery_status':
            messages.info(request, 'Delivery status is automatic. Connect Google to activate, disconnect to deactivate.')
            return redirect('/dashboard2/emp_google_auth/')

        if form_type == 'send_test_google':
            if not email_config.google_refresh_token:
                messages.error(request, 'Google account is not connected. Click "Sign in with Google" first.')
                return redirect('/dashboard2/emp_google_auth/')
            to_email = (email_config.from_email or request.user.email or '').strip()
            if not to_email:
                messages.error(request, 'Unable to determine destination email for test message.')
                return redirect('/dashboard2/emp_google_auth/')
            try:
                _send_via_gmail_oauth(
                    email_config=email_config,
                    to_email=to_email,
                    subject='Job Portal Gmail OAuth Test',
                    plain_body='Google sign-in setup is working. You can now send interview emails.',
                    html_body='<p>Google sign-in setup is working. You can now send interview emails.</p>',
                )
                messages.success(request, f'Test email sent to {to_email}.')
            except RuntimeError as exc:
                messages.error(request, str(exc))
            except Exception as exc:  # pragma: no cover
                messages.error(request, f'Test email failed: {exc}')
            return redirect('/dashboard2/emp_google_auth/')

    google_client_id, google_client_secret = _get_google_oauth_credentials(email_config)
    server_client_id = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or '').strip()
    server_client_secret = (getattr(django_settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '') or '').strip()
    google_client_from_server = bool(server_client_id and server_client_secret)
    masked_client_id = ''
    if google_client_id:
        masked_client_id = f'...{google_client_id[-24:]}' if len(google_client_id) > 24 else google_client_id

    return render(
        request,
        'emp_google_auth.html',
        {
            'email_config': email_config,
            'google_connected': bool(email_config.google_refresh_token),
            'delivery_active': bool(email_config.is_active),
            'google_client_configured': bool(google_client_id and google_client_secret),
            'google_oauth_auto_managed': oauth_synced_from_server,
            'google_client_from_server': google_client_from_server,
            'google_client_id_masked': masked_client_id,
            'oauth_callback_uri': request.build_absolute_uri(reverse('gmail_oauth_callback')),
        },
    )


@login_required
def gmail_oauth_connect(request):
    email_config, _ = EmployerEmailConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'username': request.user.email or '',
            'from_email': request.user.email or '',
        },
    )

    _sync_google_oauth_from_server(email_config)
    client_id, client_secret = _get_google_oauth_credentials(email_config)
    if not client_id or not client_secret:
        messages.error(
            request,
            'Google OAuth is not configured at website level. Admin must set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.'
        )
        return redirect('/dashboard2/emp_google_auth/')

    if not _is_google_client_id_format_valid(client_id):
        messages.error(
            request,
            'Google Client ID looks invalid. Use the full value from Google Cloud ending with ".apps.googleusercontent.com".'
        )
        return redirect('/dashboard2/emp_google_auth/')

    if _looks_like_placeholder_oauth_values(client_id, client_secret):
        messages.error(
            request,
            'Sample OAuth credentials detected. Replace with real Google Cloud OAuth Client ID and Client Secret.'
        )
        return redirect('/dashboard2/emp_google_auth/')

    state = f'{request.user.id}:{secrets.token_urlsafe(24)}'
    request.session['gmail_oauth_state'] = state
    auth_url = _build_google_auth_url(request, client_id, state)
    return redirect(auth_url)


@login_required
def gmail_oauth_callback(request):
    oauth_error = request.GET.get('error')
    if oauth_error:
        oauth_description = request.GET.get('error_description', '').strip()
        if oauth_error == 'invalid_client':
            messages.error(
                request,
                'Google OAuth client not found. Admin must fix website OAuth credentials and then retry Sign in with Google.'
            )
        elif oauth_error == 'access_denied':
            messages.error(
                request,
                'Google blocked access because OAuth app is in testing mode. '
                f'Add "{request.user.email}" as a Test user in Google Cloud OAuth consent screen, then retry.'
            )
        else:
            base_message = f'Google sign-in failed: {oauth_error}'
            if oauth_description:
                base_message = f'{base_message} ({oauth_description})'
            messages.error(request, base_message)
        return redirect('/dashboard2/emp_google_auth/')

    expected_state = request.session.get('gmail_oauth_state')
    returned_state = request.GET.get('state', '')
    if not expected_state or expected_state != returned_state:
        messages.error(request, 'Invalid Google OAuth state. Please retry sign-in.')
        return redirect('/dashboard2/emp_google_auth/')

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google did not return an authorization code.')
        return redirect('/dashboard2/emp_google_auth/')

    email_config, _ = EmployerEmailConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'username': request.user.email or '',
            'from_email': request.user.email or '',
        },
    )
    _sync_google_oauth_from_server(email_config)
    client_id, client_secret = _get_google_oauth_credentials(email_config)
    if not client_id or not client_secret:
        messages.error(request, 'Google OAuth is not configured on server.')
        return redirect('/dashboard2/emp_google_auth/')

    redirect_uri = request.build_absolute_uri(reverse('gmail_oauth_callback'))
    try:
        token_payload = _google_token_request({
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        })
    except RuntimeError as exc:
        messages.error(request, str(exc))
        return redirect('/dashboard2/emp_google_auth/')

    access_token = token_payload.get('access_token', '')
    refresh_token = token_payload.get('refresh_token', '')
    expires_in = int(token_payload.get('expires_in', 3600))
    if not access_token:
        messages.error(request, 'Google sign-in did not return an access token.')
        return redirect('/dashboard2/emp_google_auth/')

    signed_in_email = _google_fetch_user_email(access_token)

    # Keep existing refresh token if Google doesn't re-issue one.
    email_config.google_access_token = access_token
    if refresh_token:
        email_config.google_refresh_token = refresh_token
    email_config.google_token_expiry = timezone.now() + timedelta(seconds=max(60, expires_in - 30))
    email_config.provider = 'gmail_oauth'
    email_config.is_active = True
    previous_username = (email_config.username or '').strip()
    if signed_in_email:
        email_config.username = signed_in_email
        # Do not overwrite custom sender email if employer changed it manually.
        if not email_config.from_email or email_config.from_email == previous_username:
            email_config.from_email = signed_in_email
    elif not email_config.from_email:
        email_config.from_email = request.user.email or email_config.username
    email_config.save(update_fields=[
        'google_access_token',
        'google_refresh_token',
        'google_token_expiry',
        'provider',
        'is_active',
        'username',
        'from_email',
        'updated_at',
    ])

    request.session.pop('gmail_oauth_state', None)
    messages.success(request, 'Google account connected. Gmail OAuth is ready.')
    return redirect('/dashboard2/emp_google_auth/')


@login_required
def gmail_oauth_disconnect(request):
    email_config = EmployerEmailConfig.objects.filter(user=request.user).first()
    if not email_config:
        messages.info(request, 'No email settings found.')
        return redirect('/dashboard2/emp_settings/')

    email_config.google_access_token = ''
    email_config.google_refresh_token = ''
    email_config.google_token_expiry = None
    email_config.is_active = False
    if email_config.provider == 'gmail_oauth':
        email_config.provider = 'gmail_oauth'
    email_config.save(update_fields=[
        'google_access_token',
        'google_refresh_token',
        'google_token_expiry',
        'is_active',
        'provider',
        'updated_at',
    ])
    messages.success(request, 'Google account disconnected.')
    return redirect('/dashboard2/emp_settings/')


@login_required
def emp_job_applications(request):
    """List applications for the employer's jobs and handle shortlist toggles."""
    applications_qs = (
        JobApplication.objects
        .filter(job__user=request.user)
        .select_related('job')
        .order_by('-created_at')
    )

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        action = request.POST.get('action')
        application = get_object_or_404(JobApplication, id=app_id, job__user=request.user)

        if action == 'shortlist':
            application.status = 'shortlisted'
            application.is_shortlisted = True
            application.save(update_fields=['status', 'is_shortlisted', 'updated_at'])
            messages.success(request, f'{application.applicant_name} shortlisted for {application.job.job_title}.')
            return redirect('/dashboard2/emp_job_applications/')

        if action == 'unshortlist':
            application.status = 'pending'
            application.is_shortlisted = False
            application.save(update_fields=['status', 'is_shortlisted', 'updated_at'])
            messages.info(request, f'{application.applicant_name} moved back to pending.')
            return redirect('/dashboard2/emp_job_applications/')

        if action == 'hire':
            user_email_config = EmployerEmailConfig.objects.filter(
                user=request.user,
                is_active=True,
            ).first()

            email_mode = 'none'
            smtp_host = ''
            smtp_port = 587
            use_tls = True
            smtp_user = ''
            smtp_password = ''
            api_key = ''
            from_email = ''

            if (
                user_email_config
                and user_email_config.google_refresh_token
                and user_email_config.from_email
            ):
                email_mode = 'gmail_oauth'
                from_email = user_email_config.from_email.strip()
            elif user_email_config and user_email_config.provider == 'resend' and user_email_config.api_key and user_email_config.from_email:
                email_mode = 'resend'
                api_key = user_email_config.api_key
                from_email = user_email_config.from_email.strip()
            elif user_email_config and user_email_config.provider == 'smtp' and user_email_config.username and user_email_config.app_password:
                email_mode = 'smtp'
                smtp_host = _normalize_smtp_host(user_email_config.smtp_host, user_email_config.username)
                smtp_port = user_email_config.smtp_port
                use_tls = user_email_config.use_tls
                smtp_user = user_email_config.username
                smtp_password = user_email_config.app_password
                from_email = (user_email_config.from_email or smtp_user).strip()
                if smtp_user.lower().endswith('@gmail.com'):
                    from_email = smtp_user
            else:
                # Project-level SMTP fallback
                fallback_user = getattr(django_settings, 'EMAIL_HOST_USER', '')
                fallback_pass = getattr(django_settings, 'EMAIL_HOST_PASSWORD', '')
                fallback_from = (getattr(django_settings, 'DEFAULT_FROM_EMAIL', '') or fallback_user).strip()
                if fallback_user and fallback_pass and fallback_from:
                    email_mode = 'smtp'
                    smtp_host = _normalize_smtp_host(getattr(django_settings, 'EMAIL_HOST', 'smtp.gmail.com'), fallback_user)
                    smtp_port = getattr(django_settings, 'EMAIL_PORT', 587)
                    use_tls = getattr(django_settings, 'EMAIL_USE_TLS', True)
                    smtp_user = fallback_user
                    smtp_password = fallback_pass
                    from_email = fallback_from

            if email_mode == 'none':
                messages.error(
                    request,
                    'Email is not active. Open Settings, sign in with Google, and set delivery to Active.'
                )
                return redirect('/dashboard2/emp_job_applications/')

            subject = f'Interview Invitation - {application.job.job_title}'
            plain_body = (
                f'Dear {application.applicant_name},\n\n'
                f'Congratulations! You have been shortlisted for the position of {application.job.job_title} '
                f'at {application.job.company_name or "our company"}.\n\n'
                f'Next steps:\n'
                f'- We will contact you to schedule an interview.\n'
                f'- Please confirm your availability by replying to this email.\n'
                f'- Bring an updated resume and portfolio (if applicable).\n\n'
                f'Role summary:\n'
                f'- Job: {application.job.job_title}\n'
                f'- Location: {application.job.location or "Remote/Onsite to be discussed"}\n'
                f'- Job type: {application.job.job_type}\n'
                f'- Salary: {application.job.salary or "As discussed"}\n\n'
                f'If you have questions, reach us at {from_email}.\n\n'
                f'Best regards,\n{request.user.get_full_name() or request.user.username}'
            )
            # Public banner URL for a polished, branded email layout.
            banner_url = 'https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg?auto=compress&cs=tinysrgb&w=1200'
            html_body = f"""
                <div style="margin:0;padding:24px;background:#f3f6fb;font-family:Arial,sans-serif;">
                  <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e4ebf3;border-radius:14px;overflow:hidden;">
                    <img src="{banner_url}" alt="Interview Invitation" style="width:100%;height:200px;object-fit:cover;display:block;">
                    <div style="padding:24px;">
                      <h2 style="margin:0 0 10px;color:#13314d;">Interview Invitation</h2>
                      <p style="margin:0 0 14px;color:#2d445a;">Dear {application.applicant_name},</p>
                      <p style="margin:0 0 14px;color:#2d445a;">
                        Congratulations. You have been <strong>shortlisted</strong> for the role of
                        <strong>{application.job.job_title}</strong> at <strong>{application.job.company_name or "our company"}</strong>.
                      </p>
                      <div style="margin:18px 0;padding:14px;background:#f8fbff;border:1px solid #deebfb;border-radius:10px;">
                        <p style="margin:0 0 8px;color:#173b5c;"><strong>Role Summary</strong></p>
                        <p style="margin:0;color:#2d445a;">Job: {application.job.job_title}</p>
                        <p style="margin:4px 0 0;color:#2d445a;">Location: {application.job.location or "Remote/Onsite to be discussed"}</p>
                        <p style="margin:4px 0 0;color:#2d445a;">Job type: {application.job.job_type}</p>
                        <p style="margin:4px 0 0;color:#2d445a;">Salary: {application.job.salary or "As discussed"}</p>
                      </div>
                      <p style="margin:0 0 8px;color:#2d445a;"><strong>Next steps</strong></p>
                      <ul style="margin:0 0 14px 18px;padding:0;color:#2d445a;">
                        <li>We will contact you soon to schedule an interview.</li>
                        <li>Please reply with your preferred availability.</li>
                        <li>Bring your updated resume and portfolio (if applicable).</li>
                      </ul>
                      <p style="margin:0;color:#2d445a;">For queries, contact: {from_email}</p>
                      <p style="margin:14px 0 0;color:#2d445a;">Best regards,<br>{request.user.get_full_name() or request.user.username}</p>
                    </div>
                  </div>
                </div>
            """

            try:
                if email_mode == 'smtp':
                    sent = _send_via_smtp(
                        host=smtp_host,
                        port=smtp_port,
                        username=smtp_user,
                        password=smtp_password,
                        use_tls=use_tls,
                        from_email=from_email,
                        to_email=application.email,
                        subject=subject,
                        plain_body=plain_body,
                        html_body=html_body,
                    )
                elif email_mode == 'gmail_oauth':
                    sent = _send_via_gmail_oauth(
                        email_config=user_email_config,
                        to_email=application.email,
                        subject=subject,
                        plain_body=plain_body,
                        html_body=html_body,
                    )
                else:
                    try:
                        sent = _send_via_resend(
                            api_key=api_key,
                            from_email=from_email,
                            to_email=application.email,
                            subject=subject,
                            plain_body=plain_body,
                            html_body=html_body,
                        )
                    except RuntimeError as resend_error:
                        # Automatic fallback to SMTP if credentials are available.
                        fallback_host = ''
                        fallback_port = 587
                        fallback_tls = True
                        fallback_user = ''
                        fallback_password = ''
                        fallback_from = ''

                        if user_email_config and user_email_config.username and user_email_config.app_password:
                            fallback_host = user_email_config.smtp_host
                            fallback_port = user_email_config.smtp_port
                            fallback_tls = user_email_config.use_tls
                            fallback_user = user_email_config.username
                            fallback_password = user_email_config.app_password
                            fallback_from = (user_email_config.from_email or fallback_user).strip()
                        else:
                            fb_user = getattr(django_settings, 'EMAIL_HOST_USER', '')
                            fb_pass = getattr(django_settings, 'EMAIL_HOST_PASSWORD', '')
                            fb_from = (getattr(django_settings, 'DEFAULT_FROM_EMAIL', '') or fb_user).strip()
                            if fb_user and fb_pass and fb_from:
                                fallback_host = getattr(django_settings, 'EMAIL_HOST', 'smtp.gmail.com')
                                fallback_port = getattr(django_settings, 'EMAIL_PORT', 587)
                                fallback_tls = getattr(django_settings, 'EMAIL_USE_TLS', True)
                                fallback_user = fb_user
                                fallback_password = fb_pass
                                fallback_from = fb_from

                        if fallback_host and fallback_user and fallback_password and fallback_from:
                            if '@' in fallback_host and fallback_user.lower().endswith('@gmail.com'):
                                fallback_host = 'smtp.gmail.com'
                            sent = _send_via_smtp(
                                host=fallback_host,
                                port=fallback_port,
                                username=fallback_user,
                                password=fallback_password,
                                use_tls=fallback_tls,
                                from_email=fallback_from,
                                to_email=application.email,
                                subject=subject,
                                plain_body=plain_body,
                                html_body=html_body,
                            )
                            messages.warning(
                                request,
                                f'Resend failed ({resend_error}). Email delivered via SMTP fallback.'
                            )
                        else:
                            raise resend_error

                if sent:
                    application.status = 'hired'
                    application.is_shortlisted = True
                    application.save(update_fields=['status', 'is_shortlisted', 'updated_at'])
                    messages.success(request, f'Interview email sent successfully to {application.email}.')
                else:
                    messages.error(request, 'Email service returned 0; candidate was not marked hired.')
            except smtplib.SMTPAuthenticationError:
                # Attempt Resend API fallback if configured.
                if user_email_config and user_email_config.api_key and user_email_config.from_email:
                    try:
                        sent = _send_via_resend(
                            api_key=user_email_config.api_key,
                            from_email=user_email_config.from_email,
                            to_email=application.email,
                            subject=subject,
                            plain_body=plain_body,
                            html_body=html_body,
                        )
                        if sent:
                            application.status = 'hired'
                            application.is_shortlisted = True
                            application.save(update_fields=['status', 'is_shortlisted', 'updated_at'])
                            messages.warning(
                                request,
                                f'Gmail rejected credentials. Interview email sent via Resend API to {application.email}.'
                            )
                        else:
                            messages.error(
                                request,
                                'Gmail authentication failed and Resend fallback did not send. Update provider credentials in Settings.'
                            )
                    except Exception as fallback_exc:
                        messages.error(
                            request,
                            f'Gmail authentication failed and Resend fallback failed: {fallback_exc}'
                        )
                else:
                    messages.error(
                        request,
                        'Gmail authentication failed. Normal Gmail password is blocked by Google; use App Password or configure Resend API.'
                    )
            except socket.gaierror:
                messages.error(
                    request,
                    f'Email host lookup failed for "{smtp_host}". Use a valid SMTP host (for Gmail: smtp.gmail.com).'
                )
            except smtplib.SMTPException as exc:
                messages.error(request, f'SMTP error: {exc}')
            except RuntimeError as exc:
                messages.error(request, str(exc))
            except Exception as exc:  # pragma: no cover - best effort email
                messages.error(request, f'Email send failed: {exc}')
            return redirect('/dashboard2/emp_job_applications/')

        messages.error(request, 'Invalid action.')
        return redirect('/dashboard2/emp_job_applications/')

    paginator = Paginator(applications_qs, 20)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)

    context = {
        'applications': applications,
        'total_applications': applications_qs.count(),
        'shortlisted_count': applications_qs.filter(is_shortlisted=True).count(),
        'shortlisted_applications': applications_qs.filter(is_shortlisted=True),
    }
    return render(request, 'emp_job_applications.html', context)


@login_required
def post_job(request):
    if request.method == 'POST':
        pj = Job.objects.create(
            user=request.user,
            job_title=request.POST['job_title'],
            description=request.POST['job_description'],
            company_name=request.POST['company_name'],
            location=request.POST['job_location'],
            job_type=request.POST['workplace_type'],
            salary=request.POST['salary'],
            tags=request.POST['tags'],
            last_date=request.POST['last_date'],
            url=request.POST['job_url'],
            file_upload=request.FILES.get('file', None),
            is_published=request.POST.get('is_published') == 'true',
            is_closed=request.POST.get('is_closed') == 'true',
        )

        if pj:
            messages.success(request, 'Job posted successfully!')
        return redirect('/dashboard2/emp_my_job_grid/')

    return render(request, 'emp_post_job.html')


@login_required
def my_job_grid(request):
    jobs_list = Job.objects.filter(user=request.user).order_by('-created_at')
    for job in jobs_list:
        if job.tags:
            job.tag_list = [tag.strip() for tag in job.tags.split(',')]
        else:
            job.tag_list = []

    paginator = Paginator(jobs_list, 12)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    context = {
        'jobs': jobs,
        'total_jobs': jobs_list.count(),
    }
    return render(request, 'emp_my_job_grid.html', context)


@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('/dashboard2/emp_my_job_grid/')

    context = {'job': job}
    return render(request, 'emp_delete_job_confirm.html', context)


@login_required
def emp_update_job(request, job_id):
    pj = get_object_or_404(Job, id=job_id, user=request.user)
    if request.method == 'POST':
        pj.job_title = request.POST['job_title']
        pj.description = request.POST['job_description']
        pj.company_name = request.POST['company_name']
        pj.location = request.POST['job_location']
        pj.job_type = request.POST['workplace_type']
        pj.salary = request.POST['salary']
        pj.tags = request.POST['tags']
        pj.last_date = request.POST['last_date']
        pj.url = request.POST['job_url']
        pj.is_published = request.POST.get('is_published') == 'true'
        pj.is_closed = request.POST.get('is_closed') == 'true'

        file_upload = request.FILES.get('file')
        if file_upload:
            pj.file_upload = file_upload

        pj.save()
        return redirect('/dashboard2/emp_my_job_grid/')

    return render(request, 'emp_update_job.html', {'job': pj, 'job_types': JOB_TYPE})
