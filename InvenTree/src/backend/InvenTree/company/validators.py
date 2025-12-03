"""Validation functions for the company app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_vendor_category_delete(category):
    """
    Validate that a vendor category can be safely deleted.
    
    Args:
        category: The vendor category to be deleted
        
    Raises:
        ValidationError: If the category is in use and cannot be deleted
    
    [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
    """
    # Check if the category is being used by any companies
    if category.companies.count() > 0:
        raise ValidationError({
            'category': _('Cannot delete category that is in use by companies')
        })
    
    # Check if there are any child categories that depend on this category
    if category.children.count() > 0:
        raise ValidationError({
            'category': _('Cannot delete category that has child categories')
        })