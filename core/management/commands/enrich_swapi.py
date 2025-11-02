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

def get_all(url):
    """Descarga paginando results de SWAPI."""
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

class Command(BaseCommand):
    help = "Enriquece con films (Media) y apariciones (Appearance) desde SWAPI."

    @transaction.atomic
    def handle(self, *args, **opts):
        # 1) Films
        films = get_all(f"{SWAPI}/films/")
        created_m = updated_m = 0
        film_by_url = {}

        for f in films:
            title = f.get("title")
            episode = f.get("episode_id")
            rdate = to_date(f.get("release_date"))

            media, new = Media.objects.update_or_create(
                title=title,
                defaults={
                    "media_type": Media.FILM,
                    "episode": episode,
                    "release_date": rdate,
                    "canonical": True,
                },
            )
            film_by_url[f["url"]] = media
            created_m += 1 if new else 0
            updated_m += 0 if new else 1

        # 2) People -> Character + Appearance
        people = get_all(f"{SWAPI}/people/")
        linked = missing = 0
        for p in people:
            name = p.get("name")
            # Character por nombre exacto
            try:
                ch = Character.objects.get(name=name)
            except Character.DoesNotExist:
                missing += 1
                self.stdout.write(f"[WARN] Character no encontrado por nombre: {name}")
                # Completar planeta si coincide, aunque no tengamos personaje
                self._maybe_enrich_planet(p)
                continue

            # Apariciones
            for furl in p.get("films", []):
                media = film_by_url.get(furl)
                if not media:
                    continue
                Appearance.objects.get_or_create(character=ch, media=media)
                linked += 1

            # Enriquecer planeta del personaje si hay match por nombre
            self._maybe_enrich_planet(p, ch)

        self.stdout.write(self.style.SUCCESS(
            f"Media films created {created_m}, updated {updated_m} | Links Character-Film +{linked} | People sin match {missing}"
        ))

    # -------- helpers --------

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
            r = requests.get(hw_url, timeout=30); r.raise_for_status()
            pj = r.json()
            pname = pj.get("name")
            if not pname:
                return
            try:
                pl = Planet.objects.get(name=pname)
            except Planet.DoesNotExist:
                # si no existe, no lo creamos aquí; mantenemos el flujo simple
                return
            # actualizar metadatos si están vacíos
            changed = False
            if not pl.climate and pj.get("climate"):
                pl.climate = pj["climate"]; changed = True
            if not pl.terrain and pj.get("terrain"):
                pl.terrain = pj["terrain"]; changed = True
            if not pl.population and pj.get("population") and pj["population"].isdigit():
                pl.population = int(pj["population"]); changed = True
            if changed:
                pl.save()
            # asociar FK al personaje si vino por SWAPI y no estaba
            if ch_instance and ch_instance.homeworld is None:
                ch_instance.homeworld = pl
                ch_instance.save(update_fields=["homeworld"])
        except Exception:
            # silenciar errores remotos de SWAPI en esta fase
            return
