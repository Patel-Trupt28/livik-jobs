from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone
from django.conf import settings as django_settings
from django.utils.crypto import get_random_string
from django.core.mail import EmailMultiAlternatives, get_connection
from datetime import timedelta
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages

from account.models import Employee, Employer, EmployeeProfile, EmployerProfile, UserSettings, AppEmailConfig


OTP_EXPIRY_MINUTES = 5


def _is_smtp_configured():
    app_cfg = AppEmailConfig.objects.first()
    if app_cfg and app_cfg.is_active:
        if app_cfg.username and app_cfg.app_password:
            return True
    host_user = getattr(django_settings, 'EMAIL_HOST_USER', '')
    host_pw = getattr(django_settings, 'EMAIL_HOST_PASSWORD', '')
    if host_user and host_pw:
        return True
    return False


def _normalize_smtp_secret(value):
    return ''.join((value or '').split())


def _resolve_smtp_sender(config):
    username = (config.username or '').strip()
    from_email = (config.from_email or username).strip()
    if 'gmail.com' in (config.host or '').lower():
        return username
    return from_email or username


def _validate_smtp_config(config):
    if not config.username or not config.app_password:
        return 'SMTP credentials are missing in SMTP Settings.'
    if 'gmail.com' in (config.host or '').lower():
        normalized_password = _normalize_smtp_secret(config.app_password)
        if len(normalized_password) != 16:
            return f'Gmail App Password must be 16 characters. Detected {len(normalized_password)} characters after removing spaces.'
    return ''


def _send_login_otp(email, code):
    subject = 'Your Login OTP'
    plain_body = f'Your login OTP is: {code}. It expires in {OTP_EXPIRY_MINUTES} minutes.'
    html_body = f'<p>Your login OTP is: <strong>{code}</strong>. It expires in {OTP_EXPIRY_MINUTES} minutes.</p>'
    app_cfg = AppEmailConfig.objects.first()
    if app_cfg and app_cfg.is_active:
        validation_error = _validate_smtp_config(app_cfg)
        if validation_error:
            return False, validation_error
        from_email = _resolve_smtp_sender(app_cfg)
        use_tls = app_cfg.use_tls and not app_cfg.use_ssl
        connection = get_connection(
            host=app_cfg.host,
            port=app_cfg.port,
            username=app_cfg.username,
            password=_normalize_smtp_secret(app_cfg.app_password),
            use_tls=use_tls,
            use_ssl=app_cfg.use_ssl,
            timeout=20,
        )
        msg = EmailMultiAlternatives(subject, plain_body, from_email=from_email, to=[email], connection=connection)
    else:
        from_email = (getattr(django_settings, 'DEFAULT_FROM_EMAIL', '') or getattr(django_settings, 'EMAIL_HOST_USER', '') or '').strip()
        if not getattr(django_settings, 'EMAIL_HOST_USER', '') or not getattr(django_settings, 'EMAIL_HOST_PASSWORD', ''):
            return False, 'SMTP credentials are missing. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (Gmail App Password).'
        msg = EmailMultiAlternatives(subject, plain_body, from_email=from_email or None, to=[email])
    msg.attach_alternative(html_body, 'text/html')
    try:
        sent_count = msg.send(fail_silently=False)
        if sent_count and sent_count > 0:
            return True, ''
        return False, 'Email backend returned 0 (not sent).'
    except Exception as exc:
        return False, str(exc)


def _send_test_email(config, to_email):
    subject = 'SMTP Test Email'
    plain_body = 'This is a test email from your SMTP settings.'
    html_body = '<p>This is a test email from your SMTP settings.</p>'
    validation_error = _validate_smtp_config(config)
    if validation_error:
        return False, validation_error
    from_email = _resolve_smtp_sender(config)
    use_tls = config.use_tls and not config.use_ssl
    connection = get_connection(
        host=config.host,
        port=config.port,
        username=config.username,
        password=_normalize_smtp_secret(config.app_password),
        use_tls=use_tls,
        use_ssl=config.use_ssl,
        timeout=20,
    )
    msg = EmailMultiAlternatives(subject, plain_body, from_email=from_email, to=[to_email], connection=connection)
    msg.attach_alternative(html_body, 'text/html')
    try:
        sent_count = msg.send(fail_silently=False)
        if sent_count and sent_count > 0:
            return True, ''
        return False, 'Email backend returned 0 (not sent).'
    except Exception as exc:
        return False, str(exc)


