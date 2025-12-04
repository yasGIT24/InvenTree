"""Stock data validators for ensuring data integrity in inventory operations."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_stock_transaction(data):
    """Validate a stock transaction to ensure data integrity.
    
    Args:
        data: Dictionary containing stock transaction data
        
    Returns:
        True if the transaction is valid
        
    Raises:
        ValidationError: If transaction data validation fails
    """
    errors = {}
    
    # Required fields for stock transactions
    required_fields = ['part', 'quantity', 'location', 'stockitem_id']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
    
    # Validate quantity
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = float(data['quantity'])
            
            # Quantity must be positive for standard transactions
            if quantity <= 0:
                errors['quantity'] = _('Quantity must be greater than zero')
                
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
    
    # Validate destination for transfers
    if data.get('transaction_type') == 'transfer':
        if 'location' not in data or not data['location']:
            errors['location'] = _('Destination location must be specified for transfers')
    
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_stock_item_creation(data):
    """Validate data for creating a new stock item.
    
    Args:
        data: Dictionary containing stock item creation data
        
    Returns:
        True if data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    errors = {}
    
    # Required fields for stock item creation
    required_fields = ['part', 'location', 'quantity']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
    
    # Validate quantity
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = float(data['quantity'])
            
            if quantity <= 0:
                errors['quantity'] = _('Quantity must be greater than zero')
                
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
    
    # Check serialization
    if data.get('serialized', False):
        if data.get('quantity', 0) != 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock items')
            
        if not data.get('serial'):
            errors['serial'] = _('Serial number must be provided for serialized stock items')
    
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_stock_item_serialized(stock_item):
    """Validate a serialized stock item.
    
    Args:
        stock_item: StockItem object to validate
        
    Returns:
        True if the stock item is valid
        
    Raises:
        ValidationError: If stock item validation fails
    """
    errors = {}
    
    if stock_item.serialized:
        # Serialized stock items must have a serial number
        if not stock_item.serial:
            errors['serial'] = _('Serial number is required for serialized items')
            
        # Serialized stock items must have quantity = 1
        if stock_item.quantity != 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock items')
            
        # Serial must be unique for the part
        if stock_item.part:
            # Check if the serial number is already in use for this part
            from stock.models import StockItem
            
            existing = StockItem.objects.filter(
                part=stock_item.part,
                serial=stock_item.serial
            ).exclude(pk=stock_item.pk)
            
            if existing.exists():
                errors['serial'] = _('Serial number must be unique for this part')
                
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_stock_adjustment(data):
    """Validate a stock adjustment operation.
    
    Args:
        data: Dictionary containing stock adjustment data
        
    Returns:
        True if the adjustment is valid
        
    Raises:
        ValidationError: If adjustment validation fails
    """
    errors = {}
    
    # Required fields for stock adjustments
    required_fields = ['stockitem', 'quantity', 'notes']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
            
    # Get stock item
    stock_item = data.get('stockitem', None)
    
    if stock_item:
        # Validate adjustment quantity
        if 'quantity' in data and data['quantity'] is not None:
            try:
                quantity = float(data['quantity'])
                current_quantity = float(stock_item.quantity)
                
                # Cannot adjust to a negative quantity
                if current_quantity + quantity < 0:
                    errors['quantity'] = _('Adjustment would result in negative stock quantity')
                    
                # Cannot adjust quantity of serialized stock items
                if stock_item.serialized and quantity != 0:
                    errors['quantity'] = _('Cannot adjust quantity of serialized stock items')
                    
            except (ValueError, TypeError):
                errors['quantity'] = _('Invalid quantity value')
    
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_stock_audit(data):
    """Validate a stock audit operation.
    
    Args:
        data: Dictionary containing stock audit data
        
    Returns:
        True if the audit is valid
        
    Raises:
        ValidationError: If audit validation fails
    """
    errors = {}
    
    # Required fields for stock audit
    required_fields = ['stockitem', 'quantity']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
            
    # Check if new quantity is valid
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = float(data['quantity'])
            
            if quantity < 0:
                errors['quantity'] = _('Quantity cannot be negative')
                
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
            
    # Get stock item
    stock_item = data.get('stockitem', None)
    
    if stock_item:
        # Serialized items must have quantity = 1
        if stock_item.serialized and data.get('quantity', 0) != 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock items')
    
    if errors:
        raise ValidationError(errors)
        
    return True