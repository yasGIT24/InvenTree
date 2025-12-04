"""Importer functionality for the Company app."""

import logging
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext_lazy as _

import common.models
from company.models import Company
from importer.models import DataImportRow

logger = logging.getLogger('inventree')


# [AGENT GENERATED CODE - REQUIREMENT:US2-AC1,US2-AC2,US2-AC3]
class CompanyImporter:
    """Class for importing company data via bulk upload."""

    @staticmethod
    def validate_import_data(rows: list[DataImportRow]) -> tuple[int, int]:
        """Validate the data for a batch of company imports.
        
        Arguments:
            rows: List of DataImportRow objects to validate
            
        Returns:
            Tuple of (valid_rows, invalid_rows) counts
        """
        valid_rows = 0
        invalid_rows = 0
        
        for row in rows:
            # Skip rows that have already been processed
            if row.complete:
                continue
                
            # Validate the data for this row
            if row.validate():
                valid_rows += 1
            else:
                invalid_rows += 1
        
        return valid_rows, invalid_rows
    
    @staticmethod
    def import_company_data(rows: list[DataImportRow]) -> tuple[int, int]:
        """Import a batch of company data.
        
        Arguments:
            rows: List of DataImportRow objects to import
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created = 0
        updated = 0
        
        for idx, row in enumerate(rows):
            # Skip rows that have already been processed
            if row.complete:
                continue
                
            # Extract the required fields for this row
            row_data = row.serializer_data()
            
            try:
                # Determine if we're updating an existing company or creating a new one
                if row.session.update_records and 'id' in row_data:
                    # Update existing company
                    company = Company.objects.get(pk=row_data['id'])
                    
                    # Update the company
                    for key, value in row_data.items():
                        if key != 'id':
                            setattr(company, key, value)
                            
                    company.save()
                    updated += 1
                    row.complete = True
                    row.save()
                else:
                    # Create new company
                    if row.validate(commit=True):
                        created += 1
            except Exception as e:
                # Log the error
                logger.error(f"Error importing company data: {e}")
                row.errors = {'error': str(e)}
                row.save()
        
        return created, updated