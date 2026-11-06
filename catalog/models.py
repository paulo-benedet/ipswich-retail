from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=60)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sku", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name="product_positive_price")]

    def __str__(self):
        return self.name


class Order(models.Model):
    reference = models.UUIDField(unique=True, editable=False)
    customer = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    submission_key = models.UUIDField(unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    payment_method = models.CharField(max_length=30, default='cash_on_delivery')
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    sku = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
