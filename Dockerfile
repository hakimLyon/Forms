FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

RUN mkdir -p /data /data/media
VOLUME ["/data"]

EXPOSE 3000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin','admin@thesisdefense.local','admin123')\" && gunicorn config.wsgi:application --bind 0.0.0.0:3000 --workers 3 --timeout 120"]
