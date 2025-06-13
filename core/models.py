from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=10, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=[
        ('CAR', 'Car'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('TRUCK', 'Truck')
    ])
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.plate_number

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
