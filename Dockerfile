FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Settings need a key to load; this one only serves collectstatic.
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

RUN mkdir -p /data /data/media
VOLUME ["/data"]

EXPOSE 3000
# A first admin is created only from DJANGO_SUPERUSER_USERNAME, _EMAIL and
# _PASSWORD when they are set in the host's environment.
CMD ["sh", "-c", "python manage.py migrate --noinput && (python manage.py createsuperuser --noinput || true) && gunicorn config.wsgi:application --bind 0.0.0.0:3000 --workers 3 --timeout 120"]
