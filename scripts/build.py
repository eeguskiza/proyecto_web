#!/usr/bin/env python3
"""
Script de build rápido para dejar el proyecto listo con un solo comando.

Pasos:
1) Instala dependencias de requirements.txt en el entorno activo.
2) Ejecuta las migraciones.
3) Carga los datos iniciales solo si la base está vacía.

Idempotente: repetirlo no rompe nada.
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
DOTENV_PATH = BASE_DIR / ".env"


def run(cmd, **kwargs):
    """Ejecuta un comando mostrando qué se está haciendo."""
    print(f"→ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=BASE_DIR, **kwargs)


def ensure_repo_root():
    if not (BASE_DIR / "manage.py").exists():
        print("Este script debe ejecutarse desde la raíz del proyecto.")
        sys.exit(1)


def ensure_dotenv():
    """Crea un .env mínimo para desarrollo si no existe."""
    if DOTENV_PATH.exists():
        print("Archivo .env ya existe; no se modifica.")
        return

    secret = secrets.token_urlsafe(50)
    content = [
        "# Variables locales (no subir a control de versiones)",
        f"DJANGO_SECRET_KEY={secret}",
        "DJANGO_DEBUG=true",
        "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost",
        "DJANGO_CSRF_TRUSTED_ORIGINS=",
        "",
    ]
    DOTENV_PATH.write_text("\n".join(content))
    print(f"Generado .env con SECRET_KEY aleatoria en {DOTENV_PATH}")


def install_dependencies():
    reqs = BASE_DIR / "requirements.txt"
    if not reqs.exists():
        print("No se encontró requirements.txt; nada que instalar.")
        return
    print("Instalando dependencias...")
    run([PYTHON, "-m", "pip", "install", "--upgrade", "pip"])
    run([PYTHON, "-m", "pip", "install", "-r", str(reqs)])


def run_migrations():
    print("Aplicando migraciones...")
    run([PYTHON, "manage.py", "migrate"])


def has_core_data():
    code = subprocess.call(
        [
            PYTHON,
            "manage.py",
            "shell",
            "-c",
            (
                "from core.models import Character; import sys; "
                "sys.exit(0 if Character.objects.exists() else 1)"
            ),
        ],
        cwd=BASE_DIR,
    )
    return code == 0


def load_seed_data():
    if has_core_data():
        print("Datos ya presentes; se omite load_data.")
        return
    print("Cargando datos iniciales (akabab + CSV planetas + SWAPI)...")
    run([PYTHON, "manage.py", "load_data"])
    print("   ✔ Datos cargados.")


def main():
    ensure_repo_root()
    ensure_dotenv()
    install_dependencies()
    run_migrations()
    load_seed_data()
    print("\nBuild completado. ¡Listo para ejecutar runserver!")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"\nERROR: el comando falló con código {exc.returncode}.")
        sys.exit(exc.returncode)
