from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView
from .models import Character, Media, Planet, Species, StarSystem

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
    poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]

    for index, film in enumerate(films):
        film.release_year = film.release_date.year if film.release_date else None
        film.poster_static = poster_pool[index % len(poster_pool)]

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
    filters = {
        "q": request.GET.get("q", "").strip(),
        "climate": request.GET.get("climate", "").strip(),
        "terrain": request.GET.get("terrain", "").strip(),
        "system": request.GET.get("system", "").strip(),
    }

    planets_qs = Planet.objects.select_related("star_system").all().order_by("name")

    if filters["q"]:
        planets_qs = planets_qs.filter(name__icontains=filters["q"])

    if filters["climate"]:
        planets_qs = planets_qs.filter(climate__icontains=filters["climate"])

    if filters["terrain"]:
        planets_qs = planets_qs.filter(terrain__icontains=filters["terrain"])

    if filters["system"].isdigit():
        planets_qs = planets_qs.filter(star_system_id=int(filters["system"]))

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
    for p in planets_qs:
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

    climate_options = (
        Planet.objects.exclude(climate__isnull=True)
        .exclude(climate__exact="")
        .order_by("climate")
        .values_list("climate", flat=True)
        .distinct()
    )

    terrain_options = (
        Planet.objects.exclude(terrain__isnull=True)
        .exclude(terrain__exact="")
        .order_by("terrain")
        .values_list("terrain", flat=True)
        .distinct()
    )

    system_options = StarSystem.objects.order_by("name")

    filters_active = any(filters.values())

    return render(
        request,
        "planets/list.html",
        {
            "planets": clean_planets,
            "filters": filters,
            "filters_active": filters_active,
            "climate_options": climate_options,
            "terrain_options": terrain_options,
            "system_options": system_options,
        },
    )
