# Vendor Categories

<!-- [AGENT GENERATED CODE - REQUIREMENT: US1, US2] -->

## Overview

Vendor Categories allow you to organize suppliers and vendors into logical groups for better inventory management and reporting. This feature provides hierarchical categorization with validation to ensure data integrity.

## Features

### Category Management
- **Create Categories**: Add new vendor categories with names and descriptions
- **Hierarchical Structure**: Support for parent-child category relationships  
- **Validation**: Prevent deletion of categories currently in use by companies
- **Bulk Operations**: Import multiple categories via CSV upload

### Data Integrity
- **Deletion Protection**: Categories cannot be deleted if they are assigned to companies
- **Duplicate Prevention**: Category names must be unique across the system
- **Circular Reference Protection**: Prevent categories from being their own parent

## User Interface

### Category List View
The vendor category list provides:
- Overview of all categories with company counts
- Hierarchical display showing parent-child relationships
- Status indicators (Active/Inactive)
- Action buttons for edit, delete, and view operations

### Creating Categories
1. Navigate to Company > Vendor Categories
2. Click "Add Category" button
3. Fill in category details:
   - **Name** (required): Unique category name
   - **Description** (optional): Detailed category description
   - **Parent Category** (optional): Select parent for hierarchy
   - **Active Status**: Enable/disable the category

### Bulk Upload
Categories can be bulk uploaded via CSV file:

#### CSV Format
```csv
name,description,parent,is_active
Electronics,Electronic components and parts,,true
Resistors,Passive electronic components,Electronics,true
Capacitors,Energy storage components,Electronics,true
```

#### Required Fields
- `name`: Category name (unique, max 100 characters)

#### Optional Fields  
- `description`: Category description (max 500 characters)
- `parent`: Parent category name (must exist)
- `is_active`: Boolean (true/false, 1/0, yes/no)

### Validation Rules
<!-- [AGENT GENERATED CODE - REQUIREMENT: US5] -->
- Category names cannot be empty or contain only whitespace
- Names are limited to 100 characters
- Descriptions are limited to 500 characters
- Parent categories cannot create circular references
- Categories cannot be their own parent
- Names must be unique (case-insensitive)

## Permissions
<!-- [AGENT GENERATED CODE - REQUIREMENT: US6] -->

### Required Permissions
- **View**: `company.view_vendorcategory`
- **Add**: `company.add_vendorcategory`  
- **Change**: `company.change_vendorcategory`
- **Delete**: `company.delete_vendorcategory`

### Role-Based Access
- **Admin**: Full access to all operations
- **Company Manager**: Full access to vendor categories
- **Purchasing Manager**: View and edit access
- **Read-Only Users**: View access only

## API Integration

### Endpoints
- `GET /api/company/category/` - List all vendor categories
- `POST /api/company/category/` - Create new category
- `GET /api/company/category/{id}/` - Get category details
- `PATCH /api/company/category/{id}/` - Update category
- `DELETE /api/company/category/{id}/` - Delete category (if unused)

### Example API Usage
```python
import requests

# Create a new category
category_data = {
    "name": "Electronic Components",
    "description": "All electronic parts and components",
    "is_active": True
}

response = requests.post(
    "http://inventree.example.com/api/company/category/",
    json=category_data,
    headers={"Authorization": "Token your-api-token"}
)
```

## Integration with Companies

### Assigning Categories
Companies can be assigned to vendor categories:
1. Edit a company record
2. Select appropriate vendor category from dropdown
3. Save changes

### Category Usage
- Companies display their assigned category in listings
- Categories show count of assigned companies
- Reporting can be filtered by vendor category

## Best Practices

### Naming Conventions
- Use clear, descriptive category names
- Follow consistent naming patterns
- Consider future organizational needs

### Hierarchy Design  
- Keep hierarchies shallow (2-3 levels maximum)
- Group related categories under common parents
- Avoid overly complex structures

### Maintenance
- Regularly review category usage
- Merge or deactivate unused categories  
- Update descriptions as business needs evolve

## Troubleshooting

### Common Issues

**Cannot Delete Category**
- *Cause*: Category is assigned to one or more companies
- *Solution*: Reassign companies to different categories first

**Duplicate Category Name**
- *Cause*: Category name already exists (case-insensitive)
- *Solution*: Choose a unique name or modify existing category

**Bulk Upload Errors**
- *Cause*: Invalid CSV format or data validation failures
- *Solution*: Check CSV format and fix validation errors shown

**Permission Denied**
- *Cause*: Insufficient user permissions
- *Solution*: Contact administrator to grant appropriate roles

## Migration and Import

### Migrating Existing Data
When implementing vendor categories on existing systems:
1. Export current company data
2. Analyze supplier types and create category structure
3. Use bulk upload to create categories
4. Update company records with appropriate categories

### Data Validation
All imported data goes through the same validation as manual entries:
- Name uniqueness checks
- Length limitations
- Parent relationship validation
- Permission verification

<!-- [END AGENT GENERATED CODE] -->

<!-- [AGENT SUMMARY: See requirement IDs US1, US2, US5, US6 for agent run change_impact_analysis_review_final] -->