def _start_otp_flow(request, user, next_url, role):
    if not user.email:
        messages.error(request, 'Email not found on your account. Please contact support.')
        return redirect('/account/login/' if role == 'employee' else '/account/emp_login/')

    otp_code = get_random_string(length=6, allowed_chars='0123456789')
    sent, error_message = _send_login_otp(user.email, otp_code)
    if not sent:
        messages.error(request, 'Unable to send OTP email. Please configure SMTP email settings and try again.')
        if error_message:
            messages.warning(request, f'Email error: {error_message}')
        if getattr(django_settings, 'DEBUG', False):
            messages.warning(request, f'DEBUG OTP: {otp_code}')
        else:
            return redirect('/account/login/' if role == 'employee' else '/account/emp_login/')

    request.session['otp_user_id'] = user.id
    request.session['otp_code'] = otp_code
    request.session['otp_expires_at'] = (timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    request.session['otp_next'] = next_url or ''
    request.session['otp_role'] = role
    return render(
        request,
        'login.html' if role == 'employee' else 'emp_login.html',
        {'next': next_url, 'show_otp': True}
    )


def smtp_settings(request):
    config, _ = AppEmailConfig.objects.get_or_create(id=1)

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        config.host = request.POST.get('host', config.host).strip() or 'smtp.gmail.com'
        config.port = int(request.POST.get('port', config.port) or 587)
        config.use_tls = request.POST.get('use_tls') == 'on'
        config.use_ssl = request.POST.get('use_ssl') == 'on'
        config.username = request.POST.get('username', '').strip().lower()
        submitted_password = request.POST.get('smtp_secret_key', '')
        if submitted_password.strip():
            config.app_password = _normalize_smtp_secret(submitted_password)
        elif action == 'test':
            config.app_password = ''
        config.from_email = request.POST.get('from_email', '').strip().lower()
        config.is_active = request.POST.get('is_active') == 'on'
        config.save()
        if action == 'test':
            test_email = request.POST.get('test_email', '').strip()
            if not test_email:
                messages.error(request, 'Enter a test email address.')
                return redirect('/account/smtp_settings/')
            if not submitted_password.strip():
                messages.error(request, 'Paste a Gmail App Password before sending a test email.')
                return redirect('/account/smtp_settings/')
            sent, error_message = _send_test_email(config, test_email)
            if sent:
                messages.success(request, f'Test email sent to {test_email}.')
            else:
                messages.error(request, 'Unable to send test email.')
                if error_message:
                    messages.warning(request, f'Email error: {error_message}')
            return redirect('/account/smtp_settings/')
        messages.success(request, 'SMTP settings saved.')
        return redirect('/account/smtp_settings/')

    return render(request, 'smtp_settings.html', {'config': config})


def _verify_otp(request, role):
    otp_code = (request.POST.get('otp_code') or '').strip()
    session_code = request.session.get('otp_code')
    session_user_id = request.session.get('otp_user_id')
    expires_at_raw = request.session.get('otp_expires_at')
    next_url = request.session.get('otp_next') or ''
    session_role = request.session.get('otp_role')

    if session_role != role or not session_user_id or not session_code or not expires_at_raw:
        messages.error(request, 'OTP session expired. Please log in again.')
        return None, None

    try:
        expires_at = timezone.datetime.fromisoformat(expires_at_raw)
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())
    except Exception:
        expires_at = timezone.now() - timedelta(seconds=1)

    if timezone.now() > expires_at:
        messages.error(request, 'OTP expired. Please log in again.')
        return None, None

    if otp_code != session_code:
        messages.error(request, 'Invalid OTP. Please try again.')
        return None, None

    try:
        user = User.objects.get(id=session_user_id)
    except User.DoesNotExist:
        messages.error(request, 'Account not found. Please log in again.')
        return None, None

    # Clear OTP session
    for key in ('otp_user_id', 'otp_code', 'otp_expires_at', 'otp_next', 'otp_role'):
        if key in request.session:
            del request.session[key]

    return user, next_url


