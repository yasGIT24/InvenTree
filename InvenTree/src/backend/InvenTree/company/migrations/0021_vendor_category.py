"""Migration to add the VendorCategory model.

[AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
[AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
"""

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):
    """Migration to add VendorCategory model."""

    dependencies = [
        ('company', '0020_auto_20220113_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=250, verbose_name='Description')),
                ('pathstring', models.CharField(blank=True, help_text='Internal path field', max_length=250, null=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='company.vendorcategory', verbose_name='Parent')),
            ],
            options={
                'verbose_name': 'Vendor Category',
                'verbose_name_plural': 'Vendor Categories',
                'unique_together': {('name', 'parent')},
            },
        ),
        migrations.AddField(
            model_name='company',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Select vendor category', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_companies', to='company.vendorcategory', verbose_name='Vendor Category'),
        ),
    ]