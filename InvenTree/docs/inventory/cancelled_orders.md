# Cancelled Purchase Orders in Inventory Management

<!-- [AGENT GENERATED CODE - REQUIREMENT: US4] -->

## Overview

Cancelled purchase orders are fully integrated into InvenTree's inventory management system, ensuring accurate stock projections and comprehensive visibility across all inventory modules and reconciliation reports. This feature maintains data integrity by properly handling the impact of cancelled orders on inventory calculations.

## Key Features

### Visibility and Tracking
- **Inventory Module Integration**: Cancelled orders appear in all relevant inventory views
- **Reconciliation Reports**: Cancelled orders are clearly marked in audit reports
- **Stock Projection Updates**: Cancelled quantities are automatically excluded from projected stock levels
- **Audit Trail**: Complete tracking of cancellation events and reasons

### Status Management
- **Clear Marking**: Cancelled orders are visually distinguished with warning indicators
- **Reason Tracking**: Capture and store cancellation reasons for audit purposes
- **Date Tracking**: Record cancellation timestamps for reporting
- **Status Filtering**: Filter views to show/hide cancelled orders as needed

## Impact on Inventory Calculations

### Stock Level Projections
<!-- [AGENT GENERATED CODE - REQUIREMENT: US4, US5] -->
When a purchase order is cancelled:
1. **Immediate Update**: Stock projections are recalculated automatically
2. **Quantity Exclusion**: Cancelled order quantities are removed from "Expected Stock"
3. **Availability Calculation**: Available stock projections update in real-time
4. **Dependent Calculations**: Manufacturing and sales projections are updated

### Inventory Reconciliation
Cancelled orders affect reconciliation in several ways:
- **Expected vs Actual**: Cancelled quantities are excluded from expected calculations
- **Variance Analysis**: Proper handling prevents false variance reporting
- **Financial Impact**: Cost implications are tracked and reported
- **Supplier Performance**: Cancellation rates are factored into supplier metrics

## User Interface

### Purchase Order Views
Cancelled purchase orders are displayed with:
- **Status Badge**: Red "CANCELLED" badge with warning icon
- **Visual Indicators**: Crossed-out styling or muted colors
- **Cancellation Info**: Date cancelled and reason (if provided)
- **Impact Notice**: Warning about exclusion from inventory calculations

### Inventory Reports
In inventory modules, cancelled orders:
- Appear in dedicated "Cancelled Orders" section
- Are clearly marked with cancellation status
- Show original quantities and cancellation impact
- Include filters to include/exclude from calculations

### Stock Projection Displays
Stock projections clearly indicate:
- **Current Stock**: Actual on-hand quantities
- **Expected Stock**: Confirmed purchase orders only
- **Excluded Stock**: Cancelled order quantities shown separately
- **Net Projection**: Final calculated available stock

## Reconciliation and Reporting

### Reconciliation Reports
<!-- [AGENT GENERATED CODE - REQUIREMENT: US4] -->
Cancelled orders are integrated into reconciliation reports with:

#### Standard Reports
- **Inventory Variance Report**: Excludes cancelled orders from variance calculations
- **Purchase Order Analysis**: Dedicated section for cancelled order analysis
- **Supplier Performance**: Cancellation rates and impact metrics
- **Financial Reconciliation**: Cost impact of cancelled orders

#### Custom Reports
- Filter options to include/exclude cancelled orders
- Cancellation reason analysis
- Time-based cancellation trends
- Impact on stock availability

### Report Configuration
Users can configure reports to:
- Show cancelled orders separately
- Include/exclude from calculations
- Group by cancellation reason
- Filter by cancellation date range

## API Integration

### Endpoints
- `GET /api/order/po/` - List purchase orders (includes cancelled status)
- `GET /api/order/po/{id}/` - Get PO details including cancellation info
- `PATCH /api/order/po/{id}/cancel/` - Cancel purchase order with reason
- `GET /api/stock/projections/` - Get stock projections (excludes cancelled)

### Data Structure
```json
{
  "pk": 123,
  "reference": "PO-2024-001",
  "status": 70,
  "status_text": "Cancelled",
  "cancelled_date": "2024-03-15T10:30:00Z",
  "cancellation_reason": "Supplier unable to fulfill order",
  "original_quantities": {...},
  "impact_on_projections": {...}
}
```

