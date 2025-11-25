from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from core.models import Character
        from django.db.utils import OperationalError

        try:
            # Crear grupo Editor si no existe
            editor_group, created = Group.objects.get_or_create(name='Editor')

            # Obtener permisos del modelo Character
            content_type = ContentType.objects.get_for_model(Character)
            add_permission = Permission.objects.get(codename='add_character', content_type=content_type)
            change_permission = Permission.objects.get(codename='change_character', content_type=content_type)

            # Asignar permisos al grupo Editor
            editor_group.permissions.add(add_permission, change_permission)

        except OperationalError:
            # Evita errores si la base de datos aún no está lista (p.ej., antes de migraciones)
            pass
