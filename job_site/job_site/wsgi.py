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

application = get_wsgi_application()
app = application

