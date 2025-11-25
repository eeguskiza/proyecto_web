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
│   └── css/
│       ├── base.css
│       ├── home.css
│       ├── characters.css
│       ├── character_detail.css
│       ├── media.css
│       └── planets.css
├── manage.py
└── requirements.txt

````

## Requisitos
- Python 3.11+ (desarrollado con 3.12)
- `pip`, `venv`

## ⚙️ Puesta en marcha 
### 1) Crear y activar entorno
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
````
### 2) Instalar dependencias
```bash
pip install -r requirements.txt
````
### 3) Migraciones
```bash
python manage.py migrate
````
### 4) Usuario admin
```bash
python manage.py createsuperuser
````
### 5) Cargar y enriquecer datos
```bash
python manage.py load_data
````
### 6) Levantar servidor
```bash
python manage.py runserver
````

Acceso al admin: `http://127.0.0.1:8000/admin`


## 🧰 Comandos de datos

* `python manage.py load_data`
  Ejecuta en cascada las tres etapas (akabab, CSV de planetas y SWAPI).  
  El comando es idempotente y admite `--skip-akabab`, `--skip-planets` y `--skip-swapi`
  para omitir fases concretas si ya están cargadas.

## Notas

* Las imágenes **no se descargan**: se usan las URLs remotas de akabab (`image_url`).
* Si SWAPI difiere en algún nombre y no enlaza, el comando lo avisa en consola.
* La tercera etapa (`load_data` sin `--skip-swapi`) requiere conexión a Internet para consultar el mirror de SWAPI.

## Créditos

* Datos: [akabab/starwars-api](https://github.com/akabab/starwars-api) y [SWAPI](https://swapi.py4e.com/)
* Autores: **Erik Eguskiza**, **Alexander Jauregui**, **Jon Velasco** y **Alex Ribera**

## CONVERTIRTE EN EDITOR
* python manage.py createsuperuser (si esto lo has hecho ya esta)
* desde el shell:
from django.contrib.auth.models import User
usuario = User.objects.get(username='juan')
usuario.is_staff = True        # Acceso al admin
usuario.is_superuser = True    # Permisos totales
usuario.save()
luego runserver te metes en el admin inicias sesion con el user name q has creado y te metes en el normal
