from decimal import Decimal
from .models import Product


BASKET_KEY = "basket"


def get_basket(request):
    """Keep each browser session's basket separate, including shared demo logins."""
    owner = str(request.user.pk)
    if request.session.get("basket_owner") != owner:
        request.session[BASKET_KEY] = {}
        request.session["basket_owner"] = owner
    return request.session.get(BASKET_KEY, {}).copy()


def get_basket_lines(basket):
    lines = []
    for product in Product.objects.filter(pk__in=basket):
        quantity = basket[str(product.pk)]
        lines.append({"product": product, "quantity": quantity, "total": product.price * quantity})
    return lines


def get_basket_summary(basket):
    """Count selected units and calculate their current catalogue subtotal."""
    count = 0
    subtotal = Decimal("0.00")
    # Query the entire basket, independently of search/category filters.
    for product in Product.objects.filter(pk__in=basket):
        quantity = basket[str(product.pk)]
        count += quantity
        subtotal += product.price * quantity
    return {"count": count, "subtotal": subtotal}
