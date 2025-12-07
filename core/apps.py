from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Registramos un hook post_migrate para crear el grupo Editor sin tocar la BD en import.
        from django.db.models.signals import post_migrate
        from django.apps import apps

        def create_editor_group(sender, **kwargs):
            from django.contrib.auth.models import Group, Permission
            from django.contrib.contenttypes.models import ContentType
            from django.db.utils import OperationalError

            try:
                Character = apps.get_model("core", "Character")
                editor_group, _ = Group.objects.get_or_create(name="Editor")
                content_type = ContentType.objects.get_for_model(Character)
                add_perm = Permission.objects.get(
                    codename="add_character", content_type=content_type
                )
                change_perm = Permission.objects.get(
                    codename="change_character", content_type=content_type
                )
                editor_group.permissions.add(add_perm, change_perm)
            except OperationalError:
                # BD no lista (p. ej. antes de migrar); se volverá a ejecutar tras migraciones.
                pass

        post_migrate.connect(create_editor_group, sender=self)
