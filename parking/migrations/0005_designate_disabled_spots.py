from django.db import migrations

def designate_disabled_spots(apps, schema_editor):
    ParkingSpace = apps.get_model('parking', 'ParkingSpace')
    # Designar los primeros 4 espacios como espacios para discapacitados
    ParkingSpace.objects.filter(space_number__in=['1', '2', '3', '4']).update(is_disabled_spot=True)

def reverse_disabled_spots(apps, schema_editor):
    ParkingSpace = apps.get_model('parking', 'ParkingSpace')
    # Revertir la designación
    ParkingSpace.objects.filter(is_disabled_spot=True).update(is_disabled_spot=False)

class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0004_parkingspace_is_disabled_spot'),
    ]

    operations = [
        migrations.RunPython(designate_disabled_spots, reverse_disabled_spots),
    ] 