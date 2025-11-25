from django.db import models

from django.db import models

class Species(models.Model):
    name = models.CharField(max_length=80, unique=True)
    classification = models.CharField(max_length=80, null=True, blank=True)
    designation = models.CharField(max_length=80, null=True, blank=True)
    language = models.CharField(max_length=80, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sector(models.Model):
    name = models.CharField(max_length=120, unique=True)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="sectors"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlanetSpecies(models.Model):
    planet = models.ForeignKey("Planet", on_delete=models.CASCADE)
    species = models.ForeignKey("Species", on_delete=models.CASCADE)

    class Meta:
        unique_together = [("planet", "species")]
        indexes = [
            models.Index(fields=["planet", "species"]),
        ]
    
class StarSystem(models.Model):
    name = models.CharField(max_length=120, unique=True)
    sector = models.ForeignKey(
        Sector, null=True, blank=True, on_delete=models.SET_NULL, related_name="systems"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Planet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    climate = models.CharField(max_length=120, null=True, blank=True)
    terrain = models.CharField(max_length=120, null=True, blank=True)
    population = models.BigIntegerField(null=True, blank=True)

    star_system = models.ForeignKey(
        StarSystem, null=True, blank=True, on_delete=models.SET_NULL, related_name="planets")
    capital_city = models.CharField(max_length=120, null=True, blank=True)
    grid_coordinates = models.CharField(max_length=20, null=True, blank=True)

    native_species = models.ManyToManyField(
    "Species", through="PlanetSpecies", related_name="homeworlds", blank=True
    )


    def __str__(self):
        return self.name


class Media(models.Model):
    FILM = "film"
    SERIES = "series"
    MEDIA_TYPES = [(FILM, "Film"), (SERIES, "Series")]

    title = models.CharField(max_length=150, unique=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default=FILM)
    episode = models.IntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    chronology_order = models.IntegerField(null=True, blank=True)
    canonical = models.BooleanField(default=True)
    director = models.CharField(max_length=100, null=True, blank=True)
    producer = models.CharField(max_length=200, null=True, blank=True)
    opening_crawl = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    characters = models.JSONField(null=True, blank=True)
    planets = models.JSONField(null=True, blank=True)
    starships = models.JSONField(null=True, blank=True)
    vehicles = models.JSONField(null=True, blank=True)
    species = models.JSONField(null=True, blank=True)   

    class Meta:
        ordering = ["media_type", "episode", "release_date", "title"]

    def __str__(self):
        return self.title


class Affiliation(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=120, unique=True)
    species = models.ForeignKey(Species, null=True, blank=True, on_delete=models.SET_NULL)
    homeworld = models.ForeignKey(Planet, null=True, blank=True, on_delete=models.SET_NULL)

    height_m = models.FloatField(null=True, blank=True)
    mass_kg = models.FloatField(null=True, blank=True)
    gender = models.CharField(max_length=30, null=True, blank=True)
    birth_year_bby_aby = models.CharField(max_length=20, null=True, blank=True)
    death_year_bby_aby = models.CharField(max_length=20, null=True, blank=True)
    eye_color = models.CharField(max_length=30, null=True, blank=True)
    hair_color = models.CharField(max_length=30, null=True, blank=True)
    skin_color = models.CharField(max_length=30, null=True, blank=True)
    cybernetics = models.TextField(null=True, blank=True)

    image_url = models.URLField(null=True, blank=True)
    wiki_url = models.URLField(null=True, blank=True)

    films_and_series = models.ManyToManyField(
        Media, through="Appearance", related_name="cast", blank=True
    )
    affiliations = models.ManyToManyField(
        Affiliation, through="CharacterAffiliation", related_name="members", blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Appearance(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    credit_order = models.IntegerField(null=True, blank=True)
    role_name = models.CharField(max_length=120, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = [("character", "media")]


class CharacterAffiliation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE)
    since_year_bby_aby = models.CharField(max_length=20, null=True, blank=True)
    until_year_bby_aby = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = [("character", "affiliation")]


class PlanetInquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(null=True, blank=True)
    affiliation = models.CharField(max_length=120, null=True, blank=True)
    planet = models.ForeignKey(
        Planet,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inquiries",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.planet or 'Sin planeta'}"
