from django.db import models

class DatabaseRouter:
    """
    Router para manejar operaciones de base de datos en múltiples bases de datos.
    """
    def db_for_read(self, model, **hints):
        """
        Sugiere la base de datos para operaciones de lectura.
        """
        if model._meta.app_label == 'sessions':
            return 'default'
        # Permitir lectura desde ambas bases de datos
        return None

    def db_for_write(self, model, **hints):
        """
        Sugiere la base de datos para operaciones de escritura.
        """
        if model._meta.app_label == 'sessions':
            return 'default'
        # Permitir escritura en ambas bases de datos
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permite relaciones entre objetos.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determina si las migraciones deben ejecutarse en una base de datos específica.
        """
        if app_label == 'sessions':
            return db == 'default'
        # Permitir migraciones en ambas bases de datos
        return True 