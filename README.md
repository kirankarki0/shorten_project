# Shorten Project

Minimal Django URL shortener following KISS and DRY principles.

Quick start
1. Create virtualenv and install requirements
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run migrations and start server
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver

3. Visit http://127.0.0.1:8000/
