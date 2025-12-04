/* [AGENT GENERATED CODE - REQUIREMENT: US1, US2] */
/**
 * VendorCategoryList Component
 * 
 * Provides UI for managing vendor categories including:
 * - List view of all vendor categories
 * - Create new categories
 * - Edit existing categories  
 * - Delete categories with validation
 * - Bulk upload categories from CSV
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
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  Tooltip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';

import { api } from '../functions/api';
import { PermissionCheck } from './PermissionCheck';
import { ValidationUtils } from './ValidationUtils';

/* [AGENT GENERATED CODE - REQUIREMENT: US1, US2, US5, US6] */
const VendorCategoryList = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editDialog, setEditDialog] = useState({ open: false, category: null });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, category: null });
  const [uploadDialog, setUploadDialog] = useState({ open: false });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadErrors, setUploadErrors] = useState([]);

  // Load vendor categories on component mount
  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const response = await api.get('/company/category/');
      setCategories(response.data.results || []);
      setError(null);
    } catch (err) {
      setError('Failed to load vendor categories: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // [AGENT GENERATED CODE - REQUIREMENT: US1] - Delete category with validation
  const handleDeleteCategory = async (category) => {
    try {
      // Check if category can be deleted
      const canDelete = category.can_delete?.can_delete;
      const reason = category.can_delete?.reason;
      
      if (!canDelete) {
        setError(`Cannot delete category: ${reason}`);
        return;
      }

      await api.delete(`/company/category/${category.pk}/`);
      await loadCategories();
      setDeleteDialog({ open: false, category: null });
    } catch (err) {
      setError('Failed to delete category: ' + err.message);
    }
  };

  // [AGENT GENERATED CODE - REQUIREMENT: US2] - Save category (create/update)
  const handleSaveCategory = async (categoryData) => {
    try {
      // Validate category data
      const validationResult = ValidationUtils.validateVendorCategory(categoryData);
      if (!validationResult.isValid) {
        setError(validationResult.errors.join(', '));
        return;
      }

      if (editDialog.category) {
        // Update existing category
        await api.patch(`/company/category/${editDialog.category.pk}/`, categoryData);
      } else {
        // Create new category
        await api.post('/company/category/', categoryData);
      }
      
      await loadCategories();
      setEditDialog({ open: false, category: null });
    } catch (err) {
      setError('Failed to save category: ' + err.message);
    }
  };

  // [AGENT GENERATED CODE - REQUIREMENT: US2] - Bulk upload CSV
  const handleBulkUpload = async (file) => {
    try {
      setUploadProgress(0);
      setUploadErrors([]);
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('model_type', 'vendor_category');
      
      const response = await api.post('/importer/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      if (response.data.errors && response.data.errors.length > 0) {
        setUploadErrors(response.data.errors);
      } else {
        await loadCategories();
        setUploadDialog({ open: false });
      }
    } catch (err) {
      setError('Failed to upload categories: ' + err.message);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Vendor Categories
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Actions Bar */}
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Box>
          <PermissionCheck permission="company.add">
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setEditDialog({ open: true, category: null })}
            >
              Add Category
            </Button>
          </PermissionCheck>
        </Box>
        
        <Box>
          <PermissionCheck permission="company.add">
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={() => setUploadDialog({ open: true })}
              sx={{ mr: 1 }}
            >
              Bulk Upload
            </Button>
          </PermissionCheck>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => window.open('/company/category/?export=csv')}
          >
            Export CSV
          </Button>
        </Box>
      </Box>

      {/* Categories Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Parent Category</TableCell>
              <TableCell>Companies</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {categories.map((category) => (
              <TableRow key={category.pk}>
                <TableCell>
                  <Typography variant="subtitle2">
                    {category.full_name}
                  </Typography>
                </TableCell>
                <TableCell>{category.description || '-'}</TableCell>
                <TableCell>{category.parent?.name || '-'}</TableCell>
                <TableCell>
                  <Chip 
                    label={category.company_count || 0} 
                    size="small" 
                    color="info"
                  />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={category.is_active ? 'Active' : 'Inactive'}
                    color={category.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <PermissionCheck permission="company.view">
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                  </PermissionCheck>
                  
                  <PermissionCheck permission="company.change">
                    <Tooltip title="Edit Category">
                      <IconButton 
                        size="small"
                        onClick={() => setEditDialog({ open: true, category })}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </PermissionCheck>
                  
                  <PermissionCheck permission="company.delete">
                    <Tooltip 
                      title={
                        category.can_delete?.can_delete 
                          ? "Delete Category" 
                          : category.can_delete?.reason
                      }
                    >
                      <span>
                        <IconButton 
                          size="small"
                          onClick={() => setDeleteDialog({ open: true, category })}
                          disabled={!category.can_delete?.can_delete}
                          color={category.can_delete?.can_delete ? "error" : "default"}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </PermissionCheck>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit/Create Dialog */}
      <CategoryEditDialog
        open={editDialog.open}
        category={editDialog.category}
        categories={categories}
        onClose={() => setEditDialog({ open: false, category: null })}
        onSave={handleSaveCategory}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, category: null })}>
        <DialogTitle>Delete Vendor Category</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{deleteDialog.category?.name}"?
          </Typography>
          {deleteDialog.category?.company_count > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              This category is used by {deleteDialog.category.company_count} companies.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, category: null })}>
            Cancel
          </Button>
          <Button 
            onClick={() => handleDeleteCategory(deleteDialog.category)}
            color="error"
            disabled={!deleteDialog.category?.can_delete?.can_delete}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Upload Dialog */}
      <BulkUploadDialog
        open={uploadDialog.open}
        progress={uploadProgress}
        errors={uploadErrors}
        onClose={() => setUploadDialog({ open: false })}
        onUpload={handleBulkUpload}
      />
    </Box>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US1, US2, US5] - Category Edit Dialog
