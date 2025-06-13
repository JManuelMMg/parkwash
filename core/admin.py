from django.contrib import admin
from .models import Vehicle, Location

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'vehicle_type', 'owner', 'created_at')
    list_filter = ('vehicle_type', 'created_at')
    search_fields = ('plate_number', 'owner__username')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity', 'created_at')
    search_fields = ('name', 'address')
