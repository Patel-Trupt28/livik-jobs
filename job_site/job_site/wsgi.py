"""
WSGI config for job_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

for path_str in [str(BASE_DIR), str(ROOT_DIR)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_site.settings')

from django.core.wsgi import get_wsgi_application

# Vercel's Python runtime requires 'app' or 'application'
application = get_wsgi_application()
app = application

# Self-healing database bootstrap on serverless startup
def _bootstrap():
    try:
        from django.contrib.auth.models import User
        from django.core.management import call_command
        
        need_init = False
        try:
            if not User.objects.filter(username__in=['trupt', 'patel-trupt28', 'candidate']).exists():
                need_init = True
        except Exception:
            need_init = True

        if need_init:
            call_command('migrate', interactive=False)
            try:
                import seed_db
                seed_db.seed()
            except ImportError:
                try:
                    from job_site import seed_db
                    seed_db.seed()
                except Exception as seed_err:
                    print(f"Seed error: {seed_err}")
    except Exception as exc:
        print(f"Bootstrap error: {exc}")

_bootstrap()

