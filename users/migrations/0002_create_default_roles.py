from django.db import migrations
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def create_default_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    
    # Crear roles predefinidos
    roles = {
        'admin': {
            'description': 'Acceso total al sistema',
            'permissions': [
                'add_user', 'change_user', 'delete_user', 'view_user',
                'add_parkingspace', 'change_parkingspace', 'delete_parkingspace', 'view_parkingspace',
                'add_reservation', 'change_reservation', 'delete_reservation', 'view_reservation',
                'add_payment', 'change_payment', 'delete_payment', 'view_payment',
                'add_report', 'change_report', 'delete_report', 'view_report',
            ]
        },
        'manager': {
            'description': 'Gestión de operaciones diarias',
            'permissions': [
                'view_user',
                'add_parkingspace', 'change_parkingspace', 'view_parkingspace',
                'add_reservation', 'change_reservation', 'view_reservation',
                'add_payment', 'change_payment', 'view_payment',
                'add_report', 'view_report',
            ]
        },
        'staff': {
            'description': 'Personal operativo',
            'permissions': [
                'view_user',
                'view_parkingspace',
                'add_reservation', 'change_reservation', 'view_reservation',
                'add_payment', 'view_payment',
            ]
        },
        'client': {
            'description': 'Usuario regular',
            'permissions': [
                'view_parkingspace',
                'add_reservation', 'view_reservation',
                'add_payment', 'view_payment',
            ]
        }
    }

    for role_name, role_data in roles.items():
        role = Role.objects.create(
            name=role_name,
            description=role_data['description']
        )
        
        # Asignar permisos
        perms = []
        for perm_codename in role_data['permissions']:
            try:
                perm = Permission.objects.get(codename=perm_codename)
                perms.append(perm)
            except Permission.DoesNotExist:
                continue
        if hasattr(role, 'permissions'):
            role.permissions.set(perms)

def remove_default_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, remove_default_roles),
    ] 