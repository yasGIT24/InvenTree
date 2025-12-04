# Inventory Action Permissions

This document describes the role-based access control (RBAC) system for inventory actions in InvenTree.

## Overview

InvenTree now enforces fine-grained permissions for inventory actions using a role-based access control system. This ensures that only authorized users can perform specific inventory operations.

## Available Permissions

The following inventory action permissions are available:

| Permission | Description |
|------------|-------------|
| `stock.can_adjust_stock` | Permission to adjust stock quantities |
| `stock.can_count_stock` | Permission to perform stock counts/audits |
| `stock.can_transfer_stock` | Permission to transfer stock between locations |

## User Roles and Permissions

Permissions are assigned to user roles, which are then assigned to users. A user can perform an action only if they have the required role with the necessary permission.

### Example

1. A user with the "Stock" role and "can_adjust_stock" permission can adjust stock quantities.
2. A user with the "Stock" role but without the "can_adjust_stock" permission cannot adjust stock quantities.

## API Endpoints

The following API endpoints require specific permissions:

| Endpoint | Required Permission |
|----------|---------------------|
| `/api/stock/rbac/adjust/` | `stock.can_adjust_stock` |
| `/api/stock/rbac/count/` | `stock.can_count_stock` |
| `/api/stock/rbac/transfer/` | `stock.can_transfer_stock` |

## Object-Level Permissions

In addition to role-based permissions, the system also enforces object-level permissions. For example:

1. A user may have permission to adjust stock quantities in general, but they might not have permission to adjust a specific stock item.
2. Stock items may have ownership or responsibility restrictions, allowing only specific users to modify them.

## Implementing Custom Inventory Actions

When implementing custom inventory actions, use the `InventoryActionPermission` class to enforce the appropriate permissions:

```python
from InvenTree.api import InventoryActionView

class MyCustomStockAction(InventoryActionView):
    # Specify the required permission
    inventory_action_permission = 'stock.custom_permission'
    
    def perform_action(self, request, *args, **kwargs):
        # Implementation of the custom action
        return Response({'status': 'success'})
```

To add a custom object-level permission check:

```python
class MyCustomStockAction(InventoryActionView):
    inventory_action_permission = 'stock.custom_permission'
    inventory_object_permission = 'check_my_custom_permission'
    
    def check_my_custom_permission(self, request, obj):
        # Custom permission logic
        return True  # or False
```

## Decorator Usage

For existing API views that need inventory action permissions:

```python
from InvenTree.permissions import inventory_permission

@inventory_permission('stock.can_adjust_stock')
def my_view_function(request):
    # Implementation
    return Response({'status': 'success'})
```