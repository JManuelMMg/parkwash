# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media

# Copiar el código fuente
COPY . .

# Configurar variables de entorno necesarias
ENV DJANGO_SETTINGS_MODULE=parking_system.settings
ENV PYTHONUNBUFFERED=1
ENV DJANGO_CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
ENV DJANGO_CACHE_LOCATION=redis://redis:6379/1

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer el puerto
EXPOSE 8000

# Script de inicio
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Comando para ejecutar la aplicación
ENTRYPOINT ["/entrypoint.sh"] 