from catalog.views import products, add_to_basket, view_basket
from django.urls import path
from config.health import health, metrics
from accounts.views import CustomerLoginView, welcome

urlpatterns = [path("basket/", view_basket, name="basket"), path("basket/add/<int:product_id>/", add_to_basket, name="add_to_basket"), path("products/", products, name="products"), path("health/", health, name="health"), path("metrics/", metrics, name="metrics"), path("", CustomerLoginView.as_view(), name="login"), path("welcome/", welcome, name="welcome")]
