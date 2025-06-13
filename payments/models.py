from django.db import models
from parking.models import Reservation
from carwash.models import Appointment
from django.contrib.auth.models import User

class Payment(models.Model):
    reservation = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.SET_NULL)
    appointment = models.ForeignKey(Appointment, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[
        ('CASH', 'Efectivo'),
        ('CARD', 'Tarjeta'),
        ('DIGITAL', 'Billetera Digital')
    ])
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
        ('REFUNDED', 'Reembolsado')
    ], default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pago {self.id} - ${self.amount}"

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
