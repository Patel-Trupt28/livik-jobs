#!/bin/bash
# Install dependencies
python3 -m pip install -r requirements.txt || python -m pip install -r requirements.txt

# Run migrations if database is available
python3 job_site/manage.py migrate --noinput || python job_site/manage.py migrate --noinput

# Collect static files
python3 job_site/manage.py collectstatic --noinput || python job_site/manage.py collectstatic --noinput
