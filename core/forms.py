from django import forms

from .models import PlanetInquiry
from .models import Character

class PlanetInquiryForm(forms.ModelForm):
    """Formulario de contacto para enviar información de planetas."""
    class Meta:
        model = PlanetInquiry
        fields = ["name", "email", "affiliation", "planet", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }
class CharacterForm(forms.ModelForm):
    """Formulario básico para crear personajes desde la vista protegida."""
    class Meta:
        model = Character
        fields = ['name', 'species', 'homeworld', 'height_m', 'mass_kg', 'gender','birth_year_bby_aby','death_year_bby_aby','eye_color','hair_color','skin_color','cybernetics', 'image_url','wiki_url']
