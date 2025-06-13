from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from users.mixins import RoleRequiredMixin
from .models import ParkingSpace, Reservation
from core.models import Vehicle
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.

class ParkingSpaceListView(ListView):
    model = ParkingSpace
    template_name = 'parking/space_list.html'
    context_object_name = 'spaces'

    def get_queryset(self):
        # Obtener todos los espacios
        spaces = ParkingSpace.objects.all()
        
        # Verificar y actualizar el estado de ocupación para cada espacio
        for space in spaces:
            # Verificar si hay una reservación activa para este espacio
            has_active_reservation = Reservation.objects.filter(
                space=space,
                status__in=['ACTIVE', 'PENDING'],  # Incluir también reservas pendientes
                end_time__gt=timezone.now()
            ).exists()
            
            # Si el estado actual no coincide con la existencia de una reservación activa
            if space.is_occupied != has_active_reservation:
                space.is_occupied = has_active_reservation
                space.save(update_fields=['is_occupied', 'updated_at'])
                
                # Si el espacio está ocupado, asegurarse de que tenga una reservación activa
                if has_active_reservation:
                    try:
                        active_reservation = Reservation.objects.get(
                            space=space,
                            status__in=['ACTIVE', 'PENDING'],
                            end_time__gt=timezone.now()
                        )
                        # Si la reservación está pendiente, actualizarla a activa
                        if active_reservation.status == 'PENDING':
                            active_reservation.status = 'ACTIVE'
                            active_reservation.save(update_fields=['status', 'updated_at'])
                    except Reservation.DoesNotExist:
                        # Si no hay reservación activa pero el espacio está marcado como ocupado,
                        # liberar el espacio
                        space.is_occupied = False
                        space.save(update_fields=['is_occupied', 'updated_at'])
        
        return spaces

class ParkingSpaceDetailView(DetailView):
    model = ParkingSpace
    template_name = 'parking/space_detail.html'
    context_object_name = 'space'

class ParkingSpaceCreateView(RoleRequiredMixin, CreateView):
    model = ParkingSpace
    template_name = 'parking/space_form.html'
    fields = ['location', 'space_number', 'is_disabled_spot']
    success_url = reverse_lazy('parking:list')
    required_role = 'admin'
    required_permissions = ['parking.add_parkingspace']

    def form_valid(self, form):
        # Asegurarse de que el nuevo espacio se cree como no ocupado
        form.instance.is_occupied = False
        messages.success(self.request, 'Espacio de estacionamiento creado exitosamente.')
        return super().form_valid(form)

class ParkingSpaceUpdateView(RoleRequiredMixin, UpdateView):
    model = ParkingSpace
    template_name = 'parking/space_form.html'
    fields = ['location', 'space_number', 'is_disabled_spot']
    success_url = reverse_lazy('parking:list')
    required_role = 'admin'
    required_permissions = ['parking.change_parkingspace']

    def form_valid(self, form):
        messages.success(self.request, 'Espacio de estacionamiento actualizado exitosamente.')
        return super().form_valid(form)

class ParkingSpaceDeleteView(RoleRequiredMixin, DeleteView):
    model = ParkingSpace
    template_name = 'parking/space_confirm_delete.html'
    success_url = reverse_lazy('parking:list')
    required_role = 'admin'
    required_permissions = ['parking.delete_parkingspace']

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Espacio de estacionamiento eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

class SpaceOccupyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        space = get_object_or_404(ParkingSpace, pk=pk)
        
        if space.is_occupied:
            messages.error(request, 'Este espacio ya está ocupado.')
            return redirect('parking:list')

        # Validar datos requeridos
        plate_number = request.POST.get('plate_number')
        vehicle_type = request.POST.get('vehicle_type')

        if not plate_number or not vehicle_type:
            messages.error(request, 'Por favor complete todos los campos requeridos.')
            return redirect('parking:list')

        try:
            # Intentar encontrar un vehículo existente
            vehicle = Vehicle.objects.get(plate_number=plate_number)
            
            # Si el vehículo existe pero pertenece a otro usuario
            if vehicle.owner != request.user:
                messages.error(request, 'Este número de placa ya está registrado por otro usuario.')
                return redirect('parking:list')
                
            # Actualizar el tipo de vehículo si cambió
            if vehicle.vehicle_type != vehicle_type:
                vehicle.vehicle_type = vehicle_type
                vehicle.save()
        
        except Vehicle.DoesNotExist:
            # Crear nuevo vehículo
            try:
                vehicle = Vehicle.objects.create(
                    plate_number=plate_number,
                    vehicle_type=vehicle_type,
                    owner=request.user
                )
            except Exception as e:
                messages.error(request, f'Error al registrar el vehículo: {str(e)}')
                return redirect('parking:list')

        try:
            # Crear la reservación
            reservation = Reservation.objects.create(
                space=space,
                vehicle=vehicle,
                user=request.user,
                start_time=timezone.now(),
                end_time=timezone.now() + timezone.timedelta(hours=1),
                total_cost=space.hourly_rate,
                status='ACTIVE'
            )
            
            # Marcar el espacio como ocupado y guardar
            space.is_occupied = True
            space.save(update_fields=['is_occupied', 'updated_at'])
            
            messages.success(request, f'Espacio {space.space_number} ocupado exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al crear la reservación: {str(e)}')
            # Si el vehículo fue creado pero la reservación falló, eliminar el vehículo
            if vehicle.pk and not Vehicle.objects.filter(plate_number=plate_number).exclude(pk=vehicle.pk).exists():
                vehicle.delete()
            
        return redirect('parking:list')

class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    template_name = 'parking/reservation_form.html'
    fields = ['parking_space', 'start_time', 'end_time']
    success_url = reverse_lazy('parking:my_reservations')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Reserva creada exitosamente.')
        return super().form_valid(form)

class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = 'parking/reservation_detail.html'
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

class ReservationCancelView(LoginRequiredMixin, UpdateView):
    model = Reservation
    template_name = 'parking/reservation_cancel.html'
    fields = []
    success_url = reverse_lazy('parking:my_reservations')

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user, status='ACTIVE')

    def form_valid(self, form):
        form.instance.status = 'CANCELLED'
        messages.success(self.request, 'Reserva cancelada exitosamente.')
        return super().form_valid(form)

class UserReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'parking/reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import ParkingSpace
        context['spaces'] = ParkingSpace.objects.filter(is_occupied=False)
        return context

class ReservationUpdateView(RoleRequiredMixin, UpdateView):
    model = Reservation
    template_name = 'parking/reservation_form.html'
    fields = ['parking_space', 'start_time', 'end_time', 'status']
    success_url = reverse_lazy('parking:list')
    required_role = 'staff'
    required_permissions = ['parking.change_reservation']

    def form_valid(self, form):
        messages.success(self.request, 'Reserva actualizada exitosamente.')
        return super().form_valid(form)

