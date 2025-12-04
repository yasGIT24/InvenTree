"""Custom validation routines for the 'importer' app."""

import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Define maximum limits for imported file data
IMPORTER_MAX_FILE_SIZE = 32 * 1024 * 1042
IMPORTER_MAX_ROWS = 5000
IMPORTER_MAX_COLS = 1000


def validate_data_file(data_file):
    """Validate the provided data file."""
    import importer.operations

    filesize = data_file.size

    if filesize > IMPORTER_MAX_FILE_SIZE:
        raise ValidationError(_('Data file exceeds maximum size limit'))

    dataset = importer.operations.load_data_file(data_file)

    if not dataset.headers or len(dataset.headers) == 0:
        raise ValidationError(_('Data file contains no headers'))

    if len(dataset.headers) > IMPORTER_MAX_COLS:
        raise ValidationError(_('Data file contains too many columns'))

    if len(dataset) > IMPORTER_MAX_ROWS:
        raise ValidationError(_('Data file contains too many rows'))


def validate_importer_model_type(value):
    """Validate that the given model type is supported for importing."""
    from importer.registry import supported_models

    if value not in supported_models():
        raise ValidationError(f"Unsupported model type '{value}'")


def validate_field_defaults(value):
    """Validate that the provided value is a valid dict."""
    if value is None:
        return

    if type(value) is not dict:
        # OK if we can parse it as JSON
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError(_('Value must be a valid dictionary object'))

# [AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
def validate_vendor_category_data(row, **kwargs):
    """Validate the vendor category data during import.
    
    This function validates a row of vendor category data to ensure:
    1. Required fields are present
    2. The name is valid 
    3. The parent category exists (if specified)
    4. The parent category is not structural (if specified)

    Args:
        row (dict): A dictionary of key-value pairs for the vendor category
        **kwargs: Additional contextual information
            - model_fields: List of model fields for the vendor category
            - instance: Existing instance if updating
    
    Raises:
        ValidationError: If the validation fails
    """
    from company.validators import validate_vendor_category_name
    from company.models import VendorCategory
    
    errors = {}
    
    # Check for required fields
    if 'name' not in row or not row['name']:
        errors['name'] = _('Name is required')
    
    # Check if parent exists
    if 'parent' in row and row['parent']:
        try:
            # Try to look up the parent by ID first
            try:
                parent_id = int(row['parent'])
                parent = VendorCategory.objects.get(pk=parent_id)
            except (ValueError, VendorCategory.DoesNotExist):
                # If not an ID, try by name
                parent = VendorCategory.objects.filter(name=row['parent']).first()
                
                if parent is None:
                    errors['parent'] = _('Parent category not found: {parent}').format(parent=row['parent'])
            
            # Check if parent is structural
            if parent and parent.structural:
                # If a category is structural, it's not meant to have items directly assigned to it
                errors['parent'] = _('Cannot assign to a structural parent category')
        except Exception as e:
            errors['parent'] = str(e)
    
    # Validate unique name within parent (if name is provided)
    if 'name' in row and row['name'] and 'parent' not in errors:
        parent = None
        if 'parent' in row and row['parent']:
            try:
                try:
                    parent_id = int(row['parent'])
                    parent = VendorCategory.objects.get(pk=parent_id)
                except (ValueError, VendorCategory.DoesNotExist):
                    parent = VendorCategory.objects.filter(name=row['parent']).first()
            except:
                pass
                
        try:
            # Call the existing validation function
            validate_vendor_category_name(row['name'], parent)
        except ValidationError as e:
            if 'name' in e.message_dict:
                errors['name'] = e.message_dict['name']
    
    if errors:
        raise ValidationError(errors)
# [END AGENT GENERATED CODE]