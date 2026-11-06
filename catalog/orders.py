"""Create an order and commit stock changes as one transaction."""
import uuid
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import F
from .models import Product, Order, OrderItem


class StockError(ValueError):
    pass


def place_order(user, submission_key, basket, details):
    existing = Order.objects.filter(submission_key=submission_key, customer=user).first()
    if existing:
        return existing
    try:
        with transaction.atomic():
            # The unique key serializes simultaneous submissions of the same form.
            order = Order.objects.create(customer=user, submission_key=submission_key,
                reference=uuid.uuid4(), subtotal=0, total=0, **details)
            products = list(Product.objects.select_for_update().filter(pk__in=basket).order_by('pk'))
            if not basket or len(products) != len(basket):
                raise StockError('Your basket contains a product that is no longer available. Please review your basket.')
            subtotal = Decimal('0.00')
            for product in products:
                quantity = basket[str(product.pk)]
                if type(quantity) is not int or quantity < 1 or quantity > product.stock:
                    raise StockError(f'Only {product.stock} units of {product.name} are available. Please review your basket.')
                # Conditional update also protects stock on databases without row locks.
                if Product.objects.filter(pk=product.pk, stock__gte=quantity).update(stock=F('stock') - quantity) != 1:
                    raise StockError(f'Stock changed for {product.name}. Please review your basket.')
                line_total = product.price * quantity
                OrderItem.objects.create(order=order, product=product, sku=product.sku,
                    name=product.name, quantity=quantity, unit_price=product.price, line_total=line_total)
                subtotal += line_total
            order.subtotal = order.total = subtotal
            order.save(update_fields=['subtotal', 'total'])
            return order
    except IntegrityError:
        existing = Order.objects.filter(submission_key=submission_key, customer=user).first()
        if existing:
            return existing
        raise
