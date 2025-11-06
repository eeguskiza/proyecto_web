from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from .models import Character, Media, Planet, Species

class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = []

        for s in Species.objects.all():
            tallest = (
                Character.objects
                .filter(
                    species=s,
                    image_url__isnull=False  # que tenga campo de imagen
                )
                .exclude(image_url="")      # que no esté vacío
                .order_by("-height_m")
                .first()
            )
            if tallest:
                featured.append(tallest)

        context["featured_characters"] = featured
        context["stats"] = {
            "personajes": Character.objects.count(),
            "especies": Species.objects.count(),
            "peliculas": Media.objects.filter(media_type=Media.FILM).count(),
        }
        return context
    
def media_view(request):
    films = Media.objects.filter(media_type=Media.FILM).order_by("episode")
    return render(request, "media/list.html", {"films": films})


def handler_404(request, exception, template_name="errors/404.html"):
    return render(request, template_name, status=404)

def handler_500(request, template_name="errors/500.html"):
    return render(request, template_name, status=500)

def detalle_personaje(request, personaje_id):
    personaje = get_object_or_404(Character, id=personaje_id)
    return render(request, "characters/detail.html", {"personaje": personaje})

def index_personajes(request):
    especie_id = request.GET.get("especie")
    personajes = Character.objects.select_related("species").all()
    if especie_id:
        personajes = personajes.filter(species_id=especie_id)
    especies = Species.objects.all()
    return render(request, "characters/list.html", {
        "personajes": personajes,
        "especies": especies,
    })


def planets_view(request):
    planets = Planet.objects.select_related("star_system").all().order_by("name")

    bad_values = {"unknown", "desconocido", "none", "n/a", "null", "0", ""}
    
    def imperial_phrase(field):
        phrases = {
            "climate": "Condición atmosférica clasificada.",
            "terrain": "Superficie bajo censura imperial.",
            "population": "Cifras eliminadas del registro.",
            "capital_city": "Localidad no reconocida por el Imperio.",
            "grid_coordinates": "Sistema fuera del alcance imperial.",
            "star_system": "Sector no autorizado.",
        }
        return phrases.get(field, "Archivo incompleto.")

    clean_planets = []
    for p in planets:
        # Campos normalizados
        fields = {
            "climate": str(p.climate or "").strip().lower(),
            "terrain": str(p.terrain or "").strip().lower(),
            "population": str(p.population or "").strip().lower(),
            "capital_city": str(p.capital_city or "").strip().lower(),
            "grid_coordinates": str(p.grid_coordinates or "").strip().lower(),
        }

        # Contamos campos válidos
        valid_count = sum(1 for v in fields.values() if v not in bad_values)

        # Creamos versiones “display” con frases imperiales
        p.display_climate = p.climate if fields["climate"] not in bad_values else imperial_phrase("climate")
        p.display_terrain = p.terrain if fields["terrain"] not in bad_values else imperial_phrase("terrain")
        p.display_population = p.population if fields["population"] not in bad_values else imperial_phrase("population")
        p.display_capital = p.capital_city if fields["capital_city"] not in bad_values else imperial_phrase("capital_city")
        p.display_grid = p.grid_coordinates if fields["grid_coordinates"] not in bad_values else imperial_phrase("grid_coordinates")
        p.display_system = getattr(p.star_system, "name", imperial_phrase("star_system"))

        # Guardamos número de campos válidos (para ordenar después)
        p.valid_fields = valid_count

        clean_planets.append(p)

    # 🔹 Ordenar de más completos a menos
    clean_planets.sort(key=lambda x: x.valid_fields, reverse=True)

    return render(request, "planets/list.html", {"planets": clean_planets})
