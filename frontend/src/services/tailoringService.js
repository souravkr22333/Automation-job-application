/**
 * Tailoring Service - API calls for template management, resume tailoring,
 * ATS optimization, and version management.
 */

import api from './api';

const BASE_URL = '/resumes';

const tailoringService = {

    // TEMPLATE MANAGEMENT
  

  
   // Get all available resume templates
   
  getTemplates: async (params = {}) => {
    try {
      const response = await api.get(`${BASE_URL}/templates/`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching templates:', error);
      throw error.response?.data || error;
    }
  },

  
   //Get a specific template by ID
   
  getTemplate: async (templateId) => {
    try {
      const response = await api.get(`${BASE_URL}/templates/${templateId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Create a new template
   */
  createTemplate: async (templateData) => {
    try {
      const response = await api.post(`${BASE_URL}/templates/`, templateData);
      return response.data;
    } catch (error) {
      console.error('Error creating template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Update an existing template
   */
  updateTemplate: async (templateId, templateData) => {
    try {
      const response = await api.put(`${BASE_URL}/templates/${templateId}/`, templateData);
      return response.data;
    } catch (error) {
      console.error('Error updating template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Delete a template
   */
  deleteTemplate: async (templateId) => {
    try {
      const response = await api.delete(`${BASE_URL}/templates/${templateId}/`);
      return response.data;
    } catch (error) {
      console.error('Error deleting template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Apply a template to a resume
   */
  applyTemplate: async (resumeId, templateId) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/apply-template/`, {
        template_id: templateId
      });
      return response.data;
    } catch (error) {
      console.error('Error applying template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Get default template
   */
  getDefaultTemplate: async () => {
    try {
      const response = await api.get(`${BASE_URL}/templates/default/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching default template:', error);
      throw error.response?.data || error;
    }
  },

  // ============================================================
  // RESUME TAILORING
  // ============================================================

  /**
   * Tailor a resume for a specific job
   */
  tailorResume: async (resumeId, jobId, templateId = null) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/tailor/`, {
        job_id: jobId,
        template_id: templateId
      });
      return response.data;
    } catch (error) {
      console.error('Error tailoring resume:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Get tailoring status
   */
  getTailorStatus: async (taskId) => {
    try {
      const response = await api.get(`${BASE_URL}/tailor-status/${taskId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching tailor status:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Auto-tailor for multiple jobs
   */
  batchTailor: async (resumeId, jobIds) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/batch-tailor/`, {
        job_ids: jobIds
      });
      return response.data;
    } catch (error) {
      console.error('Error in batch tailoring:', error);
      throw error.response?.data || error;
    }
  },

  // ============================================================
  // ATS OPTIMIZATION
  // ============================================================

  /**
   * Check ATS compatibility of a resume against a job description
   */
  checkATS: async (resumeId, jobDescription) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/ats-check/`, {
        job_description: jobDescription
      });
      return response.data;
    } catch (error) {
      console.error('Error checking ATS:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Optimize resume for ATS
   */
  optimizeATS: async (resumeId, jobDescription) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/ats-optimize/`, {
        job_description: jobDescription
      });
      return response.data;
    } catch (error) {
      console.error('Error optimizing ATS:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Get improvement suggestions for ATS
   */
  getATSSuggestions: async (resumeId, jobDescription) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/ats-suggestions/`, {
        job_description: jobDescription
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching ATS suggestions:', error);
      throw error.response?.data || error;
    }
  },

  // ============================================================
  // VERSION MANAGEMENT
  // ============================================================

  /**
   * Get all versions of a resume
   */
  getVersions: async (resumeId) => {
    try {
      const response = await api.get(`${BASE_URL}/${resumeId}/versions/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching versions:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Get a specific version
   */
  getVersion: async (resumeId, versionId) => {
    try {
      const response = await api.get(`${BASE_URL}/${resumeId}/versions/${versionId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching version:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Compare two versions
   */
  compareVersions: async (resumeId, versionId1, versionId2) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/compare-versions/`, {
        version_id_1: versionId1,
        version_id_2: versionId2
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing versions:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Rollback to a previous version
   */
  rollbackVersion: async (resumeId, versionId) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/rollback/`, {
        version_id: versionId
      });
      return response.data;
    } catch (error) {
      console.error('Error rolling back version:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Create a new version snapshot
   */
  createVersion: async (resumeId, versionName = '', changeReason = '') => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/create-version/`, {
        version_name: versionName,
        change_reason: changeReason
      });
      return response.data;
    } catch (error) {
      console.error('Error creating version:', error);
      throw error.response?.data || error;
    }
  },

  // ============================================================
  // EXPORT
  // ============================================================

  /**
   * Export resume as PDF
   */
  exportPDF: async (resumeId, templateId = null) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/export-pdf/`, {
        template_id: templateId
      }, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting PDF:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Export resume as DOCX
   */
  exportDOCX: async (resumeId, templateId = null) => {
    try {
      const response = await api.post(`${BASE_URL}/${resumeId}/export-docx/`, {
        template_id: templateId
      }, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting DOCX:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Export resume as plain text
   */
  exportTXT: async (resumeId) => {
    try {
      const response = await api.get(`${BASE_URL}/${resumeId}/export-txt/`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting TXT:', error);
      throw error.response?.data || error;
    }
  }
};

export default tailoringService;