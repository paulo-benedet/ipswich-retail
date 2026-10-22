from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from .forms import CustomerAuthenticationForm


class CustomerLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomerAuthenticationForm

    def get_success_url(self):
        # Issue #1 always leads to the temporary welcome page.
        return reverse("welcome")


@never_cache
@login_required
def welcome(request):
    return render(request, "accounts/welcome.html")
