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
│   │   ├── load_data.py       # carga akabab (local)
│   │   └── enrich_swapi.py    # añade películas + apariciones desde SWAPI
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   └── views.py               # (se añadirá en la siguiente fase)
├── swsite/                    # settings y urls del proyecto
├── data/
│   └── all.json               # snapshot del dataset de akabab
├── templates/                 # (se añadirá en la siguiente fase)
├── static/                    # (css/imágenes locales opcionales)
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
### 5) Cargar datos
```bash
python manage.py load_data
````
### 6) Enriquecer con películas y apariciones
```bash
python manage.py enrich_swapi
````
### 7) Levantar servidor
```bash
python manage.py runserver
````

Acceso al admin: `http://127.0.0.1:8000/admin`


## 🧰 Comandos de datos

* `python manage.py load_data`
  Lee `data/all.json` y crea/actualiza Species, Planet, Affiliation, Character.
  *Idempotente* (upsert por nombre).
* `python manage.py enrich_swapi`
  Descarga films de SWAPI y crea **Media** (`film`) + vínculos **Appearance** (Character↔Media).
  Completa metadatos de planetas cuando hay coincidencia por nombre.

## Notas

* Las imágenes **no se descargan**: se usan las URLs remotas de akabab (`image_url`).
* Si SWAPI difiere en algún nombre y no enlaza, el comando lo avisa en consola.

## Créditos

* Datos: [akabab/starwars-api](https://github.com/akabab/starwars-api) y [SWAPI](https://swapi.py4e.com/)
* Autores: **Erik Eguskiza**, **Alexander Jauregui**, **Jon Velasco** y **Alex Ribera**

