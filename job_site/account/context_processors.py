from .models import UserSettings


def user_settings(request):
    if not request.user.is_authenticated:
        return {'user_settings': None}

    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    return {'user_settings': settings}
