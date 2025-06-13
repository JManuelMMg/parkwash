from django.db import models
from django.contrib.auth.models import User, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, verbose_name='Número de Teléfono', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dirección')
    car_brand = models.CharField(max_length=50, verbose_name='Marca del Vehículo', blank=True, null=True)
    car_model = models.CharField(max_length=50, verbose_name='Modelo del Vehículo', blank=True, null=True)
    license_plate = models.CharField(max_length=10, verbose_name='Placas', blank=True, null=True)
    car_photo = models.ImageField(upload_to='car_photos/', blank=True, null=True, verbose_name='Foto del Vehículo')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

class UserRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'Sin rol'}"

    class Meta:
        verbose_name = 'Rol de Usuario'
        verbose_name_plural = 'Roles de Usuario'

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('PERMISSION_CHANGE', 'Cambio de permisos'),
        ('ROLE_CHANGE', 'Cambio de rol'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-created_at']

class UserNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('RESERVATION', 'Reserva'),
        ('PAYMENT', 'Pago'),
        ('SYSTEM', 'Sistema'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_parking_locations = models.JSONField(default=list)
    notification_preferences = models.JSONField(default=dict)
    theme_preference = models.CharField(max_length=20, default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preferencia de Usuario'
        verbose_name_plural = 'Preferencias de Usuario'

class UserVehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=20)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vehículo de Usuario'
        verbose_name_plural = 'Vehículos de Usuario'
        unique_together = ['user', 'plate_number']

class RecurringReservation(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Diario'),
        ('WEEKLY', 'Semanal'),
        ('MONTHLY', 'Mensual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parking_space = models.ForeignKey('parking.ParkingSpace', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reserva Recurrente'
        verbose_name_plural = 'Reservas Recurrentes'

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Autenticación de Dos Factores'
        verbose_name_plural = 'Autenticaciones de Dos Factores'

    def generate_backup_codes(self):
        """Genera códigos de respaldo para el usuario"""
        import secrets
        codes = [secrets.token_hex(4) for _ in range(8)]
        self.backup_codes = codes
        self.save()
        return codes

    def verify_code(self, code):
        """Verifica el código de autenticación"""
        import pyotp
        if not self.secret_key:
            return False
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(code)

    def verify_backup_code(self, code):
        """Verifica un código de respaldo"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False
