from django.urls import path
from django.views.decorators.cache import cache_page
from core.views import (
    HomeView,
    MediaListView,
    MediaDetailView,
    CharacterListView,
    CharacterDetailView,
    SpeciesListView,
    SpeciesDetailView,
    PlanetsView,
    PlanetDetailView,
    AffiliationDetailView,
    crear_personaje,
    ChatPageView,
    ChatBotSearchView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("chat/", ChatPageView.as_view(), name="chat"),
    path("media/<int:media_id>/", cache_page(60 * 15)(MediaDetailView.as_view()), name="media_detail"),
    path("media/", cache_page(60 * 15)(MediaListView.as_view()), name="media"),
    path("characters/", CharacterListView.as_view(), name="characters"),
    path("characters/<int:personaje_id>/", cache_page(60 * 15)(CharacterDetailView.as_view()), name="detalle_personaje"),
    path("personajes/", CharacterListView.as_view(), name="index_personajes"),
    path("species/<int:species_id>/", cache_page(60 * 15)(SpeciesDetailView.as_view()), name="species_detail"),
    path("species/", cache_page(60 * 15)(SpeciesListView.as_view()), name="species_list"),
    path("planets/", PlanetsView.as_view(), name="planets"),
    path("planets/<int:planet_id>/", cache_page(60 * 15)(PlanetDetailView.as_view()), name="planet_detail"),
    path("affiliations/<int:affiliation_id>/", cache_page(60 * 15)(AffiliationDetailView.as_view()), name="affiliation_detail"),
    path("characters/crear/", crear_personaje, name="crear_personaje"),
    path("chatbot/search/", ChatBotSearchView.as_view(), name="chatbot_search"),
    
]
