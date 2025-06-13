from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(UserPassesTestMixin):
    required_role = None
    required_permissions = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        # Si el usuario es superusuario, tiene acceso total
        if self.request.user.is_superuser:
            return True

        # Verificar rol específico
        if self.required_role:
            try:
                user_role = self.request.user.userrole.role
                if not user_role or user_role.name != self.required_role:
                    return False
            except:
                return False

        # Verificar permisos específicos
        if self.required_permissions:
            return all(self.request.user.has_perm(perm) for perm in self.required_permissions)

        return True

    def handle_no_permission(self):
        raise PermissionDenied("No tienes permiso para acceder a esta página.") 