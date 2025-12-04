/* [AGENT GENERATED CODE - REQUIREMENT: US6] */
/**
 * PermissionCheck Component
 * 
 * Provides UI permission checking for role-based access control:
 * - Hides/shows components based on user permissions
 * - Integrates with InvenTree RBAC system
 * - Supports granular permission checking
 * - Handles permission loading states
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../functions/api';

/* [AGENT GENERATED CODE - REQUIREMENT: US6] */
// Permission context for global state management
const PermissionContext = createContext({
  permissions: {},
  userRoles: [],
  loading: true,
  checkPermission: () => false,
  hasRole: () => false,
  isOwner: () => false
});

// Permission provider component
export const PermissionProvider = ({ children }) => {
  const [permissions, setPermissions] = useState({});
  const [userRoles, setUserRoles] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserPermissions();
  }, []);

  const loadUserPermissions = async () => {
    try {
      // Load current user info
      const userResponse = await api.get('/auth/user/');
      setCurrentUser(userResponse.data);

      // Load user roles
      const rolesResponse = await api.get('/auth/roles/');
      setUserRoles(rolesResponse.data);

      // Load detailed permissions
      const permissionsResponse = await api.get('/auth/permissions/');
      const permissionMap = {};
      
      permissionsResponse.data.forEach(perm => {
        const [app, action] = perm.split('.');
        if (!permissionMap[app]) {
          permissionMap[app] = {};
        }
        permissionMap[app][action] = true;
      });

      setPermissions(permissionMap);

    } catch (error) {
      console.error('Failed to load user permissions:', error);
      // Set empty permissions on error
      setPermissions({});
      setUserRoles([]);
    } finally {
      setLoading(false);
    }
  };

  // Check if user has a specific permission
  const checkPermission = (permission) => {
    if (!permission || loading) return false;
    
    // Handle dot notation permissions (e.g., 'company.add')
    const parts = permission.split('.');
    if (parts.length !== 2) return false;
    
    const [app, action] = parts;
    return permissions[app]?.[action] || false;
  };

  // Check if user has a specific role
  const hasRole = (roleName) => {
    if (!roleName || loading) return false;
    return userRoles.some(role => role.name === roleName || role.code === roleName);
  };

  // Check if user is owner of a resource
  const isOwner = (resource) => {
    if (!resource || !currentUser) return false;
    return resource.owner === currentUser.pk || resource.created_by === currentUser.pk;
  };

  const contextValue = {
    permissions,
    userRoles,
    currentUser,
    loading,
    checkPermission,
    hasRole,
    isOwner,
    reload: loadUserPermissions
  };

  return (
    <PermissionContext.Provider value={contextValue}>
      {children}
    </PermissionContext.Provider>
  );
};

// Hook for accessing permission context
export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

// [AGENT GENERATED CODE - REQUIREMENT: US6] - Main PermissionCheck Component
const PermissionCheck = ({ 
  permission,
  role,
  owner,
  children,
  fallback = null,
  requireAll = false,
  className,
  style 
}) => {
  const { checkPermission, hasRole, isOwner, loading } = usePermissions();

  // Don't render anything while permissions are loading
  if (loading) {
    return fallback;
  }

  const checks = [];

  // Add permission checks
  if (permission) {
    if (Array.isArray(permission)) {
      if (requireAll) {
        checks.push(permission.every(p => checkPermission(p)));
      } else {
        checks.push(permission.some(p => checkPermission(p)));
      }
    } else {
      checks.push(checkPermission(permission));
    }
  }

  // Add role checks
  if (role) {
    if (Array.isArray(role)) {
      if (requireAll) {
        checks.push(role.every(r => hasRole(r)));
      } else {
        checks.push(role.some(r => hasRole(r)));
      }
    } else {
      checks.push(hasRole(role));
    }
  }

  // Add owner checks
  if (owner) {
    checks.push(isOwner(owner));
  }

  // Determine if user has access
  const hasAccess = checks.length > 0 && (
    requireAll ? checks.every(Boolean) : checks.some(Boolean)
  );

  if (!hasAccess) {
    return fallback;
  }

  // Render children if permissions are satisfied
  if (className || style) {
    return (
      <div className={className} style={style}>
        {children}
      </div>
    );
  }

  return children;
};

