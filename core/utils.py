import requests

def resolve_swapi_names(urls):
    """Convierte URLs de SWAPI en nombres legibles (planetas, personajes, etc.)."""
    if not urls:
        return []

    names = []
    for url in urls:
        try:
            response = requests.get(url, timeout=3)  #timeout de 3 segundos por si no carga
            if response.status_code == 200:
                data = response.json()
                name = data.get("name") or data.get("title")
                if name:
                    names.append(name)
        except Exception:
            continue

    return names
