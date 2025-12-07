import os
import json
import requests

from django.db.models import Count, Prefetch, Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse

from .models import Affiliation, Character, Media, Planet, Species, StarSystem
from .forms import PlanetInquiryForm, CharacterForm


@login_required
@permission_required('core.add_character', raise_exception=True)
def crear_personaje(request):
    """Formulario simple para dar de alta personajes desde la web."""
    if request.method == "POST":
        form = CharacterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index_personajes')
    else:
        form = CharacterForm()

    return render(request, "characters/crear.html", {"form": form})


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        """Monta el escaparate de la home con el personaje más alto de cada especie."""
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


class ChatPageView(TemplateView):
    """Página dedicada al chatbot a pantalla completa."""
    template_name = "chat.html"


class MediaListView(ListView):
    """Listado de pelis/series con carteles alternando imágenes locales."""
    model = Media
    template_name = "media/list.html"
    context_object_name = "films"

    def get_queryset(self):
        qs = Media.objects.filter(media_type=Media.FILM).order_by("episode")
        poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]
        films = list(qs)
        for index, film in enumerate(films):
            film.release_year = film.release_date.year if film.release_date else None
            film.poster_static = poster_pool[index % len(poster_pool)]
        return films


class MediaDetailView(DetailView):
    """Detalle de una película con su reparto precargado."""
    model = Media
    pk_url_kwarg = "media_id"
    template_name = "media/detail.html"
    context_object_name = "film"

    def get_queryset(self):
        character_qs = Character.objects.select_related("species").order_by("name")
        return Media.objects.prefetch_related(Prefetch("cast", queryset=character_qs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        film = context["film"]
        poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]
        film.poster_static = poster_pool[(film.id - 1) % len(poster_pool)]
        film.release_year = film.release_date.year if film.release_date else None
        context["cast"] = list(film.cast.all())
        return context


def handler_404(request, exception, template_name="errors/404.html"):
    return render(request, template_name, status=404)


def handler_500(request, template_name="errors/500.html"):
    return render(request, template_name, status=500)


class CharacterDetailView(DetailView):
    """Ficha de un personaje con enlaces a su especie, planeta y filmografía."""
    model = Character
    pk_url_kwarg = "personaje_id"
    template_name = "characters/detail.html"
    context_object_name = "personaje"

    def get_queryset(self):
        return Character.objects.select_related("species", "homeworld").prefetch_related("films_and_series", "affiliations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        personaje = context["personaje"]
        context["films"] = personaje.films_and_series.filter(media_type=Media.FILM).order_by("episode", "release_date", "title")
        return context


class CharacterListView(ListView):
    """Buscador con filtros de texto, especie y película (sin caché: depende de permisos)."""
    model = Character
    template_name = "characters/list.html"
    context_object_name = "personajes"

    def get_filters(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "species": self.request.GET.get("species", "").strip(),
            "media": self.request.GET.get("media", "").strip(),
        }

    def get_queryset(self):
        filters = self.get_filters()
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

        return personajes.distinct().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        context["filters"] = filters
        context["filters_active"] = any(filters.values())
        context["species_options"] = (
            Species.objects.filter(character__isnull=False)
            .annotate(character_count=Count("character", distinct=True))
            .order_by("name")
        )
        context["media_options"] = Media.objects.filter(media_type=Media.FILM).order_by("episode", "release_date", "title")
        return context


class SpeciesListView(ListView):
    """Especies ordenadas que tengan al menos un personaje asociado."""
    model = Species
    template_name = "species/list.html"
    context_object_name = "species_list"

    def get_queryset(self):
        return (
            Species.objects.filter(character__isnull=False)
            .annotate(character_count=Count("character", distinct=True))
            .order_by("name")
        )


class SpeciesDetailView(DetailView):
    """Detalle de especie y sus personajes residentes."""
    model = Species
    pk_url_kwarg = "species_id"
    template_name = "species/detail.html"
    context_object_name = "species"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        especie = context["species"]
        context["characters"] = (
            Character.objects.select_related("homeworld")
            .filter(species=especie)
            .prefetch_related("films_and_series")
            .order_by("name")
        )
        return context


class PlanetsView(TemplateView):
    """Listado de planetas y formulario de contacto. Sin caché para no romper el POST."""
    template_name = "planets/list.html"
    form_success = False

    def get_filters(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "climate": self.request.GET.get("climate", "").strip(),
            "terrain": self.request.GET.get("terrain", "").strip(),
            "system": self.request.GET.get("system", "").strip(),
        }

    def get_planets(self):
        filters = self.get_filters()
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
            # Mensajes temáticos para campos con datos pobres de SWAPI.
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
        return clean_planets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        context["filters"] = filters
        context["filters_active"] = any(filters.values())
        context["planets"] = self.get_planets()
        context["climate_options"] = (
            Planet.objects.exclude(climate__isnull=True)
            .exclude(climate__exact="")
            .order_by("climate")
            .values_list("climate", flat=True)
            .distinct()
        )
        context["terrain_options"] = (
            Planet.objects.exclude(terrain__isnull=True)
            .exclude(terrain__exact="")
            .order_by("terrain")
            .values_list("terrain", flat=True)
            .distinct()
        )
        context["system_options"] = StarSystem.objects.order_by("name")
        context["inquiry_form"] = kwargs.get("inquiry_form", PlanetInquiryForm())
        context["form_success"] = getattr(self, "form_success", False)
        return context

    def post(self, request, *args, **kwargs):
        form = PlanetInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            self.form_success = True
            return self.render_to_response(self.get_context_data(inquiry_form=PlanetInquiryForm()))
        return self.render_to_response(self.get_context_data(inquiry_form=form))


class PlanetDetailView(DetailView):
    """Ficha de planeta con fauna y residentes humanos/alienígenas."""
    model = Planet
    pk_url_kwarg = "planet_id"
    template_name = "planets/detail.html"
    context_object_name = "planet"

    def get_queryset(self):
        return Planet.objects.select_related("star_system")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        planet = context["planet"]
        context["native_species"] = (
            planet.native_species.all()
            .annotate(character_count=Count("character", distinct=True))
            .order_by("name")
        )
        context["residents"] = (
            Character.objects.filter(homeworld=planet)
            .select_related("species")
            .order_by("name")
        )
        return context


class AffiliationDetailView(DetailView):
    """Listado de miembros de una afiliación concreta."""
    model = Affiliation
    pk_url_kwarg = "affiliation_id"
    template_name = "affiliations/detail.html"
    context_object_name = "affiliation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        affiliation = context["affiliation"]
        context["members"] = (
            Character.objects.filter(affiliations=affiliation)
            .select_related("species", "homeworld")
            .distinct()
            .order_by("name")
        )
        return context


class ChatBotSearchView(ListView):
    """Endpoint simple para buscar personajes desde el chatbot."""
    http_method_names = ["get"]
    model = Character

    def render_to_response(self, context, **response_kwargs):
        query = self.request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"error": "Falta la consulta"}, status=400)

        personaje = self._find_character(query)
        if personaje:
            payload = self._character_payload(personaje, body=f"Te muestro info de {personaje.name}:")
            return JsonResponse(payload, status=200)

        media_obj = self._find_media(query)
        if media_obj:
            payload = self._media_payload(media_obj, body=f"Te muestro info de {media_obj.title}:")
            return JsonResponse(payload, status=200)

        gpt_data = self._gpt_reply(query)
        if gpt_data:
            name = gpt_data.get("name") or ""
            body = gpt_data.get("body")

            match = self._find_character(name)
            if match:
                payload = self._character_payload(match, body=body)
                return JsonResponse(payload, status=200)

            media_match = self._find_media(name)
            if media_match:
                payload = self._media_payload(media_match, body=body)
                return JsonResponse(payload, status=200)

            if body:
                match = self._find_character(body)
                if match:
                    payload = self._character_payload(match, body=body)
                    return JsonResponse(payload, status=200)
                media_match = self._find_media(body)
                if media_match:
                    payload = self._media_payload(media_match, body=body)
                    return JsonResponse(payload, status=200)

            if body:
                return JsonResponse({"reply": body}, status=200)

        return JsonResponse(
            {"reply": "Solo puedo ayudarte con personajes o películas de Star Wars. Prueba con un nombre o especie."},
            status=200,
        )

    def _find_character(self, text: str):
        return (
            Character.objects.select_related("species", "homeworld")
            .prefetch_related("films_and_series")
            .filter(
                Q(name__icontains=text)
                | Q(species__name__icontains=text)
                | Q(homeworld__name__icontains=text)
            )
            .order_by("name")
            .first()
        )

    def _character_payload(self, personaje, body=None):
        films = (
            personaje.films_and_series.filter(media_type=Media.FILM)
            .order_by("episode", "release_date")
            .values_list("title", flat=True)
        )
        return {
            "kind": "character",
            "name": personaje.name,
            "body": body or f"Aquí tienes información sobre {personaje.name}.",
            "species": getattr(personaje.species, "name", "Desconocida"),
            "homeworld": getattr(personaje.homeworld, "name", "Desconocido"),
            "cybernetics": personaje.cybernetics or "",
            "film": films[0] if films else "Sin película registrada",
            "image": personaje.image_url or "",
            "detail_url": reverse("detalle_personaje", args=[personaje.id]),
        }

    def _find_media(self, text: str):
        return (
            Media.objects.filter(media_type=Media.FILM, title__icontains=text)
            .order_by("episode", "release_date", "title")
            .first()
        )

    def _media_payload(self, media_obj, body=None):
        poster_pool = [f"img/{i}.jpg" for i in range(1, 8)]
        poster = poster_pool[(media_obj.id - 1) % len(poster_pool)]
        return {
            "kind": "media",
            "name": media_obj.title,
            "body": body or f"Aquí tienes información sobre {media_obj.title}.",
            "release_year": media_obj.release_date.year if media_obj.release_date else None,
            "episode": media_obj.episode,
            "poster": poster,
            "detail_url": reverse("media_detail", args=[media_obj.id]),
        }

    def _gpt_reply(self, query: str) -> dict | None:
        """Llama a la API de OpenAI si hay clave y devuelve JSON {name, body}."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Responde solo sobre personajes o películas de Star Wars. "
                        "Devuelve siempre un JSON con los campos 'name' y 'body'. "
                        "En 'name' pon el nombre del personaje o título de la película si se entiende de la pregunta; "
                        "si no es de Star Wars, deja name vacío y body indicando que solo respondes sobre Star Wars."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
            "max_tokens": 120,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            res = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=10,
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, str):
                return json.loads(content)
            return content
        except Exception:
            return None
