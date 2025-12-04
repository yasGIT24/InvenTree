"""Add VendorCategory model to company app."""

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields

from common.icons import validate_icon


class Migration(migrations.Migration):
    """Migration to add VendorCategory model."""

    dependencies = [
        ('company', '0081_alter_company_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=250, verbose_name='Description')),
                ('pathstring', models.CharField(blank=True, help_text='Path string for this category', max_length=250, null=True, verbose_name='Path')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('structural', models.BooleanField(default=False, help_text='Companies may not be directly assigned to a structural category, but may be assigned to child categories.', verbose_name='Structural')),
                ('default_keywords', models.CharField(blank=True, help_text='Default keywords for vendors in this category', max_length=250, null=True, verbose_name='Default keywords')),
                ('_icon', models.CharField(blank=True, db_column='icon', help_text='Icon (optional)', max_length=100, null=True, validators=[validate_icon], verbose_name='Icon')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='company.vendorcategory', verbose_name='Parent')),
            ],
            options={
                'verbose_name': 'Vendor Category',
                'verbose_name_plural': 'Vendor Categories',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='company',
            name='category',
            field=mptt.fields.TreeForeignKey(blank=True, help_text='Select vendor category', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='companies', to='company.vendorcategory', verbose_name='Vendor Category'),
        ),
    ]