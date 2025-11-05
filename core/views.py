from django.views.generic import TemplateView
from .models import Species, Character, Media
from .utils import resolve_swapi_names
from django.shortcuts import render, get_object_or_404
import requests
from django.shortcuts import render
from core.models import Media

# Caché en memoria (evita repetir peticiones a la misma URL)
SWAPI_CACHE = {}

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
        return context
    
def resolve_swapi_name(url):
    """Convierte una URL de SWAPI en un nombre legible (usa caché local)."""
    if not url:
        return None
    if url in SWAPI_CACHE:
        return SWAPI_CACHE[url]
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        name = data.get("name") or data.get("title")
        SWAPI_CACHE[url] = name
        return name
    except Exception:
        # En caso de error, devuelve el ID como fallback
        return url.split("/")[-2]

def media_view(request):
    films = Media.objects.filter(media_type=Media.FILM).order_by("episode")
    enriched_films = []

    for film in films:
        enriched_films.append({
            "title": film.title,
            "episode": film.episode,
            "director": film.director,
            "producer": film.producer,
            "release_date": film.release_date,
            "opening_crawl": film.opening_crawl,
            "url": film.url,
            # Convertimos las listas de URLs en listas de nombres
            "planets": [resolve_swapi_name(u) for u in (film.planets or [])],
            "characters": [resolve_swapi_name(u) for u in (film.characters or [])],
            "starships": [resolve_swapi_name(u) for u in (film.starships or [])],
            "vehicles": [resolve_swapi_name(u) for u in (film.vehicles or [])],
            "species": [resolve_swapi_name(u) for u in (film.species or [])],
        })

    return render(request, "media.html", {"films": enriched_films})


def handler_404(request, exception, template_name="404.html"):
    return render(request, template_name, status=404)

def handler_500(request, template_name="500.html"):
    return render(request, template_name, status=500)

def detalle_personaje(request, personaje_id):
    personaje = get_object_or_404(Character, id=personaje_id)
    return render(request, 'detalle_personajes.html', {'personaje': personaje})

def index_personajes(request):
    especie_id = request.GET.get("especie")
    personajes = Character.objects.select_related("species").all()
    if especie_id:
        personajes = personajes.filter(species_id=especie_id)
    especies = Species.objects.all()
    return render(request, "index_personajes.html", {
        "personajes": personajes,
        "especies": especies,
    })