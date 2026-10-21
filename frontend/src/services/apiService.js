import axios from "axios";

const API_URL = 'http://localhost:8000/api';

// Centralized job API wrapper for the dedicated job detail page
const apiService = {
  // Fetch single job detail
  // Note: expects backend endpoint /api/jobs/<id>/
  getJobById: (jobId) => {
    return axios.get(`${API_URL}/jobs/${jobId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
  },

  saveJob: (jobId) => {
    return axios.post(`${API_URL}/jobs/${jobId}/save_job/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
  },

  unsaveJob: (jobId) => {
    return axios.post(`${API_URL}/jobs/${jobId}/unsave_job/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
  },

  applyToJob: (jobId, resumeId = null) => {
    return axios.post(`${API_URL}/jobs/apply/`, {
      job_id: jobId,
      resume_id: resumeId,
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
  },
};

export default apiService;