def employeeregistration(request):
    if request.method == 'POST':
        fname = request.POST.get('dzName', '').strip()
        lname = request.POST.get('dzLname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('dzPassword', '')
        photo = request.FILES.get('user_photo')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('/account/register/')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username is already taken. Please choose another.")
            return redirect('/account/register/')

        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists. Please log in.")
            return redirect('/account/register/')

        # create user
        myuser = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()

        # create employee
        Employee.objects.create(
            username=myuser,
            password=password,
            first_name=fname,
            last_name=lname,
            is_employee=True,
            photo=photo
        )

        EmployeeProfile.objects.get_or_create(
            user=myuser,
            defaults={
                'full_name': f"{fname} {lname}".strip() or username,
                'email': email,
            }
        )
        UserSettings.objects.get_or_create(user=myuser)

        messages.success(request, "Your account has been successfully created. You can now log in.")
        return redirect('/account/login/')

    return render(request, 'register.html')


def employeelogin(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        if request.POST.get('otp_code'):
            user, next_url = _verify_otp(request, 'employee')
            if not user:
                return render(request, 'login.html', {'next': next_url, 'show_otp': True})
            is_emp = Employee.objects.filter(username=user).exists()
            if is_emp or user.is_staff or user.is_superuser:
                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('/')
            messages.error(request, "You are not registered as an employee")
            return redirect('/account/login/')

        identifier = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        if '@' in identifier:
            user_lookup = User.objects.filter(email__iexact=identifier).first()
        else:
            user_lookup = User.objects.filter(username__iexact=identifier).first()

        if not user_lookup:
            messages.error(request, "Account not found. Please verify your credentials or register.")
            return redirect('/account/login/')

        user = authenticate(username=user_lookup.username, password=password)

        if user is not None:
            is_emp = Employee.objects.filter(username=user).exists()
            if is_emp or user.is_staff or user.is_superuser:
                if not is_emp:
                    Employee.objects.get_or_create(
                        username=user,
                        defaults={
                            'password': '',
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_employee': True,
                        }
                    )

                # Check if Two-Factor Authentication is requested and SMTP is configured
                user_settings = getattr(user, 'user_settings', None)
                requires_2fa = user_settings.two_factor_enabled if user_settings else False
                if requires_2fa and _is_smtp_configured():
                    return _start_otp_flow(request, user, next_url, 'employee')

                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('/')
            else:
                messages.error(request, "You are not registered as an employee")
        else:
            messages.error(request, "Invalid username or password")

        return redirect('/account/login/')

    return render(request, 'login.html', {'next': next_url})


def employerregistration(request):
    if request.method == 'POST':
        fname = request.POST.get('dzName1', '').strip()
        lname = request.POST.get('dzLname1', '').strip()
        username = request.POST.get('username1', '').strip()
        email = request.POST.get('email1', '').strip()
        password = request.POST.get('dzPassword1', '')
        photo = request.FILES.get('employer_photo')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('/account/emp_register/')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username is already taken. Please choose another.")
            return redirect('/account/emp_register/')

        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists. Please log in.")
            return redirect('/account/emp_register/')

        # create user
        myuser = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()

        # create employer
        Employer.objects.create(
            username=myuser,
            password=password,
            first_name=fname,
            last_name=lname,
            is_employer=True,
            photo=photo
        )

        EmployerProfile.objects.get_or_create(
            user=myuser,
            defaults={
                'full_name': f"{fname} {lname}".strip() or username,
                'email': email,
            }
        )
        UserSettings.objects.get_or_create(user=myuser)

        messages.success(request, "Your employer account has been successfully created. You can now log in.")
        return redirect('/account/emp_login/')

    return render(request, 'emp_register.html')


def employerlogin(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        if request.POST.get('otp_code'):
            user, next_url = _verify_otp(request, 'employer')
            if not user:
                return render(request, 'emp_login.html', {'next': next_url, 'show_otp': True})
            is_empr = Employer.objects.filter(username=user).exists()
            if is_empr or user.is_staff or user.is_superuser:
                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('/employer/emp')
            messages.error(request, "You are not registered as an employer")
            return redirect('/account/emp_login/')

        identifier = (request.POST.get('username1') or '').strip()
        password = request.POST.get('password1') or ''

        if '@' in identifier:
            user_lookup = User.objects.filter(email__iexact=identifier).first()
        else:
            user_lookup = User.objects.filter(username__iexact=identifier).first()

        if not user_lookup:
            messages.error(request, "Account not found. Please verify your credentials or register.")
            return redirect('/account/emp_login/')

        user = authenticate(username=user_lookup.username, password=password)

        if user is not None:
            is_empr = Employer.objects.filter(username=user).exists()
            if is_empr or user.is_staff or user.is_superuser:
                if not is_empr:
                    Employer.objects.get_or_create(
                        username=user,
                        defaults={
                            'password': '',
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_employer': True,
                        }
                    )

                # Check if Two-Factor Authentication is requested and SMTP is configured
                user_settings = getattr(user, 'user_settings', None)
                requires_2fa = user_settings.two_factor_enabled if user_settings else False
                if requires_2fa and _is_smtp_configured():
                    return _start_otp_flow(request, user, next_url, 'employer')

                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('/employer/emp')
            else:
                messages.error(request, "You are not registered as an employer")
        else:
            messages.error(request, "Invalid username or password")

        return redirect('/account/emp_login/')

    return render(request, 'emp_login.html', {'next': next_url})


def employer_logout(request):
    logout(request)
    return redirect('/employer/emp')

def employee_logout(request):
    logout(request)
    return redirect('/')
