from django.contrib.auth.models import User
from django.utils import timezone
from .models import Role, UserRole, AuditLog, TwoFactorAuth
import logging
from django.contrib import messages
from django.urls import reverse
from django.urls import reverse_lazy
from django.urls import reverse
from django.urls import reverse_lazy
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class RoleAssignmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Verificar si el usuario ya tiene un rol asignado
                UserRole.objects.get(user=request.user)
            except UserRole.DoesNotExist:
                # Si no tiene rol, asignar el rol de cliente por defecto
                logger.info(f"Asignando rol de cliente por defecto a {request.user.username}")
                client_role = Role.objects.get(name='client')
                UserRole.objects.create(user=request.user, role=client_role)
                messages.info(request, 'Se te ha asignado el rol de cliente por defecto.')

        response = self.get_response(request)
        return response

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Registrar acciones administrativas
            if request.path.startswith('/admin/'):
                action = self._determine_action(request)
                if action:
                    AuditLog.objects.create(
                        user=request.user,
                        action=action,
                        model_name=request.path.split('/')[2] if len(request.path.split('/')) > 2 else '',
                        object_id=request.path.split('/')[3] if len(request.path.split('/')) > 3 else '',
                        details={
                            'method': request.method,
                            'path': request.path,
                            'data': request.POST.dict() if request.method == 'POST' else {}
                        },
                        ip_address=self._get_client_ip(request)
                    )

        return response

    def _determine_action(self, request):
        if request.method == 'POST':
            if 'add' in request.path:
                return 'CREATE'
            elif 'change' in request.path:
                return 'UPDATE'
            elif 'delete' in request.path:
                return 'DELETE'
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class TwoFactorAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de URLs que requieren 2FA
        protected_urls = [
            '/admin/',
            '/users/profile/',
            '/users/vehicles/',
            '/users/preferences/',
        ]

        # Verificar si la URL actual requiere 2FA
        if any(request.path.startswith(url) for url in protected_urls):
            # Si el usuario está autenticado
            if request.user.is_authenticated:
                try:
                    two_factor = TwoFactorAuth.objects.get(user=request.user)
                    if two_factor.is_enabled:
                        # Si 2FA está habilitado pero no verificado en esta sesión
                        if not request.session.get('2fa_verified'):
                            # Permitir acceso a las páginas de 2FA
                            if not any(request.path.startswith(url) for url in ['/users/2fa/verify/', '/users/2fa/setup/', '/users/2fa/disable/']):
                                messages.warning(request, 'Por favor, verifica tu autenticación de dos factores.')
                                return redirect('users:2fa_verify')
                except TwoFactorAuth.DoesNotExist:
                    pass

        response = self.get_response(request)
        return response 