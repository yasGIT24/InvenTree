"""Importer functionality for the company app.

Imports vendor categories from external data sources (e.g. CSV file)

[AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
"""

from django.utils.translation import gettext_lazy as _

import importer.helpers
import importer.models
from importer.mixins import ImporterMixin
from importer.validators import ImportValidationError

from .models import VendorCategory


class VendorCategoryImporter(ImporterMixin):
    """Class for importing vendor category data."""

    model_class = VendorCategory

    # Override default fields
    field_list = [
        'name',
        'description',
        'parent',
    ]

    required_fields = ['name']

    def process_row(self, row, **kwargs):
        """Process a single row of vendor category data."""

        name = str(row.get('name', '')).strip()
        description = str(row.get('description', '')).strip()
        parent_name = str(row.get('parent', '')).strip()

        # Validate name field
        if not name:
            raise ImportValidationError(_("Vendor category name must not be empty"))

        parent = None

        if parent_name:
            try:
                parent = VendorCategory.objects.get(name=parent_name)
            except VendorCategory.DoesNotExist:
                raise ImportValidationError(
                    _("Parent category '{parent}' does not exist").format(parent=parent_name)
                )

        # Check if this vendor category already exists
        try:
            category = VendorCategory.objects.get(name=name, parent=parent)
            # Category already exists - update it
            category.description = description
            category.save()
            return category
        except VendorCategory.DoesNotExist:
            # Create a new vendor category
            category = VendorCategory.objects.create(
                name=name,
                description=description,
                parent=parent
            )
            
            return category