### Filtering Options
```python
# Get only cancelled orders
cancelled_orders = api.get('/api/order/po/', params={'status': 70})

# Get stock projections (automatically excludes cancelled)
projections = api.get('/api/stock/projections/')

# Get inventory with cancelled order impact
inventory = api.get('/api/stock/', params={'include_cancelled_impact': True})
```

## Business Rules and Validation

### Cancellation Process
1. **Permission Check**: User must have appropriate cancellation rights
2. **Status Validation**: Only pending/partial orders can be cancelled
3. **Impact Assessment**: System calculates inventory impact before cancellation
4. **Reason Requirement**: Cancellation reason may be required (configurable)
5. **Confirmation**: User must confirm understanding of inventory impact

### Automatic Updates
When an order is cancelled:
- Stock projections are immediately recalculated
- Dependent manufacturing orders are notified
- Sales orders with dependent stock are flagged
- Supplier performance metrics are updated
- Financial reports are updated with cost impact

## Permissions and Security
<!-- [AGENT GENERATED CODE - REQUIREMENT: US6] -->

### Required Permissions
- **View Cancelled Orders**: `order.view_purchaseorder`
- **Cancel Orders**: `order.cancel_purchaseorder`
- **View Impact Reports**: `stock.view_projections`
- **Modify Projections**: `stock.change_projections`

### Role-Based Access
- **Purchasing Managers**: Full cancellation and view rights
- **Inventory Managers**: View cancelled orders and impact reports
- **Finance Team**: View financial impact of cancellations
- **Read-Only Users**: View cancelled orders without modification rights

## Performance Considerations

### Optimization Strategies
- **Cached Projections**: Stock calculations are cached and updated incrementally
- **Async Processing**: Large cancellation impacts are processed in background
- **Indexed Queries**: Database indexes optimize cancelled order queries
- **Batch Updates**: Multiple cancellations are processed efficiently

### Monitoring
- **Calculation Time**: Monitor stock projection update performance
- **Query Efficiency**: Track cancelled order query performance
- **Memory Usage**: Monitor memory impact of projection calculations
- **User Experience**: Track UI responsiveness during updates

## Configuration Options

### System Settings
- **Cancellation Reasons**: Configure required/optional reason capture
- **Impact Thresholds**: Set thresholds for automatic notifications
- **Report Defaults**: Configure default cancelled order handling in reports
- **Notification Rules**: Set up automatic notifications for cancellations

### User Preferences
- **Default Filters**: User-specific defaults for showing/hiding cancelled orders
- **Report Settings**: Personal preferences for cancelled order visibility
- **Notification Preferences**: Individual notification settings

## Best Practices

### Cancellation Management
- **Timely Processing**: Cancel orders promptly when supplier confirms cancellation
- **Clear Reasons**: Provide specific, actionable cancellation reasons
- **Impact Assessment**: Review inventory impact before confirming cancellation
- **Communication**: Notify affected departments of significant cancellations

### Reporting and Analysis
- **Regular Review**: Conduct monthly cancelled order analysis
- **Trend Monitoring**: Track cancellation patterns by supplier and product category
- **Cost Impact**: Monitor financial impact of cancelled orders
- **Process Improvement**: Use cancellation data to improve purchasing processes

### Data Integrity
- **Audit Trail**: Maintain complete audit trails for all cancellations
- **Backup Procedures**: Ensure cancelled order data is included in backups
- **Validation Checks**: Regular validation of cancelled order impact calculations
- **Documentation**: Keep clear documentation of cancellation procedures

## Troubleshooting

### Common Issues

**Stock Projections Not Updating**
- *Cause*: Caching issues or background processing delays
- *Solution*: Refresh projections or check background task status

**Cancelled Orders Still Showing in Projections**
- *Cause*: Filtering settings or calculation errors
- *Solution*: Check filter settings and recalculate projections

**Performance Issues with Large Cancellations**
- *Cause*: Complex dependency calculations
- *Solution*: Use background processing for large order cancellations

**Missing Cancellation Information**
- *Cause*: Incomplete cancellation process or data migration issues
- *Solution*: Review cancellation workflow and data integrity

### Diagnostic Tools
- **Projection Calculator**: Verify stock calculation logic
- **Cancelled Order Audit**: Review complete cancellation history
- **Performance Monitor**: Track calculation performance metrics
- **Data Validation**: Verify cancelled order data consistency

<!-- [END AGENT GENERATED CODE] -->

<!-- [AGENT SUMMARY: See requirement IDs US4, US5, US6 for agent run change_impact_analysis_review_final] -->