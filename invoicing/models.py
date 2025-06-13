from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from parking.models import Reservation
from carwash.models import CarWashService

User = get_user_model()

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Service Categories"

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_time = models.DurationField(help_text="Estimated time to complete the service")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class Package(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    services = models.ManyToManyField(Service, related_name='packages')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def original_price(self):
        return sum(service.price for service in self.services.all())

    @property
    def discounted_price(self):
        return self.original_price * (1 - self.discount_percentage / 100)

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    invoice_number = models.CharField(max_length=20, unique=True)
    date_created = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pendiente'),
        ('PAID', 'Pagada'),
        ('OVERDUE', 'Vencida'),
        ('CANCELLED', 'Cancelada')
    ], default='PENDING')
    notes = models.TextField(blank=True, null=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Efectivo'),
            ('card', 'Tarjeta'),
            ('transfer', 'Transferencia')
        ],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.user.username}"

    def calculate_total(self):
        self.total_amount = sum(item.total_price for item in self.items.all())
        self.save()

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    carwash_service = models.ForeignKey(CarWashService, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"

    class Meta:
        verbose_name = 'Item de Factura'
        verbose_name_plural = 'Items de Factura'
