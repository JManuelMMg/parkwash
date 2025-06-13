from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import CarWashService, Appointment, Vehicle

# Create your views here.

class ServiceListView(ListView):
    model = CarWashService
    template_name = 'carwash/service_list.html'
    context_object_name = 'services'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ServiceDetailView(DetailView):
    model = CarWashService
    template_name = 'carwash/service_detail.html'
    context_object_name = 'service'

class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    template_name = 'carwash/appointment_create.html'
    fields = ['vehicle', 'service', 'appointment_time']
    success_url = reverse_lazy('carwash:appointments')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Cita agendada exitosamente.')
        return super().form_valid(form)

class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'carwash/appointment_list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'carwash/appointment_detail.html'
    context_object_name = 'appointment'

class AppointmentCancelView(LoginRequiredMixin, UpdateView):
    model = Appointment
    template_name = 'carwash/appointment_cancel.html'
    fields = []
    success_url = reverse_lazy('carwash:appointments')

    def form_valid(self, form):
        appointment = self.get_object()
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(self.request, 'Cita cancelada exitosamente.')
        return super().form_valid(form)

@require_http_methods(["POST"])
def register_service(request):
    try:
        # Obtener datos del formulario
        plate_number = request.POST.get('plate_number')
        model = request.POST.get('model')
        color = request.POST.get('color')
        vehicle_type = request.POST.get('vehicle_type')
        selected_service = request.POST.get('selected_service')

        # Crear o actualizar el vehículo
        vehicle, created = Vehicle.objects.update_or_create(
            plate_number=plate_number,
            defaults={
                'model': model,
                'color': color,
                'vehicle_type': vehicle_type
            }
        )

        # Crear el servicio
        service = CarWashService.objects.create(
            vehicle=vehicle,
            service_type=selected_service,
            status='PENDING'
        )

        messages.success(request, 'Servicio registrado exitosamente')
        return redirect('carwash:services')

    except Exception as e:
        messages.error(request, f'Error al registrar el servicio: {str(e)}')
        return redirect('carwash:services')
