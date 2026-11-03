BASKET_KEY = "basket"


def get_basket(request):
    """Keep each browser session's basket separate, including shared demo logins."""
    owner = str(request.user.pk)
    if request.session.get("basket_owner") != owner:
        request.session[BASKET_KEY] = {}
        request.session["basket_owner"] = owner
    return request.session.get(BASKET_KEY, {}).copy()
