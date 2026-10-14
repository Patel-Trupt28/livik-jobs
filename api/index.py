import os
import sys
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
JOB_SITE_DIR = BASE_DIR / "job_site"

# Ensure Django project directories are importable
for path_str in [str(JOB_SITE_DIR), str(BASE_DIR)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# Environment configuration for Vercel
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_site.settings")
os.environ.setdefault("VERCEL", "1")

from django.core.wsgi import get_wsgi_application

# Vercel's Python runtime requires 'app' or 'application'
application = get_wsgi_application()
app = application
