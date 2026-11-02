from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .models import Product


@never_cache
@login_required
def products(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    return render(request, "catalog/products.html", {"products": products, "query": query})
