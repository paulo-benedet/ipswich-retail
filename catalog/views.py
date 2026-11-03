from urllib.parse import urlencode
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .models import Product


@never_cache
@login_required
def products(request):
    query = request.GET.get("q", "").strip()
    categories = list(Product.objects.exclude(category="").order_by("category").values_list("category", flat=True).distinct())
    category = request.GET.get("category", "")
    if category not in categories:
        category = ""
    products = Product.objects.all()
    if category:
        products = products.filter(category=category)
    if query:
        products = products.filter(name__icontains=query)
    clear_url = reverse("products")
    if category:
        clear_url += "?" + urlencode({"category": category})
    return render(request, "catalog/products.html", {
        "products": products, "query": query, "categories": categories,
        "selected_category": category, "clear_search_url": clear_url,
    })
