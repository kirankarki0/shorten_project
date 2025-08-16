# URL Shortener Project

This is a **minimal Django URL shortener** application that follows the **KISS (Keep It Simple, Stupid)** and **DRY (Don't Repeat Yourself)** principles. The project provides a clean, straightforward solution for creating shortened URLs with basic analytics tracking.

## Quick start
1. Create virtualenv and install requirements
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run migrations and start server
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver

3. Visit http://127.0.0.1:8000/