from django.db import migrations

def align_samples(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-001', **{'name': 'Stoneware mug', 'category': 'Home', 'description': 'A comfortable everyday mug with a glazed finish.', 'price': '8.50', 'stock': 24}).update(**{'name': 'Stoneware mug', 'category': 'Kitchen', 'description': 'A warm start to your everyday.', 'price': '12.00', 'stock': 12})
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-002', **{'name': 'Cotton tea towels', 'category': 'Home', 'description': 'A practical pair of soft cotton kitchen towels.', 'price': '12.00', 'stock': 18}).update(**{'name': 'Cotton tote bag', 'category': 'Accessories', 'description': 'Room for the little essentials.', 'price': '18.00', 'stock': 8})
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-003', **{'name': 'Desk notebook', 'category': 'Stationery', 'description': 'A lined notebook for ideas, plans and everyday notes.', 'price': '6.75', 'stock': 35}).update(**{'name': 'Linen cushion', 'category': 'Living', 'description': 'An easy layer of natural texture.', 'price': '24.00', 'stock': 6})
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-004', **{'name': 'Ballpoint pen set', 'category': 'Stationery', 'description': 'Three smooth-writing pens for your desk or bag.', 'price': '4.50', 'stock': 0}).update(**{'name': 'Oak serving board', 'category': 'Kitchen', 'description': 'Made for sharing around the table.', 'price': '28.00', 'stock': 5})
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-005', **{'name': 'Canvas tote bag', 'category': 'Accessories', 'description': 'A reusable cotton bag for your daily essentials.', 'price': '14.00', 'stock': 12}).update(**{'name': 'Glass bud vase', 'category': 'Living', 'description': 'A small home for fresh stems.', 'price': '16.00', 'stock': 9})
    Product.objects.using(schema_editor.connection.alias).filter(sku='IR-006', **{'name': 'Stainless steel bottle', 'category': 'Accessories', 'description': 'A reusable 500 ml bottle for days on the go.', 'price': '19.95', 'stock': 8}).update(**{'name': 'Woven throw', 'category': 'Living', 'description': 'For slow evenings and cosy corners.', 'price': '36.00', 'stock': 0})

class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.AlterModelOptions(name="product", options={"ordering": ["sku", "pk"]}), migrations.RunPython(align_samples, migrations.RunPython.noop)]
