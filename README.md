# ***Star Wars Site (Django)***

Bienvenido a **Star Wars Site**. Este proyecto muestra información de personajes de Star Wars, sus especies, planetas y las películas en las que aparecen mediante una web interactiva creada por nosotros. 

## Estructura de datos
**Entities principales del proyecto:**

* **Species**
  Contiene la información básica de cada especie.
  **Campos:** `name`, `classification`, `designation`, `language`.

* **Planet**
  Representa los planetas del universo Star Wars.
  **Campos:** `name`, `climate`, `terrain`, `population`.

* **Media**
  Registra películas o series en las que aparecen los personajes.
  **Campos:** `title`, `media_type` (`film` o `series`), `episode`, `release_date`, `chronology_order`, `canonical`.

* **Affiliation**
  Define organizaciones, ejércitos o facciones a las que pertenecen los personajes.
  **Campos:** `name`, `category`.

* **Character**
  Personajes de la saga, con sus atributos físicos y enlaces a otras entidades.
  **Campos:**
  `name`, `species`, `homeworld`, `height_m`, `mass_kg`, `gender`,
  `birth_year_bby_aby`, `death_year_bby_aby`, `eye_color`, `hair_color`,
  `skin_color`, `cybernetics`, `image_url`, `wiki_url`.
  **Relaciones:**

  * N:M con **Media** → a través de **Appearance**
  * N:M con **Affiliation** → a través de **CharacterAffiliation**

* **Appearance**
  Tabla intermedia que enlaza personajes con películas o series.
  **Campos:** `character`, `media`, `credit_order`, `role_name`, `notes`.
  Única por `(character, media)`.

* **CharacterAffiliation**
  Tabla intermedia que vincula personajes con afiliaciones.
  **Campos:** `character`, `affiliation`, `since_year_bby_aby`, `until_year_bby_aby`, `notes`.
  Única por `(character, affiliation)`.
  

> Los datos utilizados han sido extraidos de: 
> - Personajes, imágenes, especie, afiliaciones: **akabab/starwars-api** (`data/all.json`)  
> - Películas y enlaces persona↔film: **SWAPI** (mirror `swapi.py4e.com`)

## 🗂️ Estructura del repo
```

proyecto_web/
├── core/                      # app principal
│   ├── management/commands/
│   │   └── load_data.py       # comando unificado (akabab + planetas + SWAPI)
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   └── views.py
├── swsite/                    # settings y urls del proyecto
├── data/
│   ├── all.json               # snapshot del dataset de akabab
│   └── sw_planets.csv         # catálogo extendido de planetas
├── templates/
│   ├── index.html             # layout base
│   ├── home.html
│   ├── characters/
│   │   ├── list.html
│   │   └── detail.html
│   ├── media/
│   │   └── list.html
│   ├── planets/
│   │   └── list.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
├── static/
│   ├── css/
│   │   ├── base.css
│   │   ├── home.css
│   │   ├── characters.css
│   │   ├── character_detail.css
│   │   ├── media.css
│   │   ├── planets.css
│   │   ├── chatbot.css
│   │   └── chat_page.css
│   └── js/
│       └── chatbot.js
├── manage.py
└── requirements.txt

````

## Requisitos
- Python 3.11+ (desarrollado con 3.12)
- `pip`, `venv`

## ⚙️ Puesta en marcha (3 pasos)
### 1) Crear y activar entorno
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
````
### 2) Build 
```bash
python scripts/build.py
```
Qué hace `scripts/build.py`:
- Genera un `.env` local con `DJANGO_SECRET_KEY` aleatoria (solo si no existe).
- Instala dependencias de `requirements.txt` (idempotente).
- Aplica migraciones.
- Carga datos de akabab + planetas + SWAPI si la base está vacía.

### 3) Levantar servidor
```bash
python manage.py runserver
````

Acceso al admin: `http://127.0.0.1:8000/admin`

> Para crear un superusuario: `python manage.py createsuperuser`

### Variables para despliegue (producción)
- `DJANGO_SECRET_KEY`: clave secreta robusta (requerida en prod).
- `DJANGO_DEBUG`: `false` en producción.
- `DJANGO_ALLOWED_HOSTS`: lista separada por comas de hosts/DOMINIOS permitidos.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: orígenes (con esquema) para CSRF en reversas/proxy.
- `OPENAI_API_KEY`: clave para que el chatbot pueda usar GPT como fallback (opcional).
- `OPENAI_MODEL`: modelo para el chatbot, por defecto `gpt-4o-mini`.
- `LOAD_SWAPI_ENABLED`: ponlo a `false` si el entorno bloquea SWAPI y quieres que `load_data` no falle (seguirá cargando el JSON local y el CSV).

Ejemplo:
```bash
export DJANGO_SECRET_KEY='cambia-esta-clave'
export DJANGO_DEBUG=false
export DJANGO_ALLOWED_HOSTS='midominio.com,www.midominio.com'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://midominio.com,https://www.midominio.com'
export OPENAI_API_KEY='tu_clave_openai'          # opcional, para el chatbot
export OPENAI_MODEL='gpt-4o-mini'                # opcional
export LOAD_SWAPI_ENABLED=false  # opcional si SWAPI da 403 en CI/host
python manage.py migrate
python manage.py collectstatic --noinput  # STATIC_ROOT apunta a staticfiles/
python manage.py runserver 0.0.0.0:8000
```

> Nota de seguridad: con `DJANGO_DEBUG=false` se activan automáticamente cookies seguras, HSTS, redirección a HTTPS y cabeceras de protección. El `.env` generado por el build es solo para desarrollo; ajusta los valores anteriores al desplegar.

## ✅ Validación W3C (HTML/CSS)
Instala las dependencias de validación (requiere `npm`):
```bash
npm install
```
Lanza los validadores oficiales y guarda los logs en `logs/w3c-html.log` y `logs/w3c-css.log`:
```bash
npm run validate:w3c
```
Usa estos logs para revisar y corregir cualquier incidencia de HTML/CSS reportada.
- Nota: el validador HTML se ejecuta sobre las plantillas Django sin renderizar, por lo que verás falsos positivos (doctype ausente, rutas `{% static %}`, atributos con `{% if %}`, etc.). Para una validación real, valida el HTML renderizado en runtime. El log CSS señala avisos de pseudo-elementos de vendor y la propiedad `clip` deprecada; revisa si quieres ajustarlos.


## 🧰 Comandos de datos

* `python manage.py load_data`
  Ejecuta en cascada las tres etapas (akabab, CSV de planetas y SWAPI).  
  El comando es idempotente y admite `--skip-akabab`, `--skip-planets` y `--skip-swapi`
  para omitir fases concretas si ya están cargadas.

## Notas

* Las imágenes **no se descargan**: se usan las URLs remotas de akabab (`image_url`).
* Si SWAPI difiere en algún nombre y no enlaza, el comando lo avisa en consola.
* La tercera etapa (`load_data` sin `--skip-swapi`) requiere conexión a Internet para consultar el mirror de SWAPI.
* El chatbot de la página `/chat` primero busca en tu BD; si no encuentra nada y defines `OPENAI_API_KEY`, usa GPT como fallback. Los enlaces “Ver más” llevan a las fichas internas de personajes o películas.
* i18n activo (es/en) con selector de idioma en el layout; los textos principales están marcados con `{% trans %}`.

## Créditos

* Datos: [akabab/starwars-api](https://github.com/akabab/starwars-api) y [SWAPI](https://swapi.py4e.com/)
* Autores: **Erik Eguskiza**, **Alexander Jauregui**, **Jon Velasco** y **Alex Ribera**
