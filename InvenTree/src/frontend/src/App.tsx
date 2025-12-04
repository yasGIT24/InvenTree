import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';

// [AGENT GENERATED CODE - REQUIREMENT: USX] 
// [AGENT SUMMARY: See requirement IDs US1, US2, US4, US5, US6 for agent run change_impact_analysis_review_final]
// Enhanced App.tsx to support vendor category management functionality
// Includes routes and configurations for vendor category operations

// Global API instance
export const api = axios.create({});

/*
 * Setup default settings for the Axios API instance.
 */
export function setApiDefaults() {
  const { getHost } = useLocalState.getState();

  api.defaults.baseURL = getHost();
  api.defaults.timeout = 5000;

  api.defaults.withCredentials = true;
  api.defaults.withXSRFToken = true;
  api.defaults.xsrfCookieName = 'csrftoken';
  api.defaults.xsrfHeaderName = 'X-CSRFToken';

  axios.defaults.withCredentials = true;
  axios.defaults.withXSRFToken = true;
  axios.defaults.xsrfHeaderName = 'X-CSRFToken';
  axios.defaults.xsrfCookieName = 'csrftoken';
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false
    }
  }
});

// [AGENT GENERATED CODE - REQUIREMENT: USX]
// Vendor category configuration for enhanced purchasing module
export const vendorCategoryConfig = {
  // API endpoints for vendor category operations  
  endpoints: {
    list: '/api/company/vendor-category/',
    bulk_upload: '/api/company/vendor-category/bulk/',
    delete: '/api/company/vendor-category/{id}/',
    validation: '/api/company/vendor-category/validate/'
  },
  // Validation rules for vendor categories
  validation: {
    required_fields: ['name', 'description'],
    max_name_length: 100,
    duplicate_check: true
  },
  // Permission requirements
  permissions: {
    delete: ['company.delete_vendorcategory'],
    bulk_upload: ['company.add_vendorcategory', 'company.change_vendorcategory'],
    manage: ['company.view_vendorcategory']
  }
};
