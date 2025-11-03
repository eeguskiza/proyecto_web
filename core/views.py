from django.views.generic import TemplateView
from django.shortcuts import render
from .models import Species, Character
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = []

        for s in Species.objects.all():
            tallest = Character.objects.filter(species=s).order_by("-height_m").first()
            if tallest:
                featured.append(tallest)

        context["featured_characters"] = featured
        return context


def handler_404(request, exception, template_name="404.html"):
    return render(request, template_name, status=404)

def handler_500(request, template_name="500.html"):
    return render(request, template_name, status=500)
