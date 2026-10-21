/**
 * useTailoring - Custom hook for resume tailoring logic.
 * Manages template state, tailoring operations, ATS analysis, and version management.
 */

import { useState, useCallback, useEffect } from 'react';
import tailoringService from '../services/tailoringService';

const useTailoring = (resumeId = null) => {
  // Template state
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateLoading, setTemplateLoading] = useState(false);

  // Tailoring state
  const [tailoringStatus, setTailoringStatus] = useState('idle'); // idle | tailoring | done | error
  const [tailoredText, setTailoredText] = useState('');
  const [changes, setChanges] = useState({});
  const [keywordsAdded, setKeywordsAdded] = useState([]);
  const [tailorError, setTailorError] = useState(null);

  // ATS state
  const [atsScore, setAtsScore] = useState(null);
  const [atsIssues, setAtsIssues] = useState([]);
  const [atsRecommendations, setAtsRecommendations] = useState([]);
  const [matchedKeywords, setMatchedKeywords] = useState([]);
  const [missingKeywords, setMissingKeywords] = useState([]);
  const [atsLoading, setAtsLoading] = useState(false);

  // Version state
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [versionLoading, setVersionLoading] = useState(false);

  // Comparison state
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparing, setComparing] = useState(false);

  // Polling state
  const [taskId, setTaskId] = useState(null);

  // ============================================================
  // TEMPLATE OPERATIONS
  // ============================================================

  /**
   * Load all available templates
   */
  const loadTemplates = useCallback(async () => {
    setTemplateLoading(true);
    try {
      const response = await tailoringService.getTemplates({ is_active: true });
      setTemplates(response.data || []);
      
      // Auto-select default template
      const defaultTemplate = (response.data || []).find(t => t.is_default);
      if (defaultTemplate) {
        setSelectedTemplate(defaultTemplate);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setTemplateLoading(false);
    }
  }, []);

  /**
   * Select a template to use
   */
  const selectTemplate = useCallback((template) => {
    setSelectedTemplate(template);
  }, []);

  /**
   * Apply a template to the resume
   */
  const applyTemplate = useCallback(async (templateId) => {
    if (!resumeId) return null;
    
    setTemplateLoading(true);
    try {
      const response = await tailoringService.applyTemplate(resumeId, templateId);
      setSelectedTemplate(templates.find(t => t.id === templateId) || null);
      return response;
    } catch (error) {
      console.error('Failed to apply template:', error);
      throw error;
    } finally {
      setTemplateLoading(false);
    }
  }, [resumeId, templates]);

  // ============================================================
  // TAILORING OPERATIONS
  // ============================================================

  /**
   * Start tailoring for a job
   */
  const startTailoring = useCallback(async (jobId, templateId = null) => {
    if (!resumeId || !jobId) return;
    
    setTailoringStatus('tailoring');
    setTailorError(null);
    setAtsScore(null);
    setAtsIssues([]);
    setAtsRecommendations([]);
    
    try {
      const response = await tailoringService.tailorResume(resumeId, jobId, templateId);
      
      if (response.task_id) {
        // Async tailoring - start polling
        setTaskId(response.task_id);
        pollTailorStatus(response.task_id);
      } else {
        // Sync tailoring - use result directly
        setTailoredText(response.tailored_text || '');
        setChanges(response.changes || {});
        setKeywordsAdded(response.keywords_added || []);
        setTailoringStatus('done');
      }
      
      return response;
    } catch (error) {
      setTailorError(error.message || 'Tailoring failed');
      setTailoringStatus('error');
      throw error;
    }
  }, [resumeId]);

  /**
   * Poll for tailoring status (async only)
   */
  const pollTailorStatus = useCallback(async (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await tailoringService.getTailorStatus(taskId);
        
        if (response.status === 'completed' || response.status === 'done') {
          setTailoredText(response.tailored_text || '');
          setChanges(response.changes || {});
          setKeywordsAdded(response.keywords_added || []);
          setTailoringStatus('done');
          clearInterval(pollInterval);
        } else if (response.status === 'failed') {
          setTailorError(response.error || 'Tailoring failed');
          setTailoringStatus('error');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(pollInterval);
      }
    }, 2000);

    // Cleanup polling on unmount
    return () => clearInterval(pollInterval);
  }, []);

  /**
   * Batch tailor for multiple jobs
   */
  const batchTailor = useCallback(async (jobIds) => {
    if (!resumeId || !jobIds.length) return;
    
    setTailoringStatus('tailoring');
    try {
      const response = await tailoringService.batchTailor(resumeId, jobIds);
      setTailoringStatus('done');
      return response;
    } catch (error) {
      setTailorError(error.message || 'Batch tailoring failed');
      setTailoringStatus('error');
      throw error;
    }
  }, [resumeId]);

  /**
   * Reset tailoring state
   */
  const resetTailoring = useCallback(() => {
    setTailoringStatus('idle');
    setTailoredText('');
    setChanges({});
    setKeywordsAdded([]);
    setTailorError(null);
    setAtsScore(null);
    setAtsIssues([]);
    setAtsRecommendations([]);
    setMatchedKeywords([]);
    setMissingKeywords([]);
    setComparisonResult(null);
  }, []);

  // ============================================================
  // ATS OPERATIONS
  // ============================================================

  /**
   * Check ATS compatibility
   */
  const checkATS = useCallback(async (jobDescription) => {
    if (!resumeId || !jobDescription) return;
    
    setAtsLoading(true);
    try {
      const response = await tailoringService.checkATS(resumeId, jobDescription);
      setAtsScore(response.ats_score);
      setAtsIssues(response.issues || []);
      setAtsRecommendations(response.recommendations || []);
      setMatchedKeywords(response.matched_keywords || []);
      setMissingKeywords(response.missing_keywords || []);
      return response;
    } catch (error) {
      console.error('ATS check failed:', error);
      throw error;
    } finally {
      setAtsLoading(false);
    }
  }, [resumeId]);

  /**
   * Optimize resume for ATS
   */
  const optimizeATS = useCallback(async (jobDescription) => {
    if (!resumeId || !jobDescription) return;
    
    setAtsLoading(true);
    try {
      const response = await tailoringService.optimizeATS(resumeId, jobDescription);
      
      if (response.optimized_text) {
        setTailoredText(response.optimized_text);
        setChanges({ optimized: true, improvement: response.improvement });
      }
      
      setAtsScore(response.ats_score);
      setAtsIssues(response.issues || []);
      setAtsRecommendations(response.recommendations || []);
      setMatchedKeywords(response.matched_keywords || []);
      setMissingKeywords(response.missing_keywords || []);
      
      return response;
    } catch (error) {
      console.error('ATS optimization failed:', error);
      throw error;
    } finally {
      setAtsLoading(false);
    }
  }, [resumeId]);

  // ============================================================
  // VERSION OPERATIONS
  // ============================================================

  /**
   * Load all versions
   */
  const loadVersions = useCallback(async () => {
    if (!resumeId) return;
    
    setVersionLoading(true);
    try {
      const response = await tailoringService.getVersions(resumeId);
      setVersions(response.data || []);
      return response;
    } catch (error) {
      console.error('Failed to load versions:', error);
      throw error;
    } finally {
      setVersionLoading(false);
    }
  }, [resumeId]);

  /**
   * Select a version for viewing/comparison
   */
  const selectVersion = useCallback((version) => {
    setSelectedVersion(version);
  }, []);

  /**
   * Compare two versions
   */
  const compareVersions = useCallback(async (versionId1, versionId2) => {
    if (!resumeId) return;
    
    setComparing(true);
    try {
      const response = await tailoringService.compareVersions(resumeId, versionId1, versionId2);
      setComparisonResult(response);
      return response;
    } catch (error) {
      console.error('Version comparison failed:', error);
      throw error;
    } finally {
      setComparing(false);
    }
  }, [resumeId]);

  /**
   * Rollback to a previous version
   */
  const rollbackVersion = useCallback(async (versionId) => {
    if (!resumeId) return;
    
    try {
      const response = await tailoringService.rollbackVersion(resumeId, versionId);
      await loadVersions(); // Reload versions after rollback
      return response;
    } catch (error) {
      console.error('Version rollback failed:', error);
      throw error;
    }
  }, [resumeId, loadVersions]);

  /**
   * Create a new version snapshot
   */
  const createVersion = useCallback(async (name = '', reason = '') => {
    if (!resumeId) return;
    
    try {
      const response = await tailoringService.createVersion(resumeId, name, reason);
      await loadVersions(); // Reload versions after creation
      return response;
    } catch (error) {
      console.error('Version creation failed:', error);
      throw error;
    }
  }, [resumeId, loadVersions]);

  // ============================================================
  // EXPORT OPERATIONS
  // ============================================================

  /**
   * Download resume as PDF
   */
  const downloadPDF = useCallback(async (templateId = null) => {
    if (!resumeId) return;
    
    try {
      const blob = await tailoringService.exportPDF(resumeId, templateId);
      downloadBlob(blob, `resume_v${versions.length + 1 || 1}.pdf`);
      return true;
    } catch (error) {
      console.error('PDF download failed:', error);
      throw error;
    }
  }, [resumeId, versions]);

  /**
   * Download resume as DOCX
   */
  const downloadDOCX = useCallback(async (templateId = null) => {
    if (!resumeId) return;
    
    try {
      const blob = await tailoringService.exportDOCX(resumeId, templateId);
      downloadBlob(blob, `resume_v${versions.length + 1 || 1}.docx`);
      return true;
    } catch (error) {
      console.error('DOCX download failed:', error);
      throw error;
    }
  }, [resumeId, versions]);

  /**
   * Download resume as TXT
   */
  const downloadTXT = useCallback(async () => {
    if (!resumeId) return;
    
    try {
      const blob = await tailoringService.exportTXT(resumeId);
      downloadBlob(blob, `resume_v${versions.length + 1 || 1}.txt`);
      return true;
    } catch (error) {
      console.error('TXT download failed:', error);
      throw error;
    }
  }, [resumeId, versions]);

  // ============================================================
  // HELPER
  // ============================================================

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // ============================================================
  // INITIALIZATION
  // ============================================================

  useEffect(() => {
    loadTemplates();
    if (resumeId) {
      loadVersions();
    }
  }, [resumeId, loadTemplates, loadVersions]);

  return {
    // Template
    templates,
    selectedTemplate,
    templateLoading,
    selectTemplate,
    applyTemplate,

    // Tailoring
    tailoringStatus,
    tailoredText,
    changes,
    keywordsAdded,
    tailorError,
    startTailoring,
    batchTailor,
    resetTailoring,

    // ATS
    atsScore,
    atsIssues,
    atsRecommendations,
    matchedKeywords,
    missingKeywords,
    atsLoading,
    checkATS,
    optimizeATS,

    // Version
    versions,
    selectedVersion,
    versionLoading,
    selectVersion,
    loadVersions,
    compareVersions,
    comparisonResult,
    comparing,
    rollbackVersion,
    createVersion,

    // Export
    downloadPDF,
    downloadDOCX,
    downloadTXT,
  };
};

export default useTailoring;

