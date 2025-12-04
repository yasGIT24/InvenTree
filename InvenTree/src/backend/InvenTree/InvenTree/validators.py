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


def validate_inventory_data(data):
    """Validate inventory data for various operations.
    
    This function provides high-level validation for inventory operations,
    ensuring that the data meets the required business rules.
    
    Args:
        data: Dictionary containing inventory data to validate
        
    Returns:
        True if data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    errors = {}
    
    # Required fields for inventory operations
    required_fields = ['part', 'quantity']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
            
    # Check if quantity is valid
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                errors['quantity'] = _('Quantity must be greater than zero')
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
            
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_stock_adjustment(data):
    """Validate data for stock adjustment operations.
    
    Args:
        data: Dictionary containing stock adjustment data
        
    Returns:
        True if data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    errors = {}
    
    # Validate basic inventory data first
    validate_inventory_data(data)
    
    # Additional validation for stock adjustments
    if 'notes' not in data or not data['notes']:
        errors['notes'] = _('Notes field is required for stock adjustments')
        
    if 'stock_item' not in data or data['stock_item'] is None:
        errors['stock_item'] = _('Stock item must be specified')
        
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_serial_number_uniqueness(part, serial_number):
    """Validate that a serial number is unique for a given part.
    
    Args:
        part: Part instance
        serial_number: Serial number to check
        
    Returns:
        True if the serial number is unique
        
    Raises:
        ValidationError: If serial number is not unique
    """
    from stock.models import StockItem
    
    if not part:
        return True
        
    if not serial_number:
        return True
        
    # Check if serial number already exists
    if StockItem.objects.filter(part=part, serial=serial_number).exists():
        raise ValidationError({
            'serial': _('Serial number {sn} already exists for part {part}').format(
                sn=serial_number,
                part=part.name
            )
        })
        
    return True


def validate_barcode_uniqueness(barcode_hash):
    """Validate that a barcode hash is unique across the database.
    
    Args:
        barcode_hash: Barcode hash to check
        
    Returns:
        True if the barcode is unique
        
    Raises:
        ValidationError: If barcode is not unique
    """
    from InvenTree.models import InvenTreeBarcodeMixin
    
    if not barcode_hash:
        return True
        
    # Get all model classes that inherit from InvenTreeBarcodeMixin
    from django.apps import apps
    
    for model in apps.get_models():
        if not issubclass(model, InvenTreeBarcodeMixin):
            continue
            
        if model.objects.filter(barcode_hash=barcode_hash).exists():
            raise ValidationError(_('Barcode is already in use'))
            
    return True


def validate_part_stock_coherence(part_id):
    """Validate the coherence between a part and its stock items.
    
    This ensures that stock data and part data are consistent.
    
    Args:
        part_id: ID of the part to validate
        
    Returns:
        True if stock data is coherent
        
    Raises:
        ValidationError: If stock data is incoherent
    """
    from part.models import Part
    
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return True
        
    # Virtual parts cannot have stock
    if part.virtual and part.stock_items.count() > 0:
        raise ValidationError(_('Virtual parts cannot have stock items'))
        
    # Assembly parts must be trackable if they are serialized
    if part.assembly and not part.trackable and part.stock_items.filter(serialized=True).exists():
        raise ValidationError(_('Non-trackable assembly parts cannot have serialized stock items'))
        
    # Trackable parts should not have non-serialized stock items with quantity > 1
    if part.trackable:
        if part.stock_items.filter(serialized=False, quantity__gt=1).exists():
            raise ValidationError(_('Trackable parts cannot have non-serialized stock items with quantity > 1'))
            
    return True
