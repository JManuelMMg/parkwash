from django.db import transaction
from django.db.models import Model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.db.utils import DatabaseError
from django.db import connections
from django.conf import settings
import threading
from django.db.models.signals import pre_save
from django.db.models import Q

class DatabaseSyncMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._sync_lock = threading.Lock()
        self._syncing = set()  # Conjunto para rastrear objetos en sincronización
        self._last_sync = {}  # Diccionario para rastrear la última sincronización
        
        # Registrar los manejadores de señales para todos los modelos excepto sesiones
        for model in apps.get_models():
            if not model._meta.abstract and model._meta.app_label != 'sessions':
                post_save.connect(self.handle_save, sender=model)
                post_delete.connect(self.handle_delete, sender=model)
                pre_save.connect(self.handle_pre_save, sender=model)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def _get_model_fields(self, instance):
        """Obtiene los campos del modelo excluyendo el ID"""
        return {
            field.name: getattr(instance, field.name)
            for field in instance._meta.fields
            if field.name != 'id'
        }

    def _get_sync_key(self, instance):
        """Genera una clave única para el objeto"""
        return f"{instance._meta.model_name}_{instance.pk}"

    def _sync_instance(self, instance, source_db, target_db, created=False):
        """Sincroniza una instancia entre bases de datos"""
        sync_key = self._get_sync_key(instance)
        
        if sync_key in self._syncing:
            return

        try:
            with self._sync_lock:
                self._syncing.add(sync_key)
                
                # Obtener el modelo en la base de datos destino
                target_model = apps.get_model(instance._meta.app_label, instance._meta.model_name)
                
                with transaction.atomic(using=target_db):
                    if created:
                        # Verificar si el objeto ya existe en la base de datos destino
                        if not target_model.objects.using(target_db).filter(pk=instance.pk).exists():
                            # Crear el objeto en la base de datos destino
                            target_model.objects.using(target_db).create(
                                id=instance.pk,
                                **self._get_model_fields(instance)
                            )
                    else:
                        # Actualizar el objeto en la base de datos destino
                        target_model.objects.using(target_db).filter(pk=instance.pk).update(
                            **self._get_model_fields(instance)
                        )
                
                # Actualizar el timestamp de última sincronización
                self._last_sync[sync_key] = instance.pk
                
        except DatabaseError as e:
            print(f"Error de base de datos al sincronizar con {target_db}: {str(e)}")
        except Exception as e:
            print(f"Error al sincronizar con {target_db}: {str(e)}")
        finally:
            self._syncing.discard(sync_key)

    def handle_pre_save(self, sender, instance, **kwargs):
        """Maneja la sincronización antes de guardar un objeto"""
        if not isinstance(instance, Model) or sender._meta.app_label == 'sessions':
            return

        # Determinar la base de datos origen
        if instance._state.db == 'default':
            target_db = 'sqlite'
        else:
            target_db = 'default'

        # Sincronizar en un hilo separado
        sync_thread = threading.Thread(
            target=self._sync_instance,
            args=(instance, instance._state.db, target_db, not instance.pk)
        )
        sync_thread.start()

    def handle_save(self, sender, instance, created, **kwargs):
        """Maneja la sincronización después de guardar un objeto"""
        if not isinstance(instance, Model) or sender._meta.app_label == 'sessions':
            return

        # La sincronización principal ya se realizó en pre_save
        pass

    def handle_delete(self, sender, instance, **kwargs):
        """Maneja la sincronización cuando se elimina un objeto"""
        if not isinstance(instance, Model) or sender._meta.app_label == 'sessions':
            return

        sync_key = self._get_sync_key(instance)
        
        if sync_key in self._syncing:
            return

        try:
            with self._sync_lock:
                self._syncing.add(sync_key)
                
                # Determinar la base de datos destino
                if instance._state.db == 'default':
                    target_db = 'sqlite'
                else:
                    target_db = 'default'

                with transaction.atomic(using=target_db):
                    # Obtener el modelo en la base de datos destino
                    target_model = apps.get_model(instance._meta.app_label, instance._meta.model_name)
                    # Eliminar el objeto en la base de datos destino
                    target_model.objects.using(target_db).filter(pk=instance.pk).delete()
                
                # Limpiar el registro de sincronización
                if sync_key in self._last_sync:
                    del self._last_sync[sync_key]
                
        except DatabaseError as e:
            print(f"Error de base de datos al sincronizar eliminación con {target_db}: {str(e)}")
        except Exception as e:
            print(f"Error al sincronizar eliminación con {target_db}: {str(e)}")
        finally:
            self._syncing.discard(sync_key)

    def __del__(self):
        """Limpieza al destruir el middleware"""
        # Cerrar todas las conexiones de base de datos
        for conn in connections.all():
            conn.close() 