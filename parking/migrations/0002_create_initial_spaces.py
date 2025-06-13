from django.db import migrations

def create_initial_spaces(apps, schema_editor):
    ParkingSpace = apps.get_model('parking', 'ParkingSpace')
    Location = apps.get_model('core', 'Location')
    
    # Crear una ubicación por defecto si no existe
    default_location, _ = Location.objects.get_or_create(
        name='Estacionamiento Principal',
        defaults={
            'address': 'Dirección Principal',
            'capacity': 20
        }
    )
    
    # Crear 20 espacios de estacionamiento
    for i in range(1, 21):
        ParkingSpace.objects.get_or_create(
            space_number=str(i),
            location=default_location,
            defaults={
                'is_occupied': False
            }
        )

def remove_initial_spaces(apps, schema_editor):
    ParkingSpace = apps.get_model('parking', 'ParkingSpace')
    Location = apps.get_model('core', 'Location')
    
    # Eliminar espacios
    ParkingSpace.objects.all().delete()
    # Eliminar ubicación por defecto
    Location.objects.filter(name='Estacionamiento Principal').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_spaces, remove_initial_spaces),
    ] 