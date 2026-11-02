from catalog.views import products
from django.urls import path
from config.health import health, metrics
from accounts.views import CustomerLoginView, welcome

urlpatterns = [path("products/", products, name="products"), path("health/", health, name="health"), path("metrics/", metrics, name="metrics"), path("", CustomerLoginView.as_view(), name="login"), path("welcome/", welcome, name="welcome")]
