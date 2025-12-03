from django.contrib import admin
from .models import (
    Species,
    Planet,
    Media,
    Affiliation,
    Character,
    Appearance,
    CharacterAffiliation,
    Region,
    Sector,
    PlanetSpecies,
    StarSystem,
)

admin.site.register(Species)
admin.site.register(Planet)
admin.site.register(Media)
admin.site.register(Affiliation)
admin.site.register(Appearance)
admin.site.register(CharacterAffiliation)
admin.site.register(Region)
admin.site.register(Sector)
admin.site.register(PlanetSpecies)
admin.site.register(StarSystem)


class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "homeworld", "display_affiliations")
    list_filter = ("species", "homeworld")
    search_fields = ("name", "species__name", "homeworld__name")
    
    # Campos calculados o relaciones ManyToMany
    def display_affiliations(self, obj):
        return ", ".join([a.name for a in obj.affiliations.all()])
    display_affiliations.short_description = "Affiliations"
    
    # Control de permisos: ocultar columnas para usuarios no superuser
    def get_list_display(self, request):
        columns = list(self.list_display)
        if not request.user.is_superuser:
            # quitar columna que solo admins pueden ver
            columns.remove("display_affiliations")
        return columns

# Registrar el admin
admin.site.register(Character, CharacterAdmin)
