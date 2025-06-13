# Sistema de Estacionamiento y Autolavado

Sistema integral para la gestión de estacionamiento y servicios de autolavado.

## Características

- Gestión de espacios de estacionamiento
- Reservas de estacionamiento
- Servicios de autolavado
- Sistema de pagos
- Perfiles de usuario
- Generación de reportes

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd parking_system
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
STRIPE_SECRET_KEY=tu-clave-secreta-de-stripe
STRIPE_PUBLIC_KEY=tu-clave-publica-de-stripe
```

5. Aplicar migraciones:
```bash
python manage.py migrate
```

6. Crear un superusuario:
```bash
python manage.py createsuperuser
```

7. Iniciar el servidor de desarrollo:
```bash
python manage.py runserver
```

## Estructura del Proyecto

- `core/`: Modelos y configuraciones generales
- `parking/`: Gestión de estacionamiento
- `carwash/`: Servicios de autolavado
- `payments/`: Sistema de pagos
- `users/`: Gestión de usuarios
- `reports/`: Generación de reportes

## Uso

1. Acceder al panel de administración:
   - URL: http://localhost:8000/admin/
   - Usar las credenciales del superusuario

2. Crear ubicaciones de estacionamiento
3. Configurar servicios de autolavado
4. Gestionar usuarios y permisos
5. Monitorear reservas y pagos

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 