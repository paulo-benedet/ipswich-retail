from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from .forms import CustomerAuthenticationForm


class CustomerLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomerAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.DEMO_ENABLED:
            context["demo_details"] = {"email": settings.DEMO_EMAIL, "password": settings.DEMO_PASSWORD}
        return context

    def get_success_url(self):
        # Successful login now opens the Sprint 2 catalogue.
        return reverse("products")


@never_cache
@login_required
def welcome(request):
    return redirect("products")
