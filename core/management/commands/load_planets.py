from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path
import csv
import re

from core.models import (
    Species, Planet, Region, Sector, StarSystem, PlanetSpecies
)

# ---------- Helpers ----------

UNKNOWN_TOKENS = {"unknown", "various", "n/a", "none", "—", "-", ""}

def norm_str(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    return s

def none_if_unknown(v):
    s = norm_str(v)
    if not s:
        return None
    if s.lower() in UNKNOWN_TOKENS:
        return None
    return s

_SPLIT_RE = re.compile(r"[;/,&]| and | y ", flags=re.IGNORECASE)

def parse_species_list(raw):
    s = none_if_unknown(raw)
    if not s:
        return []
    # divide por separadores comunes
    items = [x.strip(" '\"") for x in _SPLIT_RE.split(s)]
    items = [i for i in items if i and i.lower() not in UNKNOWN_TOKENS]
    # limpia plurales simples tipo Twi'leks -> Twi'lek (heurística ligera)
    cleaned = []
    for it in items:
        if it.endswith("s") and not it.endswith("'s"):
            cleaned.append(it[:-1])
        else:
            cleaned.append(it)
    # capitaliza “bonito” sin destrozar apóstrofes
    pretty = []
    for it in cleaned:
        if "'" in it:
            parts = it.split("'")
            parts = [p[:1].upper() + p[1:] if p else p for p in parts]
            pretty.append("'".join(parts))
        else:
            pretty.append(it[:1].upper() + it[1:])
    return pretty

# ---------- Command ----------

class Command(BaseCommand):
    help = "Carga planetas desde data/sw_planets.csv (no descarga nada)."

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path("data/sw_planets.csv")
        if not path.exists():
            raise FileNotFoundError("No existe data/sw_planets.csv. Coloca el CSV en esa ruta.")

        created_r = created_sct = created_sys = 0
        created_p = updated_p = linked_ps = 0
        matched_species = 0

        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = none_if_unknown(row.get("Name"))
                if not name:
                    # si no hay nombre, pasa
                    continue

                # --- Region ---
                reg_name = none_if_unknown(row.get("Region"))
                reg_obj = None
                if reg_name:
                    reg_obj, r_new = Region.objects.get_or_create(name=reg_name)
                    if r_new:
                        created_r += 1

                # --- Sector ---
                sec_name = none_if_unknown(row.get("Sector"))
                sec_obj = None
                if sec_name:
                    sec_obj, sct_new = Sector.objects.get_or_create(name=sec_name, defaults={"region": reg_obj})
                    # si ya existía pero sin region, intenta setearla
                    if not sct_new and reg_obj and sec_obj.region is None:
                        sec_obj.region = reg_obj
                        sec_obj.save(update_fields=["region"])
                    if sct_new:
                        created_sct += 1

                # --- StarSystem ---
                sys_name = none_if_unknown(row.get("System"))
                sys_obj = None
                if sys_name:
                    sys_obj, sys_new = StarSystem.objects.get_or_create(name=sys_name, defaults={"sector": sec_obj})
                    if not sys_new and sec_obj and sys_obj.sector is None:
                        sys_obj.sector = sec_obj
                        sys_obj.save(update_fields=["sector"])
                    if sys_new:
                        created_sys += 1

                # --- Planet upsert por nombre ---
                defaults = dict(
                    star_system=sys_obj,
                    capital_city=none_if_unknown(row.get("Capital City")),
                    grid_coordinates=none_if_unknown(row.get("Grid Coordinates")),
                )
                pl_obj, was_created = Planet.objects.update_or_create(
                    name=name,
                    defaults=defaults,
                )
                created_p += 1 if was_created else 0
                updated_p += 0 if was_created else 1

                # --- Inhabitants -> Species (M2M through PlanetSpecies) ---
                species_list = parse_species_list(row.get("Inhabitants"))
                for sp_name in species_list:
                    sp_obj, _ = Species.objects.get_or_create(name=sp_name)
                    _, link_new = PlanetSpecies.objects.get_or_create(planet=pl_obj, species=sp_obj)
                    if link_new:
                        linked_ps += 1
                        matched_species += 1

        msg = (
            f"Regions +{created_r}, Sectors +{created_sct}, Systems +{created_sys} | "
            f"Planets created {created_p}, updated {updated_p} | Links Planet-Species +{linked_ps} "
            f"(species matched {matched_species})"
        )
        self.stdout.write(self.style.SUCCESS(msg))
