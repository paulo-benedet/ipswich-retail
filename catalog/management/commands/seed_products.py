from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Product


class Command(BaseCommand):
    help = "Add missing PoC demonstration products without changing existing records."

    @transaction.atomic
    def handle(self, *args, **options):
        samples = [('IR-001', 'Stoneware mug', 'Kitchen', 'A warm start to your everyday.', '12.00', 12), ('IR-002', 'Cotton tote bag', 'Accessories', 'Room for the little essentials.', '18.00', 8), ('IR-003', 'Linen cushion', 'Living', 'An easy layer of natural texture.', '24.00', 6), ('IR-004', 'Oak serving board', 'Kitchen', 'Made for sharing around the table.', '28.00', 5), ('IR-005', 'Glass bud vase', 'Living', 'A small home for fresh stems.', '16.00', 9), ('IR-006', 'Woven throw', 'Living', 'For slow evenings and cosy corners.', '36.00', 0)]
        created = 0
        for sku, name, category, description, price, stock in samples:
            _, added = Product.objects.get_or_create(sku=sku, defaults=dict(name=name, category=category, description=description, price=price, stock=stock))
            created += added
        self.stdout.write(self.style.SUCCESS(f"Created {created} demonstration products; existing products preserved."))
