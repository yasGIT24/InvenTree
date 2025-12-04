"""Custom field validators for InvenTree."""

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint
from moneyed import CURRENCIES

import InvenTree.conversion
from common.settings import get_global_setting


def validate_physical_units(unit):
    """Ensure that a given unit is a valid physical unit."""
    unit = unit.strip()

    # Ignore blank units
    if not unit:
        return

    ureg = InvenTree.conversion.get_unit_registry()

    try:
        ureg(unit)
    except (AssertionError, AttributeError, pint.errors.UndefinedUnitError):
        raise ValidationError(_('Invalid physical unit'))


def validate_currency_code(code):
    """Check that a given code is a valid currency code."""
    if code not in CURRENCIES:
        raise ValidationError(_('Not a valid currency code'))


def allowable_url_schemes():
    """Return the list of allowable URL schemes.

    In addition to the default schemes allowed by Django,
    the install configuration file (config.yaml) can specify
    extra schemas
    """
    # Default schemes
    schemes = ['http', 'https', 'ftp', 'ftps']

    extra = settings.EXTRA_URL_SCHEMES

    for e in extra:
        if e.lower() not in schemes:
            schemes.append(e.lower())

    return schemes


class AllowedURLValidator(validators.URLValidator):
    """Custom URL validator to allow for custom schemes."""

    def __call__(self, value):
        """Validate the URL."""
        self.schemes = allowable_url_schemes()

        # Determine if 'strict' URL validation is required (i.e. if the URL must have a schema prefix)
        strict_urls = get_global_setting('INVENTREE_STRICT_URLS', cache=False)

        if value is not None:
            value = str(value).strip()

        if value and not strict_urls:
            # Allow URLs which do not have a provided schema
            if '://' not in value:
                # Validate as if it were http
                value = 'http://' + value

        super().__call__(value)


def validate_purchase_order_reference(value):
    """Validate the 'reference' field of a PurchaseOrder."""
    from order.models import PurchaseOrder

    # If we get to here, run the "default" validation routine
    PurchaseOrder.validate_reference_field(value)


def validate_sales_order_reference(value):
    """Validate the 'reference' field of a SalesOrder."""
    from order.models import SalesOrder

    # If we get to here, run the "default" validation routine
    SalesOrder.validate_reference_field(value)


def validate_tree_name(value):
    """Placeholder for legacy function used in migrations."""


# [AGENT GENERATED CODE - REQUIREMENT:US5-AC1,US5-AC2]
def validate_inventory_data(data, field_map=None):
    """Validate inventory data for operations across the system.
    
    This function provides comprehensive data integrity validation for inventory operations.
    
    Args:
        data: Dictionary containing data to validate
        field_map: Optional mapping of field names to validation functions
        
    Returns:
        True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Basic validation of common fields
    if 'quantity' in data:
        try:
            quantity = float(data['quantity'])
            if quantity < 0:
                errors['quantity'] = _('Quantity must be a positive number')
        except (ValueError, TypeError):
            errors['quantity'] = _('Quantity must be a valid number')
    
    # Validate serialized items have quantity=1
    if 'serial' in data and data.get('serial') and 'quantity' in data:
        try:
            quantity = float(data['quantity'])
            if quantity != 1:
                errors['quantity'] = _('Quantity must be 1 for serialized items')
        except (ValueError, TypeError):
            errors['quantity'] = _('Quantity must be a valid number')
    
    # Validate part numbers/SKUs if provided
    if 'SKU' in data and not data.get('SKU', '').strip():
        errors['SKU'] = _('SKU cannot be blank')
    
    # Validate supplier part references if provided
    if 'MPN' in data and not data.get('MPN', '').strip():
        errors['MPN'] = _('Manufacturer part number cannot be blank')
    
    # Run custom field validations if provided
    if field_map:
        for field, validator in field_map.items():
            if field in data and validator and callable(validator):
                try:
                    validator(data[field])
                except ValidationError as e:
                    errors[field] = str(e)
    
    if errors:
        raise ValidationError(errors)
    
    return True
