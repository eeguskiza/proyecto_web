from django.urls import path
from core.views import HomeView
from . import views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path('media/', views.media_view, name='media'),
]

