from urllib.parse import urlencode
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import AddToBasketForm
from .basket import get_basket, get_basket_summary, get_basket_lines, BASKET_KEY
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
    basket = get_basket(request)
    for product in products:
        product.basket_quantity = basket.get(str(product.pk), 0)
        product.remaining = max(0, product.stock - product.basket_quantity)
    clear_url = reverse("products")
    if category:
        clear_url += "?" + urlencode({"category": category})
    return render(request, "catalog/products.html", {
        "products": products, "query": query, "categories": categories,
        "basket_summary": get_basket_summary(basket),
        "selected_category": category, "clear_search_url": clear_url,
    })


@never_cache
@login_required
@require_POST
def add_to_basket(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = AddToBasketForm(request.POST)
    basket = get_basket(request)
    current = basket.get(str(product.pk), 0)
    if not form.is_valid():
        messages.error(request, "Choose a positive whole-number quantity.")
    elif product.stock == 0:
        messages.error(request, f"{product.name} is currently unavailable.")
    elif current + form.cleaned_data["quantity"] > product.stock:
        messages.error(request, f"Only {product.stock} units of {product.name} are available; your basket already contains {current}.")
    else:
        quantity = form.cleaned_data["quantity"]
        basket[str(product.pk)] = current + quantity
        request.session[BASKET_KEY] = basket
        messages.success(request, f"Added {quantity} × {product.name} to your basket.")
    # Preserve catalogue context without accepting an arbitrary redirect URL.
    params = {key: request.POST.get(key, "").strip() for key in ("q", "category")}
    params = {key: value for key, value in params.items() if value}
    target = reverse("products")
    if params:
        target += "?" + urlencode(params)
    return redirect(target)


@never_cache
@login_required
def view_basket(request):
    basket = get_basket(request)
    lines = get_basket_lines(basket)
    return render(request, "catalog/basket.html", {
        "lines": lines, "basket_summary": get_basket_summary(basket),
    })
