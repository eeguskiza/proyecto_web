from django import forms

from .models import PlanetInquiry


class PlanetInquiryForm(forms.ModelForm):
    class Meta:
        model = PlanetInquiry
        fields = ["name", "email", "affiliation", "planet", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }
