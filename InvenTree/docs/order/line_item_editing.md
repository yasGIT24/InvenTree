# Line Item Editing in Sales Orders

<!-- [AGENT GENERATED CODE - REQUIREMENT: US3] -->

## Overview

The line item editing feature allows authorized users to modify individual line items within sales orders, including quantity, price, and product code adjustments. This functionality includes comprehensive validation, approval workflows, and inventory checking to maintain data integrity.

## Features

### Editable Fields
- **Quantity**: Adjust ordered quantities with inventory validation
- **Unit Price**: Modify pricing with approval thresholds
- **Product Code/Reference**: Update part references or customer codes
- **Line Notes**: Add or modify line-specific notes

### Validation and Controls
- **Inventory Checking**: Real-time availability validation
- **Approval Workflows**: Automatic approval routing for significant changes
- **Permission Validation**: Role-based access control
- **Status Restrictions**: Prevent editing of shipped or completed orders

## User Interface

### Accessing Line Item Editor
1. Navigate to Sales Order detail page
2. Locate the line items section
3. Click the "Edit" icon next to the desired line item
4. The line item editor dialog will open

### Editor Interface Elements
- **Current vs New Values**: Side-by-side comparison
- **Validation Feedback**: Real-time error and warning messages
- **Inventory Status**: Available vs requested quantity display
- **Change Summary**: Overview of modifications before saving
- **Approval Indicator**: Shows when changes require approval

## Business Rules

### When Line Items Can Be Edited
<!-- [AGENT GENERATED CODE - REQUIREMENT: US5] -->
- Sales order status is "Pending" or "In Progress"
- Line item has not been fully allocated or shipped
- User has appropriate permissions
- No active locks from other editors

### When Line Items Cannot Be Edited
- Sales order is completed, cancelled, or shipped
- Line item is fully allocated to stock
- User lacks required permissions
- Another user is currently editing the same line item

### Approval Requirements
<!-- [AGENT GENERATED CODE - REQUIREMENT: US3] -->
Changes that require approval:
- **Quantity increases** > 10% of original value
- **Price changes** > 5% of original value  
- **Quantity doubles** or more from original
- **Total line value changes** > $1000 (configurable)

## Validation Rules

### Quantity Validation
- Must be positive number greater than 0
- Cannot exceed maximum reasonable limits (500% of original)
- Checked against available inventory
- Validated against part packaging/minimum order quantities

### Price Validation
- Must be non-negative number
- Cannot exceed maximum reasonable limits (200% of original)
- Compared against part pricing data for warnings
- Currency validation for multi-currency environments

### Reference/Product Code
- Maximum length of 100 characters
- Special character validation
- Optional customer-specific format validation

## Inventory Integration

### Real-Time Availability Checking
When quantities are modified:
1. System queries current stock levels
2. Calculates total available quantity across all locations
3. Compares against requested quantity
4. Displays warnings for insufficient stock
5. Prevents saving if negative inventory would result

### Stock Allocation Impact
- Existing allocations are preserved during editing
- Additional quantity requires new allocations
- Reduced quantity releases excess allocations
- Inventory projections are updated in real-time

## Approval Workflow

### Automatic Approval Routing
When changes exceed thresholds:
1. **Submission**: Changes are saved in "Pending Approval" status
2. **Notification**: Designated approvers are notified
3. **Review**: Approvers can view change details and rationale
4. **Decision**: Approve, reject, or request modifications
5. **Implementation**: Approved changes are applied to the order

### Approval Levels
- **Level 1**: Line managers for moderate changes
- **Level 2**: Department managers for significant changes  
- **Level 3**: Finance approval for high-value changes

### Notification System
- Email notifications to approvers
- In-app notifications and task lists
- Escalation after configured timeouts
- Status updates to original requestor

## Permissions and Security
<!-- [AGENT GENERATED CODE - REQUIREMENT: US6] -->

### Required Permissions
- **View**: `order.view_salesorderlineitem`
- **Edit**: `order.change_salesorderlineitem`
- **Approve**: `order.approve_lineitem_changes`

### Role-Based Access
- **Sales Representatives**: Edit own orders only
- **Sales Managers**: Edit all orders in their territory
- **Order Managers**: Full edit access across all orders
- **Finance Team**: Approval rights for price changes
- **Admin**: Override capabilities for all operations

### Audit Trail
All line item changes are logged:
- User who made the change
- Timestamp of modification
- Original and new values
- Approval status and approver
- Reason/justification for change

## API Integration

### Endpoints
- `GET /api/order/so-line/{id}/can-edit/` - Check edit permissions
- `PATCH /api/order/so-line/{id}/` - Update line item
- `GET /api/order/so-line/{id}/inventory/` - Check inventory availability
- `POST /api/order/so-line/{id}/approve/` - Approve pending changes

### Example Usage
```python
import requests

# Check if line item can be edited
response = requests.get(
    "http://inventree.example.com/api/order/so-line/123/can-edit/",
    headers={"Authorization": "Token your-api-token"}
)

if response.json()["can_edit"]:
    # Update the line item
    update_data = {
        "quantity": 150,
        "price": "12.50",
        "notes": "Customer requested quantity increase"
    }
    
    response = requests.patch(
        "http://inventree.example.com/api/order/so-line/123/",
        json=update_data,
        headers={"Authorization": "Token your-api-token"}
    )
```

## Error Handling

### Common Validation Errors
- **Insufficient Inventory**: Requested quantity exceeds available stock
- **Invalid Price**: Negative or unreasonably high pricing
- **Permission Denied**: User lacks required editing permissions
- **Order Status**: Cannot edit completed or shipped orders
- **Concurrent Edit**: Another user is editing the same line item

### Error Resolution
1. **Check Inventory**: Verify stock levels and allocations
2. **Review Permissions**: Ensure user has appropriate roles
3. **Order Status**: Confirm order is in editable state  
4. **Refresh Data**: Reload order data to clear concurrent edit locks

## Best Practices

### Data Entry Guidelines
- Always provide clear justification for significant changes
- Verify inventory availability before increasing quantities
- Use consistent product code formatting
- Document customer requests in line notes

### Approval Management
- Set reasonable approval thresholds based on business risk
- Establish clear escalation procedures
- Train approvers on validation criteria
- Monitor approval turnaround times

### System Administration
- Regular review of permission assignments
- Monitor edit patterns for training needs  
- Backup order data before major modifications
- Test approval workflows after system updates

## Troubleshooting

### Cannot Edit Line Item
- **Check Order Status**: Ensure order is not completed/shipped
- **Verify Permissions**: Confirm user has edit rights
- **Review Allocations**: Check if line item is fully allocated
- **Clear Locks**: Release concurrent edit locks if needed

### Approval Not Triggered  
- **Threshold Check**: Verify changes exceed approval limits
- **Workflow Configuration**: Ensure approval rules are active
- **User Setup**: Confirm approvers are properly configured
- **Notification Settings**: Check email and system notifications

### Inventory Validation Errors
- **Refresh Stock Data**: Update inventory information
- **Check Allocations**: Review existing stock allocations  
- **Location Access**: Ensure user can access relevant stock locations
- **Part Status**: Verify part is active and purchasable

<!-- [END AGENT GENERATED CODE] -->

<!-- [AGENT SUMMARY: See requirement IDs US3, US5, US6 for agent run change_impact_analysis_review_final] -->