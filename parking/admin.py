from django.contrib import admin
from .models import ParkingSpace, Reservation

@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('space_number', 'location', 'is_occupied', 'hourly_rate', 'daily_rate', 'created_at')
    list_filter = ('location', 'is_occupied', 'created_at')
    search_fields = ('space_number', 'location__name')
    fields = ('location', 'space_number', 'is_disabled_spot', 'hourly_rate', 'daily_rate')
    actions = ['liberar_espacios', 'terminar_y_facturar']

    def liberar_espacios(self, request, queryset):
        from django.utils import timezone
        count = 0
        for space in queryset:
            if space.is_occupied:
                # Buscar la reservación activa
                reservation = Reservation.objects.filter(
                    space=space,
                    status='ACTIVE'
                ).first()
                if reservation:
                    reservation.end_time = timezone.now()
                    reservation.status = 'COMPLETED'
                    reservation.save()
                space.is_occupied = False
                space.save()
                count += 1
        self.message_user(request, f"{count} espacio(s) liberado(s) correctamente.")
    liberar_espacios.short_description = "Liberar espacio(s) seleccionados"

    def terminar_y_facturar(self, request, queryset):
        from django.utils import timezone
        from invoicing.models import Invoice, InvoiceItem
        from django.contrib.auth import get_user_model
        User = get_user_model()
        count = 0
        duplicados = 0
        for space in queryset:
            if space.is_occupied:
                # Buscar todas las reservas activas
                reservas_activas = list(Reservation.objects.filter(
                    space=space,
                    status='ACTIVE'
                ).order_by('start_time'))
                if reservas_activas:
                    # La más reciente se completa y factura
                    reservation = reservas_activas[-1]
                    # Las demás se cancelan
                    for r in reservas_activas[:-1]:
                        r.status = 'CANCELLED'
                        r.end_time = timezone.now()
                        r.save()
                        duplicados += 1
                    # Terminar la reservación principal
                    reservation.end_time = timezone.now()
                    reservation.status = 'COMPLETED'
                    reservation.calculate_cost()
                    reservation.save()
                    space.is_occupied = False
                    space.save()
                    # Crear factura/ticket pendiente
                    user = reservation.user
                    last_invoice = Invoice.objects.order_by('-date_created').first()
                    if last_invoice:
                        try:
                            last_number = int(last_invoice.invoice_number.split('-')[1])
                        except Exception:
                            last_number = 0
                        new_number = f"INV-{str(last_number + 1).zfill(6)}"
                    else:
                        new_number = "INV-000001"
                    invoice = Invoice.objects.create(
                        user=user,
                        invoice_number=new_number,
                        date_created=timezone.now(),
                        due_date=timezone.now(),
                        total_amount=reservation.total_cost,
                        status='PENDING',
                        notes=f'Auto-factura por uso de espacio {space.space_number}',
                        payment_method='cash',
                    )
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=f"Estacionamiento - {space}",
                        quantity=1,
                        unit_price=reservation.total_cost,
                        total_price=reservation.total_cost,
                        reservation=reservation
                    )
                    invoice.calculate_total()
                    count += 1
        msg = f"{count} espacio(s) terminados y facturados correctamente."
        if duplicados:
            msg += f" {duplicados} reserva(s) duplicada(s) fueron canceladas automáticamente."
        self.message_user(request, msg)
    terminar_y_facturar.short_description = "Terminar uso y generar ticket/factura"

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'space', 'start_time', 'end_time', 'total_cost', 'status')
    list_filter = ('status', 'start_time', 'end_time')
    search_fields = ('vehicle__plate_number', 'space__space_number')
