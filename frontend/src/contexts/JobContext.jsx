import React, { createContext, useContext, useState, useCallback } from 'react';
import api from '../services/api';

const JobContext = createContext();

export const useJobs = () => {
  const context = useContext(JobContext);
  if (!context) {
    throw new Error('useJobs must be used within a JobProvider');
  }
  return context;
};

export const JobProvider = ({ children }) => {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchJobs = useCallback(async (filters = {}) => {
    try {
      setLoading(true);
      // Simulate API call
      const response = await api.get('/jobs', { params: filters });
      setJobs(response.data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchApplications = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/applications');
      setApplications(response.data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch applications');
    } finally {
      setLoading(false);
    }
  }, []);

  const applyToJob = useCallback(async (jobId, resumeData) => {
    try {
      setLoading(true);
      const response = await api.post(`/jobs/${jobId}/apply`, resumeData);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to apply');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateApplicationStatus = useCallback(async (applicationId, status) => {
    try {
      setLoading(true);
      const response = await api.patch(`/applications/${applicationId}`, { status });
      setApplications(prev => 
        prev.map(app => app.id === applicationId ? response.data : app)
      );
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to update status');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const value = {
    jobs,
    applications,
    loading,
    error,
    fetchJobs,
    fetchApplications,
    applyToJob,
    updateApplicationStatus,
  };

  return (
    <JobContext.Provider value={value}>
      {children}
    </JobContext.Provider>
  );
};

export default JobContext;