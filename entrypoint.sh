#!/bin/bash

# Esperar a que la base de datos esté lista
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar el servidor
python manage.py runserver 0.0.0.0:8000 