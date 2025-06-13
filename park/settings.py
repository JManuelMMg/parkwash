import os
import dj_database_url
from pathlib import Path

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.RoleAssignmentMiddleware',
    'users.middleware.AuditMiddleware',
    'users.middleware.TwoFactorAuthMiddleware',
] 

# Configuración de Email
EMAIL_BACKEND = 'contactoisfaj@gmail.com'
EMAIL_HOST = 'contactoisfaj@gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contactoisfaj@gmail.com'
EMAIL_HOST_PASSWORD = 'aorf dfzp wxwo ykos'
DEFAULT_FROM_EMAIL = 'contactoisfaj@gmail.com'
ADMIN_EMAIL = 'contactoisfaj@gmail.com'  # Email del administrador para notificaciones

# Configuración de Sesión
SESSION_COOKIE_AGE = 3600  # 1 hora en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True  # Solo enviar cookies por HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso a cookies por JavaScript

# Configuración de Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'users': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuración de Autenticación de Dos Factores
TWO_FACTOR_AUTH = {
    'ENABLED': True,
    'REQUIRED_FOR_ADMIN': True,
    'REQUIRED_FOR_STAFF': True,
    'SESSION_EXPIRY': 3600,  # 1 hora en segundos
    'BACKUP_CODES_COUNT': 10,
    'BACKUP_CODES_LENGTH': 8,
}

# Configuración de Notificaciones
NOTIFICATION_SETTINGS = {
    'ENABLE_EMAIL_NOTIFICATIONS': True,
    'ENABLE_PUSH_NOTIFICATIONS': False,
    'DEFAULT_NOTIFICATION_TYPES': ['RESERVATION', 'PAYMENT', 'SYSTEM'],
}

# Configuración de Preferencias de Usuario
USER_PREFERENCES = {
    'DEFAULT_THEME': 'light',
    'AVAILABLE_THEMES': ['light', 'dark', 'system'],
    'DEFAULT_NOTIFICATION_PREFERENCES': {
        'RESERVATION': True,
        'PAYMENT': True,
        'SYSTEM': True,
    },
}

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
} 