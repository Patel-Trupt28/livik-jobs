import os
import sys
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOB_SITE_DIR = BASE_DIR / "job_site"

# Ensure job_site and its root are importable
sys.path.insert(0, str(JOB_SITE_DIR))
sys.path.insert(0, str(BASE_DIR))

# Tell Django which settings module to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_site.settings")
os.environ.setdefault("NETLIFY", "true")

import serverless_wsgi
from job_site.wsgi import application

def handler(event, context):
    """
    Netlify Serverless Function Handler
    Converts AWS Lambda API Gateway / Netlify proxy events to WSGI and runs Django.
    """
    return serverless_wsgi.handle_request(application, event, context)
