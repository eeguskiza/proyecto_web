from django.urls import path
from core.views import HomeView
from . import views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path('media/', views.media_view, name='media'),
    path('personajes/', views.index_personajes, name='index_personajes'),
    path('personaje/<int:personaje_id>/', views.detalle_personaje, name='detalle_personaje'),
    path('characters/', views.index_personajes, name='characters'),
]

