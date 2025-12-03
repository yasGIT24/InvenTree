"""Migration for adding approval fields to SalesOrderLineItem model.

[AGENT GENERATED CODE - REQUIREMENT:Edit Individual Line Items in Sales Orders]
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Migration to add approval fields to SalesOrderLineItem model."""

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0053_merge_20230131_0652'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesorderlineitem',
            name='needs_approval',
            field=models.BooleanField(default=False, help_text='Does this line item modification require approval?', verbose_name='Needs Approval'),
        ),
        migrations.AddField(
            model_name='salesorderlineitem',
            name='approved_by',
            field=models.ForeignKey(blank=True, help_text='User who approved this line item change', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_sales_order_lines', to=settings.AUTH_USER_MODEL, verbose_name='Approved By'),
        ),
        migrations.AddField(
            model_name='salesorderlineitem',
            name='approval_date',
            field=models.DateTimeField(blank=True, help_text='Date when line item change was approved', null=True, verbose_name='Approval Date'),
        ),
        migrations.AddField(
            model_name='salesorderlineitem',
            name='pending_changes',
            field=models.JSONField(blank=True, help_text='Pending changes that require approval', null=True, verbose_name='Pending Changes'),
        ),
    ]