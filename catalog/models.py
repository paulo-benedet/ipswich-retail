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
