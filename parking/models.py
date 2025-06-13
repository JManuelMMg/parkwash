from django.db import models
from core.models import Vehicle, Location
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# Create your models here.

class ParkingSpace(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    space_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    is_disabled_spot = models.BooleanField(default=False, verbose_name='Espacio para discapacitados')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('20.00'), verbose_name='Tarifa por hora')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('150.00'), verbose_name='Tarifa por día')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        spot_type = "♿ " if self.is_disabled_spot else ""
        return f"{spot_type}{self.location.name} - Espacio {self.space_number}"

    class Meta:
        verbose_name = 'Espacio de Estacionamiento'
        verbose_name_plural = 'Espacios de Estacionamiento'

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pendiente'),
        ('ACTIVE', 'Activa'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_cost(self):
        duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
        duration_hours = Decimal(str(duration_hours))
        # Si la duración es menor a 6 horas, usar tarifa por hora
        if duration_hours < 6:
            self.total_cost = duration_hours * self.space.hourly_rate
        else:
            # Calcular días completos y horas restantes
            days = int(duration_hours // 24)
            remaining_hours = duration_hours % 24
            # Si hay más de 6 horas restantes, contar como día completo
            if remaining_hours >= 6:
                days += 1
                remaining_hours = 0
            # Calcular costo total
            self.total_cost = (Decimal(days) * self.space.daily_rate) + (remaining_hours * self.space.hourly_rate)
        self.save()

    def __str__(self):
        return f"Reserva {self.id} - {self.vehicle.plate_number}"

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
