"""
Comando simple para cargar datos de Star Wars desde data/all.json.

Qué hace:
1) Lee el JSON local (no descarga nada).
2) Crea/actualiza Species, Planet, Affiliation y Character.
3) Vincula Character <-> Affiliation mediante la tabla intermedia (through).

Notas:
- Normaliza campos que pueden venir como lista o string (homeworld, species).
- Convierte height/mass a float si es posible.
- Es idempotente: si ejecutas varias veces, hace upsert por nombre.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path
import json
from core.models import (
    Species, Planet, Affiliation, Character, CharacterAffiliation
)

# ---------- Utilidades pequeñas ----------

def norm_str(v):
    """Devuelve un string limpio. Si es lista, usa el primer string no vacío."""
    if v is None:
        return None
    if isinstance(v, list):
        for x in v:
            if isinstance(x, str) and x.strip():
                return x.strip()
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    return None

def to_float(v):
    """Convierte a float si se puede; si no, None."""
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None

# ---------- Comando ----------

class Command(BaseCommand):
    help = "Carga datos de akabab desde data/all.json (sin descargas)."

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path("data/all.json")
        if not path.exists():
            raise FileNotFoundError("No existe data/all.json. Coloca el JSON en esa ruta.")

        data = json.loads(path.read_text(encoding="utf-8"))

        created_s = created_p = created_a = 0
        created_c = updated_c = linked_ca = 0

        for it in data:
            # --- Species ---
            sp_name = norm_str(it.get("species"))
            sp_obj = None
            if sp_name:
                sp_obj, s_new = Species.objects.get_or_create(name=sp_name)
                if s_new:
                    created_s += 1

            # --- Planet (homeworld como nombre) ---
            hw_name = norm_str(it.get("homeworld"))
            pl_obj = None
            if hw_name:
                pl_obj, p_new = Planet.objects.get_or_create(name=hw_name)
                if p_new:
                    created_p += 1

            # --- Character (upsert por nombre) ---
            ch_defaults = dict(
                species=sp_obj,
                homeworld=pl_obj,
                height_m=to_float(it.get("height")),
                mass_kg=to_float(it.get("mass")),
                gender=norm_str(it.get("gender")),
                eye_color=norm_str(it.get("eyeColor")),
                hair_color=norm_str(it.get("hairColor")),
                skin_color=norm_str(it.get("skinColor")),
                cybernetics=norm_str(it.get("cybernetics")),
                image_url=norm_str(it.get("image")),
                wiki_url=norm_str(it.get("wiki")),
            )
            ch_obj, was_created = Character.objects.update_or_create(
                name=norm_str(it.get("name")),
                defaults=ch_defaults,
            )
            created_c += 1 if was_created else 0
            updated_c += 0 if was_created else 1

            # --- Affiliations (through obligatorio) ---
            for aff_raw in it.get("affiliations") or []:
                aff_name = norm_str(aff_raw)
                if not aff_name:
                    continue
                a_obj, a_new = Affiliation.objects.get_or_create(name=aff_name)
                if a_new:
                    created_a += 1
                # Con through: crear la fila intermedia explícitamente
                _, link_new = CharacterAffiliation.objects.get_or_create(
                    character=ch_obj, affiliation=a_obj
                )
                if link_new:
                    linked_ca += 1

        msg = (
            f"Species +{created_s}, Planets +{created_p}, Affiliations +{created_a} | "
            f"Characters created {created_c}, updated {updated_c} | Links C-A +{linked_ca}"
        )
        self.stdout.write(self.style.SUCCESS(msg))