class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'parking/reservation_confirm_delete.html'
    success_url = reverse_lazy('parking:my_reservations')

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reserva eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class SpaceExitView(View):
    def post(self, request, pk):
        space = get_object_or_404(ParkingSpace, pk=pk)
        
        try:
            # Buscar la reservación activa para este espacio
            reservation = Reservation.objects.get(
                space=space,
                status='ACTIVE'
            )
            
            # Actualizar la reservación
            reservation.end_time = timezone.now()
            reservation.status = 'COMPLETED'
            reservation.save()
            
            # Liberar el espacio
            space.is_occupied = False
            space.save()
            
            return JsonResponse({'status': 'success'})
            
        except Reservation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No se encontró una reservación activa'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def create_reservation(request):
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        servicio = request.POST.get('servicio')
        placa = request.POST.get('placa')
        modelo = request.POST.get('modelo')
        color = request.POST.get('color')
        tipo_vehiculo = request.POST.get('tipo_vehiculo')
        espacio_id = request.POST.get('espacio')

        # Validar tipo_vehiculo para evitar errores con .upper()
        tipo_vehiculo_val = tipo_vehiculo.upper() if tipo_vehiculo else "DESCONOCIDO"

        if servicio == 'estacionamiento':
            if not espacio_id:
                messages.error(request, 'Debes seleccionar un espacio.')
                return redirect('parking:my_reservations')
            try:
                space = ParkingSpace.objects.get(pk=espacio_id, is_occupied=False)
            except ParkingSpace.DoesNotExist:
                messages.error(request, 'El espacio seleccionado ya no está disponible.')
                return redirect('parking:my_reservations')
        else:
            space = None

        # Buscar o crear vehículo
        vehicle, created = Vehicle.objects.get_or_create(
            plate_number=placa,
            defaults={
                'vehicle_type': tipo_vehiculo_val,
                'owner': request.user
            }
        )
        if not created:
            vehicle.vehicle_type = tipo_vehiculo_val
            vehicle.owner = request.user
            vehicle.save()

        # Calcular inicio y fin (1 hora por defecto)
        import datetime
        start_time = datetime.datetime.strptime(f'{fecha} {hora}', '%Y-%m-%d %H:%M')
        end_time = start_time + datetime.timedelta(hours=1)
        total_cost = space.hourly_rate if space else 0

        # Crear reserva
        reserva = Reservation.objects.create(
            user=request.user,
            vehicle=vehicle,
            space=space,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            status='ACTIVE'
        )
        # Enviar correo de confirmación
        subject = f"Confirmación de Reserva - Park & Wash"
        if servicio == 'estacionamiento':
            message = f"Hola {request.user.get_full_name() or request.user.username},\n\nTu reserva de estacionamiento ha sido registrada.\n\nDetalles:\n- Espacio: {space.space_number if space else 'N/A'}\n- Ubicación: {space.location.name if space else 'N/A'}\n- Fecha: {fecha}\n- Hora: {hora}\n- Vehículo: {placa} ({modelo}, {color})\n- Costo: ${total_cost}\n\nGracias por usar Park & Wash."
        else:
            message = f"Hola {request.user.get_full_name() or request.user.username},\n\nTu reserva de autolavado ha sido registrada.\n\nDetalles:\n- Fecha: {fecha}\n- Hora: {hora}\n- Vehículo: {placa} ({modelo}, {color})\n- Servicio: Autolavado\n\nGracias por usar Park & Wash."
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )
        messages.success(request, 'Reserva creada exitosamente. Se ha enviado un correo de confirmación.')
        return redirect('parking:my_reservations')
    return redirect('parking:my_reservations')

@login_required
def delete_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    reservation.space.is_occupied = False
    reservation.space.save()
    reservation.delete()
    messages.success(request, 'Reserva eliminada.')
    return redirect('parking:my_reservations')

@login_required
def delete_all_reservations(request):
    reservations = Reservation.objects.filter(user=request.user)
    for reservation in reservations:
        reservation.space.is_occupied = False
        reservation.space.save()
        reservation.delete()
    messages.success(request, 'Todas las reservas han sido eliminadas.')
    return redirect('parking:my_reservations')

def parking_spaces_status(request):
    spaces = ParkingSpace.objects.all()
    data = [
        {
            'id': space.id,
            'is_occupied': space.is_occupied,
        }
        for space in spaces
    ]
    return JsonResponse({'spaces': data})

@login_required
def space_cost(request, space_id):
    space = get_object_or_404(ParkingSpace, id=space_id)
    
    try:
        reservation = Reservation.objects.filter(
            space=space,
            status='ACTIVE'
        ).order_by('start_time').last()
        if not reservation:
            raise Reservation.DoesNotExist()
        # Calcular tiempo transcurrido
        elapsed = timezone.now() - reservation.start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        elapsed_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        # Calcular costo actual usando Decimal
        duration_hours = Decimal(str(elapsed.total_seconds() / 3600))
        if duration_hours < 6:
            current_cost = duration_hours * space.hourly_rate
        else:
            days = int(duration_hours // 24)
            remaining_hours = duration_hours % 24
            if remaining_hours >= 6:
                days += 1
                remaining_hours = 0
            current_cost = (Decimal(days) * space.daily_rate) + (Decimal(str(remaining_hours)) * space.hourly_rate)
        return JsonResponse({
            'space_number': space.space_number,
            'start_time': reservation.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_time': elapsed_time,
            'current_cost': f"{current_cost:.2f}"
        })
    except Reservation.DoesNotExist:
        return JsonResponse({
            'error': 'No hay una reservación activa para este espacio'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
