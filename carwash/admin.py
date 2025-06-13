from django.contrib import admin
from .models import CarWashService, Appointment

@admin.register(CarWashService)
class CarWashServiceAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'vehicle', 'status', 'price', 'created_at')
    list_filter = ('service_type', 'status')
    search_fields = ('vehicle__plate_number', 'service_type')
    date_hierarchy = 'created_at'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_time', 'created_at')
    search_fields = ('vehicle__plate_number', 'service__name')
