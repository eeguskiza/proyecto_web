"""
Enriquece la BD con películas (SWAPI) y crea apariciones Character<->Media.

Qué hace:
1) Descarga films y people de SWAPI (mirror estable).
2) Crea/actualiza Media(title, episode, release_date, media_type='film').
3) Enlaza cada Character con sus films mediante la tabla intermedia Appearance.
4) Intenta completar Planet (climate/terrain/population) si hay coincidencia por nombre.

Suposiciones:
- Emparejamos Character por nombre exacto (misma grafía que SWAPI).
- Si un nombre no coincide, lo registramos en log y seguimos.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime
import requests

from core.models import Character, Media, Appearance, Planet

SWAPI = "https://swapi.py4e.com/api"

# ---------- CACHÉ GLOBAL ----------
_SWAPI_CACHE = {}

# ---------- Helpers ----------

def get_all(url):
    """Descarga paginando todos los resultados de SWAPI."""
    out, nxt = [], url
    while nxt:
        r = requests.get(nxt, timeout=30)
        r.raise_for_status()
        j = r.json()
        out += j.get("results", [])
        nxt = j.get("next")
    return out


def to_date(s):
    """Convierte '1977-05-25' a date; si no puede, None."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def get_name_from_url(url):
    """Dada una URL de SWAPI, devuelve su 'name' o 'title', con caché."""
    if not url:
        return None
    if url in _SWAPI_CACHE:
        return _SWAPI_CACHE[url]

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            name = data.get("name") or data.get("title")
            _SWAPI_CACHE[url] = name
            return name
    except Exception:
        pass

    return None


def resolve_names(url_list):
    """Convierte una lista de URLs SWAPI en una lista de nombres legibles."""
    if not url_list:
        return []
    names = []
    for u in url_list:
        name = get_name_from_url(u)
        if name:
            names.append(name)
    return names


# ---------- Comando principal ----------

class Command(BaseCommand):
    help = "Enriquece con films (Media) y apariciones (Appearance) desde SWAPI."

    @transaction.atomic
    def handle(self, *args, **opts):
        # 1) Descargar y crear/actualizar Films
        self.stdout.write("→ Descargando films desde SWAPI...")
        films = get_all(f"{SWAPI}/films/")
        created_m = updated_m = 0
        film_by_url = {}

        for f in films:
            title = f.get("title")
            episode = f.get("episode_id")
            rdate = to_date(f.get("release_date"))

            # Resolver nombres antes de guardar
            planets = resolve_names(f.get("planets"))
            characters = resolve_names(f.get("characters"))
            starships = resolve_names(f.get("starships"))
            vehicles = resolve_names(f.get("vehicles"))
            species = resolve_names(f.get("species"))

            media, new = Media.objects.update_or_create(
                title=title,
                defaults={
                    "media_type": Media.FILM,
                    "episode": episode,
                    "release_date": f.get("release_date"),
                    "director": f.get("director"),
                    "producer": f.get("producer"),
                    "opening_crawl": f.get("opening_crawl"),
                    "url": f.get("url"),
                    "characters": characters,
                    "planets": planets,
                    "starships": starships,
                    "vehicles": vehicles,
                    "species": species,
                },
            )

            film_by_url[f["url"]] = media
            created_m += 1 if new else 0
            updated_m += 0 if new else 1

        # 2) Enlazar personajes con películas
        self.stdout.write("→ Descargando personajes y enlazando con películas...")
        people = get_all(f"{SWAPI}/people/")
        linked = missing = 0

        for p in people:
            name = p.get("name")
            try:
                ch = Character.objects.get(name=name)
            except Character.DoesNotExist:
                missing += 1
                self.stdout.write(f"[WARN] Character no encontrado por nombre: {name}")
                self._maybe_enrich_planet(p)
                continue

            # Crear relaciones de aparición
            for furl in p.get("films", []):
                media = film_by_url.get(furl)
                if not media:
                    continue
                Appearance.objects.get_or_create(character=ch, media=media)
                linked += 1

            # Enriquecer planeta
            self._maybe_enrich_planet(p, ch)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Media films created {created_m}, updated {updated_m} | "
            f"Links Character-Film +{linked} | People sin match {missing}"
        ))


    # ---------- Helper interno ----------
    def _maybe_enrich_planet(self, person_obj, ch_instance=None):
        """
        Si SWAPI trae homeworld como URL, descarga el planeta y actualiza:
        - climate, terrain, population
        Aplica solo si ya existe Planet con ese nombre.
        """
        hw_url = person_obj.get("homeworld")
        if not hw_url or not isinstance(hw_url, str):
            return
        try:
            r = requests.get(hw_url, timeout=30)
            r.raise_for_status()
            pj = r.json()
            pname = pj.get("name")
            if not pname:
                return
            try:
                pl = Planet.objects.get(name=pname)
            except Planet.DoesNotExist:
                return

            changed = False
            if not pl.climate and pj.get("climate"):
                pl.climate = pj["climate"]; changed = True
            if not pl.terrain and pj.get("terrain"):
                pl.terrain = pj["terrain"]; changed = True
            if not pl.population and pj.get("population") and pj["population"].isdigit():
                pl.population = int(pj["population"]); changed = True
            if changed:
                pl.save()

            if ch_instance and ch_instance.homeworld is None:
                ch_instance.homeworld = pl
                ch_instance.save(update_fields=["homeworld"])
        except Exception:
            return
