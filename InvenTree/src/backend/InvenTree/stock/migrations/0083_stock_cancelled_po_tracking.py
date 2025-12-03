"""Migration to enhance tracking of cancelled purchase orders in inventory.

[AGENT GENERATED CODE - REQUIREMENT:Track and Display Cancelled Supplier Purchase Orders in Inventory]
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Migration to enhance tracking of cancelled purchase orders in inventory."""

    dependencies = [
        ('stock', '0082_stocklocationtype_recursivebooleanfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='is_from_cancelled_po',
            field=models.BooleanField(default=False, help_text='Indicates if this stock item is associated with a cancelled purchase order', verbose_name='From Cancelled PO'),
        ),
        migrations.AddField(
            model_name='stockitemtracking',
            name='po_cancelled',
            field=models.BooleanField(default=False, help_text='Indicates if this tracking entry relates to a cancelled purchase order', verbose_name='PO Cancelled'),
        ),
    ]