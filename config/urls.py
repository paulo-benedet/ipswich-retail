from django.urls import path
from accounts.views import CustomerLoginView, welcome

urlpatterns = [path("", CustomerLoginView.as_view(), name="login"), path("welcome/", welcome, name="welcome")]
