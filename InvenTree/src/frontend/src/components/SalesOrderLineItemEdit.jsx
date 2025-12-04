/* [AGENT GENERATED CODE - REQUIREMENT: US3] */
/**
 * SalesOrderLineItemEdit Component
 * 
 * Provides UI for editing individual line items in sales orders including:
 * - Quantity, price, and product code editing
 * - Validation and inventory checks
 * - Approval workflow integration
 * - Permission-based access control
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableRow,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Schedule as PendingIcon
} from '@mui/icons-material';

import { api } from '../functions/api';
import { PermissionCheck } from './PermissionCheck';
import { ValidationUtils } from './ValidationUtils';

/* [AGENT GENERATED CODE - REQUIREMENT: US3, US5, US6] */
const SalesOrderLineItemEdit = ({ lineItem, salesOrder, onUpdate, onClose }) => {
  const [formData, setFormData] = useState({
    quantity: '',
    price: '',
    sale_price: '',
    reference: '',
    notes: ''
  });
  const [originalData, setOriginalData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [approvalRequired, setApprovalRequired] = useState(false);
  const [validation, setValidation] = useState({ isValid: true, errors: [] });
  const [inventoryCheck, setInventoryCheck] = useState(null);

  // Initialize form data
  useEffect(() => {
    if (lineItem) {
      const data = {
        quantity: lineItem.quantity || '',
        price: lineItem.price || '',
        sale_price: lineItem.sale_price || '',
        reference: lineItem.reference || '',
        notes: lineItem.notes || ''
      };
      setFormData(data);
      setOriginalData(data);
    }
  }, [lineItem]);

  // [AGENT GENERATED CODE - REQUIREMENT: US3] - Real-time validation
  useEffect(() => {
    validateLineItemChanges();
  }, [formData]);

  const validateLineItemChanges = async () => {
    if (!lineItem) return;

    try {
      // Client-side validation
      const clientValidation = ValidationUtils.validateLineItemEdit(formData, originalData);
      setValidation(clientValidation);

      if (!clientValidation.isValid) {
        return;
      }

      // Check if changes require approval
      const requiresApproval = checkIfApprovalRequired();
      setApprovalRequired(requiresApproval);

      // Perform inventory availability check if quantity changed
      if (formData.quantity !== originalData.quantity) {
        await checkInventoryAvailability();
      }

    } catch (err) {
      setError('Validation error: ' + err.message);
    }
  };

  const checkIfApprovalRequired = () => {
    // [AGENT GENERATED CODE - REQUIREMENT: US3] - Approval logic
    const quantityChanged = parseFloat(formData.quantity) !== parseFloat(originalData.quantity);
    const priceChanged = parseFloat(formData.price) !== parseFloat(originalData.price);
    
    // Require approval for significant changes
    const quantityChangePercent = Math.abs(
      (parseFloat(formData.quantity) - parseFloat(originalData.quantity)) / parseFloat(originalData.quantity) * 100
    );
    
    const priceChangePercent = Math.abs(
      (parseFloat(formData.price) - parseFloat(originalData.price)) / parseFloat(originalData.price) * 100
    );

    return (
      (quantityChanged && quantityChangePercent > 10) || 
      (priceChanged && priceChangePercent > 5) ||
      parseFloat(formData.quantity) > parseFloat(originalData.quantity) * 2
    );
  };

  const checkInventoryAvailability = async () => {
    try {
      const response = await api.get(`/stock/`, {
        params: {
          part: lineItem.part,
          available: true,
          location_detail: true
        }
      });
      
      const totalAvailable = response.data.results.reduce(
        (sum, item) => sum + parseFloat(item.quantity), 0
      );
      
      const requestedQuantity = parseFloat(formData.quantity);
      
      setInventoryCheck({
        available: totalAvailable,
        requested: requestedQuantity,
        sufficient: totalAvailable >= requestedQuantity
      });

      // Add warnings for inventory issues
      const newWarnings = [];
      if (totalAvailable < requestedQuantity) {
        newWarnings.push(
          `Insufficient inventory: ${totalAvailable} available, ${requestedQuantity} requested`
        );
      }
      setWarnings(newWarnings);

    } catch (err) {
      setError('Failed to check inventory: ' + err.message);
    }
  };

  // [AGENT GENERATED CODE - REQUIREMENT: US3, US5] - Save line item changes
  const handleSaveChanges = async () => {
    try {
      setLoading(true);
      setError(null);

      // Final validation
      if (!validation.isValid) {
        setError('Please fix validation errors before saving');
        return;
      }

      // Check if user can edit this line item
      const canEditResponse = await api.get(`/order/so-line/${lineItem.pk}/can-edit/`);
      if (!canEditResponse.data.can_edit) {
        setError('Cannot edit line item: ' + canEditResponse.data.reason);
        return;
      }

      const updateData = {
        ...formData,
        requires_approval: approvalRequired
      };

      const response = await api.patch(`/order/so-line/${lineItem.pk}/`, updateData);
      
      if (response.data.approval_status) {
        // Show approval status message
        const status = response.data.approval_status;
        if (status === 'pending') {
          setError(null);
          // Show success message for pending approval
        } else if (status === 'approved') {
          onUpdate(response.data);
          onClose();
        }
      } else {
        // Direct update without approval
        onUpdate(response.data);
        onClose();
      }

    } catch (err) {
      setError('Failed to update line item: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    return Object.keys(formData).some(
      key => formData[key] !== originalData[key]
    );
  };

  if (!lineItem) {
    return (
      <Box p={3}>
        <Typography>No line item selected</Typography>
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Edit Line Item - {lineItem.part_detail?.name}
          </Typography>
          <Box>
            {approvalRequired && (
              <Chip
                icon={<PendingIcon />}
                label="Approval Required"
                color="warning"
                size="small"
                sx={{ mr: 1 }}
              />
            )}
            <Chip
              label={salesOrder.status_text}
              color={salesOrder.status === 10 ? 'success' : 'default'}
              size="small"
            />
          </Box>
        </Box>

        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {warnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {warnings.map((warning, index) => (
              <Typography key={index} variant="body2">
                {warning}
              </Typography>
            ))}
          </Alert>
        )}

        {!validation.isValid && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">Validation Errors:</Typography>
            {validation.errors.map((error, index) => (
              <Typography key={index} variant="body2">• {error}</Typography>
            ))}
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Current vs New Comparison */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              Current Values
            </Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Quantity</TableCell>
                  <TableCell>{originalData.quantity}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Price</TableCell>
                  <TableCell>{originalData.price}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Reference</TableCell>
                  <TableCell>{originalData.reference || '-'}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              New Values
            </Typography>
            <Box>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                margin="normal"
                size="small"
                inputProps={{ min: 0, step: 0.01 }}
                error={validation.errors.some(e => e.includes('quantity'))}
              />

              <TextField
                fullWidth
                label="Unit Price"
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                margin="normal"
                size="small"
                inputProps={{ min: 0, step: 0.01 }}
                error={validation.errors.some(e => e.includes('price'))}
              />

              <TextField
                fullWidth
                label="Reference/Product Code"
                value={formData.reference}
                onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                margin="normal"
                size="small"
              />

              <TextField
                fullWidth
                label="Notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                margin="normal"
                size="small"
                multiline
                rows={2}
              />
            </Box>
          </Grid>
        </Grid>

        {/* Inventory Information */}
        {inventoryCheck && (
          <Box mt={2}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Inventory Status
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="body2">Available: {inventoryCheck.available}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2">Requested: {inventoryCheck.requested}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Chip
                  icon={inventoryCheck.sufficient ? <CheckIcon /> : <WarningIcon />}
                  label={inventoryCheck.sufficient ? 'Sufficient' : 'Insufficient'}
                  color={inventoryCheck.sufficient ? 'success' : 'error'}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Action Buttons */}
        <Box display="flex" justifyContent="flex-end" gap={2} mt={3}>
          <Button
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          
          <PermissionCheck permission="order.change">
            <Button
              variant="contained"
              onClick={handleSaveChanges}
              disabled={loading || !hasChanges() || !validation.isValid}
              startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
            >
              {approvalRequired ? 'Submit for Approval' : 'Save Changes'}
            </Button>
          </PermissionCheck>
        </Box>

        {/* Change Summary */}
        {hasChanges() && (
          <Box mt={2}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Change Summary
            </Typography>
            {Object.keys(formData).map(key => {
              if (formData[key] !== originalData[key]) {
                return (
                  <Typography key={key} variant="body2">
                    {key}: {originalData[key]} → {formData[key]}
                  </Typography>
                );
              }
              return null;
            })}
            
            {approvalRequired && (
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="body2">
                  These changes require approval before they take effect.
                </Typography>
              </Alert>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default SalesOrderLineItemEdit;
/* [END AGENT GENERATED CODE] */

/* [AGENT SUMMARY: See requirement IDs US3, US5, US6 for agent run change_impact_analysis_review_final] */