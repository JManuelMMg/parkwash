from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, UserRole, Role, UserNotification, UserPreference, UserVehicle, RecurringReservation, TwoFactorAuth
from .forms import CustomUserCreationForm, UserPreferenceForm, UserVehicleForm
import json
import pyotp
import qrcode
import base64
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        # Autenticar al usuario
        user = form.get_user()
        login(self.request, user)

        # Verificar el rol del usuario
        try:
            user_role = user.userrole.role
            if user_role:
                if user_role.name == 'admin':
                    messages.success(self.request, 'Bienvenido al panel de administración.')
                    return redirect('admin:index')
                elif user_role.name == 'manager':
                    messages.success(self.request, 'Bienvenido al panel de gestión.')
                    return redirect('parking:list')
                elif user_role.name == 'staff':
                    messages.success(self.request, 'Bienvenido al panel de operaciones.')
                    return redirect('parking:list')
                else:  # client
                    messages.success(self.request, 'Bienvenido al sistema de estacionamiento.')
                    return redirect('parking:list')
        except:
            # Si no tiene rol asignado, asignar rol de cliente
            client_role = Role.objects.get(name='client')
            UserRole.objects.create(user=user, role=client_role)
            messages.success(self.request, 'Bienvenido al sistema de estacionamiento.')
            return redirect('parking:list')

        return super().form_valid(form)

class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        messages.success(self.request, 'Cuenta creada exitosamente. Por favor inicia sesión.')
        return super().form_valid(form)

class UserProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'users/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['user_role'] = self.request.user.userrole.role
        except:
            context['user_role'] = None
        return context

class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'users/edit_profile.html'
    fields = ['phone_number', 'address', 'car_brand', 'car_model', 'license_plate', 'car_photo']
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user.userprofile

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado exitosamente.')
        return super().form_valid(form)

class NotificationListView(LoginRequiredMixin, ListView):
    model = UserNotification
    template_name = 'users/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get('notification_id')
        try:
            notification = UserNotification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except UserNotification.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)

class UserPreferenceView(LoginRequiredMixin, UpdateView):
    model = UserPreference
    form_class = UserPreferenceForm
    template_name = 'users/preferences.html'
    success_url = reverse_lazy('users:preferences')

    def get_object(self):
        obj, created = UserPreference.objects.get_or_create(user=self.request.user)
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Preferencias actualizadas exitosamente.')
        return super().form_valid(form)

class UserVehicleListView(LoginRequiredMixin, ListView):
    model = UserVehicle
    template_name = 'users/vehicles.html'
    context_object_name = 'vehicles'

    def get_queryset(self):
        return UserVehicle.objects.filter(user=self.request.user)

class UserVehicleCreateView(LoginRequiredMixin, CreateView):
    model = UserVehicle
    form_class = UserVehicleForm
    template_name = 'users/vehicle_form.html'
    success_url = reverse_lazy('users:vehicles')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Vehículo agregado exitosamente.')
        return super().form_valid(form)

class UserVehicleUpdateView(LoginRequiredMixin, UpdateView):
    model = UserVehicle
    form_class = UserVehicleForm
    template_name = 'users/vehicle_form.html'
    success_url = reverse_lazy('users:vehicles')

    def get_queryset(self):
        return UserVehicle.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Vehículo actualizado exitosamente.')
        return super().form_valid(form)

class UserVehicleDeleteView(LoginRequiredMixin, DeleteView):
    model = UserVehicle
    template_name = 'users/vehicle_confirm_delete.html'
    success_url = reverse_lazy('users:vehicles')

    def get_queryset(self):
        return UserVehicle.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vehículo eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

class RecurringReservationListView(LoginRequiredMixin, ListView):
    model = RecurringReservation
    template_name = 'users/recurring_reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return RecurringReservation.objects.filter(user=self.request.user)

def send_notification(user, notification_type, title, message):
    """Función auxiliar para enviar notificaciones"""
    notification = UserNotification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message
    )
    
    # Enviar email si está configurado
    if settings.EMAIL_HOST_USER:
        try:
            send_mail(
                title,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")

    return notification

class TwoFactorSetupView(LoginRequiredMixin, View):
    template_name = 'users/2fa_setup.html'

    def get(self, request):
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        if not two_factor.secret_key:
            # Generar nueva clave secreta
            secret_key = pyotp.random_base32()
            two_factor.secret_key = secret_key
            two_factor.save()

        # Generar código QR
        totp = pyotp.TOTP(two_factor.secret_key)
        provisioning_uri = totp.provisioning_uri(
            request.user.email,
            issuer_name="Parking System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir imagen a base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # Generar códigos de respaldo
        backup_codes = two_factor.generate_backup_codes()

        context = {
            'qr_code': qr_code,
            'secret_key': two_factor.secret_key,
            'backup_codes': backup_codes,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        code = request.POST.get('code')
        
        if two_factor.verify_code(code):
            two_factor.is_enabled = True
            two_factor.save()
            messages.success(request, 'Autenticación de dos factores activada exitosamente.')
            return redirect('admin:index')
        else:
            messages.error(request, 'Código inválido. Por favor, intenta nuevamente.')
            return redirect('users:2fa_setup')

class TwoFactorVerifyView(LoginRequiredMixin, View):
    template_name = 'users/2fa_verify.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            code = request.POST.get('code')
            
            if two_factor.verify_code(code):
                request.session['2fa_verified'] = True
                messages.success(request, 'Autenticación de dos factores verificada exitosamente.')
                return redirect('users:profile')
            else:
                messages.error(request, 'Código de verificación inválido.')
                return render(request, self.template_name)
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, 'La autenticación de dos factores no está configurada.')
            return redirect('users:2fa_setup')

class TwoFactorDisableView(LoginRequiredMixin, View):
    template_name = 'users/2fa_disable.html'

    def get(self, request):
        try:
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            if not two_factor.is_enabled:
                messages.info(request, 'La autenticación de dos factores no está activada.')
                return redirect('users:profile')
            return render(request, self.template_name)
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, 'La autenticación de dos factores no está configurada.')
            return redirect('users:2fa_setup')

    def post(self, request):
        try:
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            code = request.POST.get('code')
            
            if two_factor.verify_code(code):
                two_factor.is_enabled = False
                two_factor.save()
                request.session.pop('2fa_verified', None)
                messages.success(request, 'Autenticación de dos factores desactivada exitosamente.')
                return redirect('users:profile')
            else:
                messages.error(request, 'Código de verificación inválido.')
                return render(request, self.template_name)
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, 'La autenticación de dos factores no está configurada.')
            return redirect('users:2fa_setup')