// [AGENT GENERATED CODE - REQUIREMENT: US1, US6] - Specific permission check components
export const VendorCategoryPermissionCheck = ({ action, children, fallback }) => {
  const getPermission = (action) => {
    switch (action) {
      case 'view': return 'company.view';
      case 'add': return 'company.add';
      case 'change': return 'company.change';
      case 'delete': return 'company.delete';
      default: return 'company.view';
    }
  };

  return (
    <PermissionCheck 
      permission={getPermission(action)}
      fallback={fallback}
    >
      {children}
    </PermissionCheck>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US3, US6] - Order permission checks
export const OrderPermissionCheck = ({ action, orderType = 'sales', children, fallback }) => {
  const getPermission = (action, type) => {
    const prefix = type === 'sales' ? 'order' : 'order';
    switch (action) {
      case 'view': return `${prefix}.view`;
      case 'add': return `${prefix}.add`;
      case 'change': return `${prefix}.change`;
      case 'delete': return `${prefix}.delete`;
      case 'edit_line_items': return `${prefix}.change`;
      default: return `${prefix}.view`;
    }
  };

  return (
    <PermissionCheck 
      permission={getPermission(action, orderType)}
      fallback={fallback}
    >
      {children}
    </PermissionCheck>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US6] - Admin permission check
export const AdminPermissionCheck = ({ children, fallback }) => {
  return (
    <PermissionCheck 
      role={['admin', 'superuser']}
      fallback={fallback}
    >
      {children}
    </PermissionCheck>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US6] - Manager permission check
export const ManagerPermissionCheck = ({ area, children, fallback }) => {
  const roles = ['admin', 'superuser'];
  
  // Add specific manager roles based on area
  switch (area) {
    case 'inventory':
      roles.push('inventory_manager', 'warehouse_manager');
      break;
    case 'purchasing':
      roles.push('purchasing_manager', 'procurement_manager');
      break;
    case 'sales':
      roles.push('sales_manager', 'order_manager');
      break;
    case 'company':
      roles.push('company_manager', 'vendor_manager');
      break;
    default:
      break;
  }

  return (
    <PermissionCheck 
      role={roles}
      fallback={fallback}
    >
      {children}
    </PermissionCheck>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US6] - HOC for permission checking
export const withPermissions = (WrappedComponent, requiredPermissions) => {
  return function WithPermissionsComponent(props) {
    return (
      <PermissionCheck 
        permission={requiredPermissions.permission}
        role={requiredPermissions.role}
        requireAll={requiredPermissions.requireAll}
        fallback={requiredPermissions.fallback}
      >
        <WrappedComponent {...props} />
      </PermissionCheck>
    );
  };
};

// [AGENT GENERATED CODE - REQUIREMENT: US6] - Permission status helpers
export const PermissionStatus = {
  // Check if user can perform vendor category operations
  canManageVendorCategories: (permissions) => {
    return permissions.checkPermission('company.add') || 
           permissions.checkPermission('company.change');
  },

  // Check if user can edit line items
  canEditLineItems: (permissions, order) => {
    const hasPermission = permissions.checkPermission('order.change');
    const isOwner = permissions.isOwner(order);
    const isManager = permissions.hasRole(['sales_manager', 'admin']);
    
    return hasPermission && (isOwner || isManager);
  },

  // Check if user can cancel purchase orders
  canCancelPurchaseOrders: (permissions, order) => {
    const hasPermission = permissions.checkPermission('order.change');
    const isOwner = permissions.isOwner(order);
    const isManager = permissions.hasRole(['purchasing_manager', 'admin']);
    
    return hasPermission && (isOwner || isManager);
  },

  // Check if user can view sensitive information
  canViewSensitiveInfo: (permissions) => {
    return permissions.hasRole(['admin', 'manager']) ||
           permissions.checkPermission('auth.view_user');
  }
};

export default PermissionCheck;
/* [END AGENT GENERATED CODE] */

/* [AGENT SUMMARY: See requirement IDs US1, US3, US6 for agent run change_impact_analysis_review_final] */