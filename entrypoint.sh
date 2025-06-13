#!/bin/bash

# Aplicar migraciones
echo "Applying migrations..."
python manage.py migrate

# Recolectar archivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Iniciar el servidor con Gunicorn
echo "Starting server..."
gunicorn park.wsgi:application --bind 0.0.0.0:$PORT