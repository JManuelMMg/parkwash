from django.db import models
from core.models import Vehicle

# Create your models here.

class CarWashService(models.Model):
    SERVICE_TYPES = [
        ('BASIC_WASH', 'Lavado Básico'),
        ('WAX', 'Encerado'),
        ('INTERIOR', 'Limpieza Interior'),
        ('FULL_SERVICE', 'Servicio Completo'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='services', null=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, default='BASIC_WASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.vehicle.plate_number if self.vehicle else 'Sin vehículo'}"

    class Meta:
        verbose_name = 'Servicio de Autolavado'
        verbose_name_plural = 'Servicios de Autolavado'

class Appointment(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service = models.ForeignKey(CarWashService, on_delete=models.CASCADE)
    appointment_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Programada'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada')
    ], default='SCHEDULED')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.service.name}"

    class Meta:
        verbose_name = 'Cita de Autolavado'
        verbose_name_plural = 'Citas de Autolavado'
