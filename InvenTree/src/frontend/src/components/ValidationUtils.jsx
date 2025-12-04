/* [AGENT GENERATED CODE - REQUIREMENT: US1, US2, US3, US5] */
/**
 * ValidationUtils Component/Module
 * 
 * Provides frontend validation utilities for:
 * - Vendor category validation
 * - Line item editing validation  
 * - Data integrity checks
 * - Form validation helpers
 */

import { 
  validateRequired,
  validateEmail, 
  validateUrl,
  validateNumeric,
  validateDecimal 
} from '../utils/validators';

/* [AGENT GENERATED CODE - REQUIREMENT: US5] */
export const ValidationUtils = {
  
  // [AGENT GENERATED CODE - REQUIREMENT: US1, US2] - Vendor Category Validation
  validateVendorCategory: (categoryData) => {
    const errors = [];
    
    // Required field validation
    if (!categoryData.name || !categoryData.name.trim()) {
      errors.push('Category name is required');
    }
    
    // Name length validation
    if (categoryData.name && categoryData.name.length > 100) {
      errors.push('Category name cannot exceed 100 characters');
    }
    
    // Name format validation (no special characters except spaces, hyphens, underscores)
    if (categoryData.name && !/^[a-zA-Z0-9\s\-_]+$/.test(categoryData.name)) {
      errors.push('Category name can only contain letters, numbers, spaces, hyphens and underscores');
    }
    
    // Description length validation
    if (categoryData.description && categoryData.description.length > 500) {
      errors.push('Description cannot exceed 500 characters');
    }
    
    // Parent category validation (prevent self-reference)
    if (categoryData.parent && categoryData.pk && categoryData.parent === categoryData.pk) {
      errors.push('Category cannot be its own parent');
    }
    
    return {
      isValid: errors.length === 0,
      errors: errors
    };
  },

  // [AGENT GENERATED CODE - REQUIREMENT: US2] - Bulk Upload Validation
  validateBulkUploadData: (csvData) => {
    const errors = [];
    const warnings = [];
    
    if (!csvData || csvData.length === 0) {
      errors.push('CSV file is empty or invalid');
      return { isValid: false, errors, warnings };
    }
    
    // Check required headers
    const requiredHeaders = ['name'];
    const optionalHeaders = ['description', 'parent', 'is_active'];
    const headers = Object.keys(csvData[0] || {});
    
    const missingHeaders = requiredHeaders.filter(header => !headers.includes(header));
    if (missingHeaders.length > 0) {
      errors.push(`Missing required columns: ${missingHeaders.join(', ')}`);
    }
    
    // Validate each row
    csvData.forEach((row, index) => {
      const rowErrors = [];
      const rowNumber = index + 1;
      
      // Validate name field
      if (!row.name || !row.name.trim()) {
        rowErrors.push(`Row ${rowNumber}: Name is required`);
      } else if (row.name.length > 100) {
        rowErrors.push(`Row ${rowNumber}: Name exceeds 100 characters`);
      }
      
      // Validate description if provided
      if (row.description && row.description.length > 500) {
        rowErrors.push(`Row ${rowNumber}: Description exceeds 500 characters`);
      }
      
      // Validate is_active field if provided
      if (row.is_active && !['true', 'false', '1', '0', 'yes', 'no'].includes(row.is_active.toLowerCase())) {
        rowErrors.push(`Row ${rowNumber}: is_active must be true/false, 1/0, or yes/no`);
      }
      
      if (rowErrors.length > 0) {
        errors.push(...rowErrors);
      }
    });
    
    // Check for duplicate names within the upload
    const names = csvData.map(row => row.name?.trim().toLowerCase()).filter(Boolean);
    const duplicates = names.filter((name, index) => names.indexOf(name) !== index);
    if (duplicates.length > 0) {
      warnings.push(`Duplicate names found in upload: ${[...new Set(duplicates)].join(', ')}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings
    };
  },

  // [AGENT GENERATED CODE - REQUIREMENT: US3] - Line Item Validation
  validateLineItemEdit: (formData, originalData) => {
    const errors = [];
    
    // Quantity validation
    if (!formData.quantity || formData.quantity === '') {
      errors.push('Quantity is required');
    } else if (isNaN(parseFloat(formData.quantity)) || parseFloat(formData.quantity) <= 0) {
      errors.push('Quantity must be a positive number');
    }
    
    // Price validation
    if (!formData.price || formData.price === '') {
      errors.push('Price is required');
    } else if (isNaN(parseFloat(formData.price)) || parseFloat(formData.price) < 0) {
      errors.push('Price must be a non-negative number');
    }
    
    // Large quantity change validation
    if (formData.quantity && originalData.quantity) {
      const quantityChange = Math.abs(
        (parseFloat(formData.quantity) - parseFloat(originalData.quantity)) / parseFloat(originalData.quantity)
      );
      if (quantityChange > 5) { // 500% change
        errors.push('Quantity change exceeds reasonable limits (500%)');
      }
    }
    
    // Large price change validation
    if (formData.price && originalData.price) {
      const priceChange = Math.abs(
        (parseFloat(formData.price) - parseFloat(originalData.price)) / parseFloat(originalData.price)
      );
      if (priceChange > 2) { // 200% change
        errors.push('Price change exceeds reasonable limits (200%)');
      }
    }
    
    // Reference/product code validation
    if (formData.reference && formData.reference.length > 100) {
      errors.push('Reference cannot exceed 100 characters');
    }
    
    // Notes validation
    if (formData.notes && formData.notes.length > 1000) {
      errors.push('Notes cannot exceed 1000 characters');
    }
    
    return {
      isValid: errors.length === 0,
      errors: errors
    };
  },

  // [AGENT GENERATED CODE - REQUIREMENT: US5] - General Form Validation
  validateForm: (formData, validationRules) => {
    const errors = {};
    let isValid = true;
    
    Object.keys(validationRules).forEach(fieldName => {
      const rules = validationRules[fieldName];
      const value = formData[fieldName];
      const fieldErrors = [];
      
      // Required field validation
      if (rules.required && (!value || (typeof value === 'string' && !value.trim()))) {
        fieldErrors.push(`${fieldName} is required`);
      }
      
      // Type-specific validation
      if (value) {
        // Email validation
        if (rules.type === 'email' && !validateEmail(value)) {
          fieldErrors.push(`${fieldName} must be a valid email address`);
        }
        
        // URL validation
        if (rules.type === 'url' && !validateUrl(value)) {
          fieldErrors.push(`${fieldName} must be a valid URL`);
        }
        
        // Numeric validation
        if (rules.type === 'number' && !validateNumeric(value)) {
          fieldErrors.push(`${fieldName} must be a valid number`);
        }
        
        // Decimal validation
        if (rules.type === 'decimal' && !validateDecimal(value)) {
          fieldErrors.push(`${fieldName} must be a valid decimal number`);
        }
        
        // Length validation
        if (rules.minLength && value.length < rules.minLength) {
          fieldErrors.push(`${fieldName} must be at least ${rules.minLength} characters`);
        }
        
        if (rules.maxLength && value.length > rules.maxLength) {
          fieldErrors.push(`${fieldName} cannot exceed ${rules.maxLength} characters`);
        }
        
        // Range validation for numbers
        if (rules.type === 'number' || rules.type === 'decimal') {
          const numValue = parseFloat(value);
          if (rules.min !== undefined && numValue < rules.min) {
            fieldErrors.push(`${fieldName} must be at least ${rules.min}`);
          }
          if (rules.max !== undefined && numValue > rules.max) {
            fieldErrors.push(`${fieldName} cannot exceed ${rules.max}`);
          }
        }
        
        // Custom pattern validation
        if (rules.pattern && !new RegExp(rules.pattern).test(value)) {
          fieldErrors.push(rules.patternMessage || `${fieldName} format is invalid`);
        }
      }
      
      if (fieldErrors.length > 0) {
        errors[fieldName] = fieldErrors;
        isValid = false;
      }
    });
    
    return {
      isValid: isValid,
      errors: errors,
      fieldErrors: Object.values(errors).flat()
    };
  },

  // [AGENT GENERATED CODE - REQUIREMENT: US5] - File Upload Validation
  validateFileUpload: (file, allowedTypes = [], maxSizeBytes = 10 * 1024 * 1024) => {
    const errors = [];
    
    if (!file) {
      errors.push('No file selected');
      return { isValid: false, errors };
    }
    
    // File type validation
    if (allowedTypes.length > 0) {
      const fileExtension = file.name.split('.').pop().toLowerCase();
      if (!allowedTypes.includes(fileExtension)) {
        errors.push(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`);
      }
    }
    
    // File size validation
    if (file.size > maxSizeBytes) {
      const maxSizeMB = (maxSizeBytes / (1024 * 1024)).toFixed(1);
      errors.push(`File size exceeds ${maxSizeMB}MB limit`);
    }
    
    // File name validation
    if (file.name.length > 255) {
      errors.push('File name is too long (max 255 characters)');
    }
    
    return {
      isValid: errors.length === 0,
      errors: errors
    };
  },

  // [AGENT GENERATED CODE - REQUIREMENT: US5] - Data Integrity Helpers
  sanitizeInput: (input, options = {}) => {
    if (typeof input !== 'string') return input;
    
    let sanitized = input.trim();
    
    // Remove dangerous characters if specified
    if (options.removeDangerousChars) {
      sanitized = sanitized.replace(/[<>\"'&]/g, '');
    }
    
    // Limit length if specified
    if (options.maxLength) {
      sanitized = sanitized.substring(0, options.maxLength);
    }
    
    // Convert to proper case if specified
    if (options.toProperCase) {
      sanitized = sanitized.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
    }
    
    return sanitized;
  },

  // Format validation messages for display
  formatValidationErrors: (errors) => {
    if (Array.isArray(errors)) {
      return errors.join('\n');
    } else if (typeof errors === 'object') {
      return Object.values(errors).flat().join('\n');
    }
    return String(errors);
  }
};

export default ValidationUtils;
/* [END AGENT GENERATED CODE] */

/* [AGENT SUMMARY: See requirement IDs US1, US2, US3, US5 for agent run change_impact_analysis_review_final] */