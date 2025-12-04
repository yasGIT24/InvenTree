"""Validators for the company app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_vendor_category_name(name, parent=None):
    """Validate that the vendor category name is unique within the parent category.
    
    Args:
        name (str): The name of the vendor category
        parent (VendorCategory, optional): The parent category. Defaults to None.
    
    Raises:
        ValidationError: If the category name is already in use in the parent category
    """
    from company.models import VendorCategory

    # Filter by parent
    if parent is not None:
        categories = VendorCategory.objects.filter(parent=parent)
    else:
        categories = VendorCategory.objects.filter(parent=None)

    categories = categories.exclude(name=name)

    names = categories.values_list('name', flat=True)

    if name.lower() in [n.lower() for n in names]:
        raise ValidationError({
            'name': _('Vendor category name must be unique within the parent category')
        })


def validate_company_category(company):
    """Validate that the selected category is not a structural category.

    Args:
        company (Company): The company instance to validate

    Raises:
        ValidationError: If the category is a structural category
    """
    if company.category and company.category.structural:
        raise ValidationError({
            'category': _('Company cannot be assigned to a structural category')
        })


# [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
def validate_vendor_category_in_use(category):
    """Check if a vendor category is in use by any Company objects.
    
    A vendor category is considered "in use" if:
    1. Any companies are directly assigned to this category
    2. Any child categories exist under this category

    Args:
        category (VendorCategory): The vendor category to check

    Returns:
        tuple: (is_in_use, message) where is_in_use is a boolean indicating if the category
               is in use, and message is a string explaining why it can't be deleted
    """
    from company.models import Company

    # Check if any companies are directly assigned to this category
    company_count = Company.objects.filter(category=category).count()

    if company_count > 0:
        return True, _('Cannot delete this category: {n} companies are assigned to it').format(n=company_count)

    # Check if there are any child categories
    child_count = category.get_children().count()

    if child_count > 0:
        return True, _('Cannot delete this category: {n} child categories exist').format(n=child_count)

    return False, ''
# [END AGENT GENERATED CODE]