"""
Comando unificado para poblar y enriquecer la base de datos de Star Wars.

Incluye tres etapas consecutivas:
1) Carga el dataset local de akabab (Species, Planet, Affiliation, Character).
2) Importa información ampliada de planetas desde `data/sw_planets.csv`.
3) Descarga films y personajes desde SWAPI para crear Media, Appearance y
   completar datos faltantes de planetas/homeworlds.

Cada etapa puede ejecutarse de forma independiente con flags opcionales.
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import (
    Affiliation,
    Appearance,
    Character,
    CharacterAffiliation,
    Media,
    Planet,
    PlanetSpecies,
    Region,
    Sector,
    Species,
    StarSystem,
)

SWAPI_ROOT = "https://swapi.py4e.com/api"
UNKNOWN_TOKENS = {"unknown", "various", "n/a", "none", "—", "-", "", "0"}
SPECIES_SPLIT_RE = re.compile(r"[;/,&]| and | y ", flags=re.IGNORECASE)


class Command(BaseCommand):
    help = (
        "Carga datos locales y remotos para poblar por completo la base Star Wars. "
        "Combina el dataset de akabab, el catálogo CSV de planetas y la "
        "información de SWAPI en un único comando."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-akabab",
            action="store_true",
            help="Omitir la carga del dataset local data/all.json.",
        )
        parser.add_argument(
            "--skip-planets",
            action="store_true",
            help="Omitir la importación del catálogo data/sw_planets.csv.",
        )
        parser.add_argument(
            "--skip-swapi",
            action="store_true",
            help="Omitir la descarga y el enriquecimiento desde SWAPI.",
    )

    def handle(self, *args, **options):
        self._swapi_cache = {}
        self._planet_data_cache = {}
        self._payload_cache = {}
        load_swapi_enabled = os.getenv("LOAD_SWAPI_ENABLED", "true").lower() == "true"

        if not options.get("skip_akabab"):
            self.stdout.write("1) Cargando dataset local de akabab...")
            stats = self._load_akabab_dataset(Path("data/all.json"))
            self.stdout.write(
                self.style.SUCCESS(
                    "   ✔ Species +{species_created}, Planets +{planets_created}, "
                    "Affiliations +{affiliations_created} | Characters creados {characters_created}, "
                    "actualizados {characters_updated} | Vínculos C-A +{affiliations_linked}".format(
                        **stats
                    )
                )
            )
        else:
            self.stdout.write("1) Dataset akabab omitido (flag --skip-akabab).")

        if not options.get("skip_planets"):
            self.stdout.write("2) Importando catálogo extendido de planetas...")
            stats = self._load_planets_catalog(Path("data/sw_planets.csv"))
            self.stdout.write(
                self.style.SUCCESS(
                    "   ✔ Regions +{regions_created}, Sectors +{sectors_created}, Systems +{systems_created} | "
                    "Planets creados {planets_created}, actualizados {planets_updated} | "
                    "Vínculos planeta-especie +{planet_species_links}".format(**stats)
                )
            )
        else:
            self.stdout.write("2) Catálogo de planetas omitido (flag --skip-planets).")

        if not options.get("skip_swapi") and load_swapi_enabled:
            self.stdout.write("3) Enriqueciendo con films y personajes de SWAPI...")
            try:
                stats = self._enrich_from_swapi()
                self.stdout.write(
                    self.style.SUCCESS(
                        "   ✔ Media films creados {media_created}, actualizados {media_updated} | "
                        "Apariciones añadidas +{appearance_links} | "
                        "Especies creadas {species_created}, actualizadas {species_updated}, homeworlds enlazados +{species_homeworld_links} | "
                        "Personajes con especie asignada +{characters_species_linked} | "
                        "Personas sin match {missing_people} | "
                        "Planetas enriquecidos +{planets_enriched}, homeworlds asignados +{homeworld_links}".format(
                            **stats
                        )
                    )
                )
            except CommandError as exc:
                self.stdout.write(
                    self.style.WARNING(
                        f"3) Enriquecimiento SWAPI omitido por error: {exc}"
                    )
                )
        else:
            self.stdout.write(
                "3) Enriquecimiento SWAPI omitido (flag --skip-swapi o LOAD_SWAPI_ENABLED=false)."
            )

    # ------------------------------------------------------------------
    # Etapa 1: dataset akabab
    # ------------------------------------------------------------------
    @transaction.atomic
    def _load_akabab_dataset(self, json_path: Path) -> dict:
        if not json_path.exists():
            raise CommandError(
                "No existe {}. Coloca el JSON antes de ejecutar.".format(json_path)
            )

        data = json.loads(json_path.read_text(encoding="utf-8"))

        stats = dict(
            species_created=0,
            planets_created=0,
            affiliations_created=0,
            characters_created=0,
            characters_updated=0,
            affiliations_linked=0,
        )

        for item in data:
            species_name = self._norm_str(item.get("species"))
            planet_name = self._norm_str(item.get("homeworld"))

            species_obj = None
            if species_name:
                species_obj, created = Species.objects.get_or_create(name=species_name)
                if created:
                    stats["species_created"] += 1

            planet_obj = None
            if planet_name:
                planet_obj, created = Planet.objects.get_or_create(name=planet_name)
                if created:
                    stats["planets_created"] += 1

            defaults = dict(
                species=species_obj,
                homeworld=planet_obj,
                height_m=self._to_float(item.get("height")),
                mass_kg=self._to_float(item.get("mass")),
                gender=self._norm_str(item.get("gender")),
                eye_color=self._norm_str(item.get("eyeColor")),
                hair_color=self._norm_str(item.get("hairColor")),
                skin_color=self._norm_str(item.get("skinColor")),
                cybernetics=self._norm_str(item.get("cybernetics")),
                image_url=self._norm_str(item.get("image")),
                wiki_url=self._norm_str(item.get("wiki")),
            )

            character, created = Character.objects.update_or_create(
                name=self._norm_str(item.get("name")),
                defaults=defaults,
            )
            if created:
                stats["characters_created"] += 1
            else:
                stats["characters_updated"] += 1

            for affiliation_raw in item.get("affiliations") or []:
                affiliation_name = self._norm_str(affiliation_raw)
                if not affiliation_name:
                    continue
                affiliation, created = Affiliation.objects.get_or_create(
                    name=affiliation_name
                )
                if created:
                    stats["affiliations_created"] += 1

                _, link_created = CharacterAffiliation.objects.get_or_create(
                    character=character,
                    affiliation=affiliation,
                )
                if link_created:
                    stats["affiliations_linked"] += 1

        return stats

    # ------------------------------------------------------------------
    # Etapa 2: catálogo extendido de planetas
    # ------------------------------------------------------------------
    @transaction.atomic
    def _load_planets_catalog(self, csv_path: Path) -> dict:
        if not csv_path.exists():
            raise CommandError(
                "No existe {}. Coloca el CSV antes de ejecutar.".format(csv_path)
            )

        stats = dict(
            regions_created=0,
            sectors_created=0,
            systems_created=0,
            planets_created=0,
            planets_updated=0,
            planet_species_links=0,
        )

        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                name = self._none_if_unknown(row.get("Name"))
                if not name:
                    continue

                region_obj = None
                region_name = self._none_if_unknown(row.get("Region"))
                if region_name:
                    region_obj, created = Region.objects.get_or_create(name=region_name)
                    if created:
                        stats["regions_created"] += 1

                sector_obj = None
                sector_name = self._none_if_unknown(row.get("Sector"))
                if sector_name:
                    sector_obj, created = Sector.objects.get_or_create(
                        name=sector_name,
                        defaults={"region": region_obj},
                    )
                    if not created and region_obj and sector_obj.region is None:
                        sector_obj.region = region_obj
                        sector_obj.save(update_fields=["region"])
                    if created:
                        stats["sectors_created"] += 1

                system_obj = None
                system_name = self._none_if_unknown(row.get("System"))
                if system_name:
                    system_obj, created = StarSystem.objects.get_or_create(
                        name=system_name,
                        defaults={"sector": sector_obj},
                    )
                    if not created and sector_obj and system_obj.sector is None:
                        system_obj.sector = sector_obj
                        system_obj.save(update_fields=["sector"])
                    if created:
                        stats["systems_created"] += 1

                defaults = dict(
                    star_system=system_obj,
                    capital_city=self._none_if_unknown(row.get("Capital City")),
                    grid_coordinates=self._none_if_unknown(row.get("Grid Coordinates")),
                )
                planet, created = Planet.objects.update_or_create(
                    name=name,
                    defaults=defaults,
                )
                if created:
                    stats["planets_created"] += 1
                else:
                    stats["planets_updated"] += 1

                for species_name in self._parse_species_list(row.get("Inhabitants")):
                    species, _ = Species.objects.get_or_create(name=species_name)
                    _, link_created = PlanetSpecies.objects.get_or_create(
                        planet=planet,
                        species=species,
                    )
                    if link_created:
                        stats["planet_species_links"] += 1

        return stats

    # ------------------------------------------------------------------
    # Etapa 3: enriquecimiento desde SWAPI
    # ------------------------------------------------------------------
    def _enrich_from_swapi(self) -> dict:
        stats = dict(
            media_created=0,
            media_updated=0,
            appearance_links=0,
            missing_people=0,
            planets_enriched=0,
            homeworld_links=0,
            species_created=0,
            species_updated=0,
            species_homeworld_links=0,
            characters_species_linked=0,
        )

        species_data = self._get_all(f"{SWAPI_ROOT}/species/")
        species_by_url = {}

        for item in species_data:
            name = self._norm_str(item.get("name"))
            if not name:
                continue

            defaults = {
                "classification": self._none_if_unknown(item.get("classification")),
                "designation": self._none_if_unknown(item.get("designation")),
                "language": self._none_if_unknown(item.get("language")),
            }

            species_obj = self._get_or_update_species(name, defaults, stats)
            species_by_url[item.get("url")] = species_obj

            planet = self._get_planet_by_url(item.get("homeworld"))
            if planet:
                _, link_created = PlanetSpecies.objects.get_or_create(
                    planet=planet, species=species_obj
                )
                if link_created:
                    stats["species_homeworld_links"] += 1

        films = self._get_all(f"{SWAPI_ROOT}/films/")
        film_by_url = {}

        for film in films:
            film_defaults = {
                "media_type": Media.FILM,
                "episode": film.get("episode_id"),
                "release_date": self._to_date(film.get("release_date")),
                "director": film.get("director"),
                "producer": film.get("producer"),
                "opening_crawl": film.get("opening_crawl"),
                "url": film.get("url"),
                "characters": self._resolve_names(film.get("characters")),
                "planets": self._resolve_names(film.get("planets")),
                "starships": self._resolve_names(film.get("starships")),
                "vehicles": self._resolve_names(film.get("vehicles")),
                "species": self._resolve_names(film.get("species")),
            }

            media_obj, created = Media.objects.update_or_create(
                title=film.get("title"),
                defaults=film_defaults,
            )
            film_by_url[film.get("url")] = media_obj
            if created:
                stats["media_created"] += 1
            else:
                stats["media_updated"] += 1

        people = self._get_all(f"{SWAPI_ROOT}/people/")

        for person in people:
            name = person.get("name")
            try:
                character = Character.objects.get(name=name)
            except Character.DoesNotExist:
                stats["missing_people"] += 1
                self.stdout.write(
                    self.style.WARNING(f"   • Character no encontrado por nombre: {name}")
                )
                stats = self._maybe_enrich_planet(person, character=None, stats=stats)
                continue

            for film_url in person.get("films", []):
                media_obj = film_by_url.get(film_url)
                if not media_obj:
                    continue
                _, link_created = Appearance.objects.get_or_create(
                    character=character,
                    media=media_obj,
                )
                if link_created:
                    stats["appearance_links"] += 1

            stats = self._maybe_enrich_planet(person, character=character, stats=stats)
            if character and not character.species:
                for species_url in person.get("species") or []:
                    species_obj = species_by_url.get(species_url)
                    if species_obj:
                        character.species = species_obj
                        character.save(update_fields=["species"])
                        stats["characters_species_linked"] += 1
                        break

        return stats

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _maybe_enrich_planet(self, person_obj, character, stats):
        hw_url = person_obj.get("homeworld")
        if not hw_url or not isinstance(hw_url, str):
            return stats

        planet_data = self._get_planet_data(hw_url)
        planet_name = planet_data.get("name")
        if not planet_name:
            return stats

        try:
            planet = Planet.objects.get(name=planet_name)
        except Planet.DoesNotExist:
            return stats

        changed = False
        numeric_population = planet_data.get("population")
        if not planet.climate and planet_data.get("climate"):
            planet.climate = planet_data["climate"]
            changed = True
        if not planet.terrain and planet_data.get("terrain"):
            planet.terrain = planet_data["terrain"]
            changed = True
        if (
            not planet.population
            and numeric_population
            and str(numeric_population).isdigit()
        ):
            planet.population = int(numeric_population)
            changed = True

        if changed:
            planet.save()
            stats["planets_enriched"] += 1

        if character and character.homeworld is None:
            character.homeworld = planet
            character.save(update_fields=["homeworld"])
            stats["homeworld_links"] += 1

        return stats

    def _get_all(self, url):
        try:
            out = []
            next_url = url
            while next_url:
                response = requests.get(next_url, timeout=30)
                response.raise_for_status()
                payload = response.json()
                out.extend(payload.get("results", []))
                next_url = payload.get("next")
            return out
        except requests.RequestException as exc:
            raise CommandError(f"Error solicitando {url}: {exc}") from exc

    def _resolve_names(self, url_list):
        if not url_list:
            return []
        names = []
        for url in url_list:
            name = self._swapi_cache.get(url)
            if name is not None:
                if name:
                    names.append(name)
                continue

            data = self._get_swapi_payload(url)
            if data:
                name = data.get("name") or data.get("title")
                self._swapi_cache[url] = name
                if name:
                    names.append(name)
                continue

            self._swapi_cache[url] = None
        return names

    def _get_planet_by_url(self, planet_url):
        if not planet_url:
            return None
        planet_data = self._get_planet_data(planet_url)
        planet_name = planet_data.get("name")
        if not planet_name:
            return None
        try:
            return Planet.objects.get(name=planet_name)
        except Planet.DoesNotExist:
            return None

    def _get_planet_data(self, planet_url):
        if not planet_url:
            return {}
        if planet_url in self._planet_data_cache:
            return self._planet_data_cache[planet_url]

        payload = self._get_swapi_payload(planet_url, timeout=30) or {}
        self._planet_data_cache[planet_url] = payload
        return payload

    def _get_swapi_payload(self, url, timeout=10):
        if not url:
            return None
        if url in self._payload_cache:
            return self._payload_cache[url]
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            self._payload_cache[url] = data
            return data
        except requests.RequestException:
            self._payload_cache[url] = None
            return None

    def _get_or_update_species(self, name, defaults, stats):
        qs = Species.objects.filter(name__iexact=name)
        species_obj = qs.first()

        if species_obj:
            duplicates = list(qs[1:])
            if duplicates:
                for dup in duplicates:
                    Character.objects.filter(species=dup).update(species=species_obj)
                    for link in PlanetSpecies.objects.filter(species=dup):
                        PlanetSpecies.objects.get_or_create(
                            planet=link.planet, species=species_obj
                        )
                    PlanetSpecies.objects.filter(species=dup).delete()
                    dup.delete()

            updated_fields = []
            for field, value in defaults.items():
                if value and getattr(species_obj, field) != value:
                    setattr(species_obj, field, value)
                    updated_fields.append(field)

            if species_obj.name != name:
                species_obj.name = name
                updated_fields.append("name")

            if updated_fields:
                species_obj.save(update_fields=updated_fields)
                stats["species_updated"] += 1
            return species_obj

        species_obj = Species.objects.create(name=name, **defaults)
        stats["species_created"] += 1
        return species_obj

    @staticmethod
    def _norm_str(value):
        if value is None:
            return None
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return None

    @staticmethod
    def _to_float(value):
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _none_if_unknown(value):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.lower() in UNKNOWN_TOKENS:
            return None
        return text

    def _parse_species_list(self, raw):
        text = self._none_if_unknown(raw)
        if not text:
            return []
        items = [segment.strip(" '") for segment in SPECIES_SPLIT_RE.split(text)]
        cleaned = []
        for item in items:
            if not item or item.lower() in UNKNOWN_TOKENS:
                continue
            if item.endswith("s") and not item.endswith("'s"):
                item = item[:-1]
            if "'" in item:
                parts = [p[:1].upper() + p[1:] if p else p for p in item.split("'")]
                item = "'".join(parts)
            else:
                item = item[:1].upper() + item[1:]
            cleaned.append(item)
        return cleaned

    @staticmethod
    def _to_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None
