from django.urls import path
from core.views import HomeView
from . import views


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("media/<int:media_id>/", views.media_detail, name="media_detail"),
    path("media/", views.media_view, name="media"),
    path("personajes/", views.index_personajes, name="index_personajes"),
    path("personaje/<int:personaje_id>/", views.detalle_personaje, name="detalle_personaje"),
    path("characters/", views.index_personajes, name="characters"),
    path("species/<int:species_id>/", views.species_detail, name="species_detail"),
    path("species/", views.species_list, name="species_list"),
    path("planets/", views.planets_view, name="planets"),
    path("characters/crear/", views.crear_personaje, name="crear_personaje"),
    path("characters/", views.index_personajes, name="index_personajes"),
    path("characters/<int:personaje_id>/", views.detalle_personaje, name="detalle_personaje"),
    
]
