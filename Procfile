web: python manage.py migrate && gunicorn backend.wsgi --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --worker-class gevent