const CategoryEditDialog = ({ open, category, categories, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent: '',
    is_active: true
  });

  useEffect(() => {
    if (category) {
      setFormData({
        name: category.name || '',
        description: category.description || '',
        parent: category.parent?.pk || '',
        is_active: category.is_active !== false
      });
    } else {
      setFormData({
        name: '',
        description: '',
        parent: '',
        is_active: true
      });
    }
  }, [category]);

  const handleSubmit = () => {
    const submitData = { ...formData };
    if (!submitData.parent) {
      delete submitData.parent;
    }
    onSave(submitData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {category ? 'Edit Vendor Category' : 'Create Vendor Category'}
      </DialogTitle>
      <DialogContent>
        <Box pt={1}>
          <TextField
            fullWidth
            label="Category Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            margin="normal"
            required
          />
          
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Parent Category</InputLabel>
            <Select
              value={formData.parent}
              onChange={(e) => setFormData({ ...formData, parent: e.target.value })}
            >
              <MenuItem value="">None</MenuItem>
              {categories
                .filter(cat => cat.pk !== category?.pk)
                .map(cat => (
                  <MenuItem key={cat.pk} value={cat.pk}>
                    {cat.full_name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          {category ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// [AGENT GENERATED CODE - REQUIREMENT: US2] - Bulk Upload Dialog
const BulkUploadDialog = ({ open, progress, errors, onClose, onUpload }) => {
  const [file, setFile] = useState(null);

  const handleFileSelect = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = () => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Bulk Upload Vendor Categories</DialogTitle>
      <DialogContent>
        <Box pt={1}>
          <Typography variant="body2" gutterBottom>
            Upload a CSV file with columns: name, description, parent, is_active
          </Typography>
          
          <input
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            style={{ margin: '16px 0' }}
          />
          
          {progress > 0 && (
            <Box mt={2}>
              <Typography variant="body2">Upload Progress: {progress}%</Typography>
              <CircularProgress variant="determinate" value={progress} />
            </Box>
          )}
          
          {errors.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" color="error">
                Upload Errors:
              </Typography>
              {errors.map((error, index) => (
                <Alert key={index} severity="error" sx={{ mt: 1 }}>
                  {error}
                </Alert>
              ))}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleUpload}
          variant="contained"
          disabled={!file || progress > 0}
        >
          Upload
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default VendorCategoryList;
/* [END AGENT GENERATED CODE] */

/* [AGENT SUMMARY: See requirement IDs US1, US2, US5, US6 for agent run change_impact_analysis_review_final] */