from django.db.models import Count, Prefetch, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import cache_page # Importación para el caché
from django.utils.decorators import method_decorator # Necesario para cachear Clases (HomeView)

# Importaciones unificadas de tus modelos y formularios
from .models import Character, Media, Planet, Species, StarSystem
from .forms import PlanetInquiryForm, CharacterForm

@login_required
@permission_required('core.add_character', raise_exception=True)
def crear_personaje(request):
    # NOTA: NO cacheamos esta vista porque contiene un formulario POST y validación CSRF.
    if request.method == "POST":
        form = CharacterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index_personajes')
    else:
        form = CharacterForm()

    return render(request, "characters/crear.html", {"form": form})


# Cacheamos la HomeView usando method_decorator (porque es una Clase)
@method_decorator(cache_page(60 * 15), name='dispatch')
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
                    image_url__isnull=False
                )
                .exclude(image_url="")
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
   
@cache_page(60 * 15)
def media_view(request):
    films = Media.objects.filter(media_type=Media.FILM).order_by("episode")
    poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]

    for index, film in enumerate(films):
        film.release_year = film.release_date.year if film.release_date else None
        film.poster_static = poster_pool[index % len(poster_pool)]

    return render(request, "media/list.html", {"films": films})


@cache_page(60 * 15) # Añadido caché
def media_detail(request, media_id: int):
    character_qs = Character.objects.select_related("species").order_by("name")
    film = get_object_or_404(
        Media.objects.prefetch_related(Prefetch("cast", queryset=character_qs)),
        pk=media_id,
    )

    poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]
    film.poster_static = poster_pool[(film.id - 1) % len(poster_pool)]
    film.release_year = film.release_date.year if film.release_date else None

    cast = list(film.cast.all())

    return render(request, "media/detail.html", {"film": film, "cast": cast})


def handler_404(request, exception, template_name="errors/404.html"):
    return render(request, template_name, status=404)


def handler_500(request, template_name="errors/500.html"):
    return render(request, template_name, status=500)


@cache_page(60 * 15) # Añadido caché
def detalle_personaje(request, personaje_id):
    personaje = get_object_or_404(
        Character.objects.select_related("species", "homeworld").prefetch_related("films_and_series"),
        id=personaje_id,
    )
    films = personaje.films_and_series.filter(media_type=Media.FILM).order_by("episode", "release_date", "title")
    return render(request, "characters/detail.html", {"personaje": personaje, "films": films})


@cache_page(60 * 15) # Añadido caché (Django cachea automáticamente según los filtros de búsqueda URL)
def index_personajes(request):
    filters = {
        "q": request.GET.get("q", "").strip(),
        "species": request.GET.get("species", "").strip(),
        "media": request.GET.get("media", "").strip(),
    }

    personajes = Character.objects.select_related("species").prefetch_related("films_and_series").all()

    if filters["q"]:
        search = filters["q"]
        personajes = personajes.filter(
            Q(name__icontains=search)
            | Q(gender__icontains=search)
            | Q(species__name__icontains=search)
            | Q(eye_color__icontains=search)
        )

    if filters["species"].isdigit():
        personajes = personajes.filter(species_id=int(filters["species"]))

    if filters["media"].isdigit():
        personajes = personajes.filter(films_and_series__id=int(filters["media"]))

    personajes = personajes.distinct().order_by("name")

    species_options = (
        Species.objects.filter(character__isnull=False)
        .annotate(character_count=Count("character", distinct=True))
        .order_by("name")
    )
    media_options = Media.objects.filter(media_type=Media.FILM).order_by("episode", "release_date", "title")
    filters_active = any(filters.values())

    return render(
        request,
        "characters/list.html",
        {
            "personajes": personajes,
            "filters": filters,
            "filters_active": filters_active,
            "species_options": species_options,
            "media_options": media_options,
        },
    )


@cache_page(60 * 15) # Añadido caché
def species_list(request):
    species = (
        Species.objects.filter(character__isnull=False)
        .annotate(character_count=Count("character", distinct=True))
        .order_by("name")
    )
    return render(request, "species/list.html", {"species_list": species})


@cache_page(60 * 15) # Añadido caché
def species_detail(request, species_id):
    especie = get_object_or_404(Species, pk=species_id)
    characters = (
        Character.objects.select_related("homeworld")
        .filter(species=especie)
        .prefetch_related("films_and_series")
        .order_by("name")
    )
    return render(
        request,
        "species/detail.html",
        {
            "species": especie,
            "characters": characters,
        },
    )


def planets_view(request):
    # NOTA: NO cacheamos esta vista porque tiene un formulario de contacto (PlanetInquiryForm).
    inquiry_form = PlanetInquiryForm()
    form_success = False

    if request.method == "POST":
        inquiry_form = PlanetInquiryForm(request.POST)
        if inquiry_form.is_valid():
            inquiry_form.save()
            form_success = True
            inquiry_form = PlanetInquiryForm()

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
        fields = {
            "climate": str(p.climate or "").strip().lower(),
            "terrain": str(p.terrain or "").strip().lower(),
            "population": str(p.population or "").strip().lower(),
            "capital_city": str(p.capital_city or "").strip().lower(),
            "grid_coordinates": str(p.grid_coordinates or "").strip().lower(),
        }

        valid_count = sum(1 for v in fields.values() if v not in bad_values)

        p.display_climate = p.climate if fields["climate"] not in bad_values else imperial_phrase("climate")
        p.display_terrain = p.terrain if fields["terrain"] not in bad_values else imperial_phrase("terrain")
        p.display_population = p.population if fields["population"] not in bad_values else imperial_phrase("population")
        p.display_capital = p.capital_city if fields["capital_city"] not in bad_values else imperial_phrase("capital_city")
        p.display_grid = p.grid_coordinates if fields["grid_coordinates"] not in bad_values else imperial_phrase("grid_coordinates")
        p.display_system = getattr(p.star_system, "name", imperial_phrase("star_system"))

        p.valid_fields = valid_count

        clean_planets.append(p)

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
            "inquiry_form": inquiry_form,
            "form_success": form_success,
        },
    )