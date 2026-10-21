// frontend/src/services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const jobApi = {
  // Get all jobs
  getAll: (params = {}) => {
    return axios.get(`${API_URL}/jobs/`, { params, 
      headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          }
    });
  },

 

  // Get saved jobs
  getSaved: (params = {}) => {
    return axios.get(`${API_URL}/jobs/saved/`, { params,
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          }
     });
  },

  // Get applied jobs
  getApplied: (params = {}) => {
    return axios.get(`${API_URL}/jobs/applied/`, { params ,
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          }
    });
  },

  // Get matched jobs
  getMatched: (params = {}) => {
    return axios.get(`${API_URL}/jobs/matched/`, { params ,
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          }
    });
  },

  // Get job statistics
  getStats: () => {
    return axios.get(`${API_URL}/jobs/stats/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Auto discover (triggered on login / website open / every visit)
  autoDiscover: () => {
    return axios.post(`${API_URL}/jobs/auto_discover/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Discover jobs
  discover: (data) => {
    return axios.post(`${API_URL}/jobs/discover/`, data, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Apply to job
  apply: (jobId, resumeId = null) => {
    return axios.post(`${API_URL}/jobs/apply/`, {
      job_id: jobId,
      resume_id: resumeId
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Save job
  save: (jobId) => {
    return axios.post(`${API_URL}/jobs/${jobId}/save_job/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Unsave job
  unsave: (jobId) => {
    return axios.post(`${API_URL}/jobs/${jobId}/unsave_job/`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,  
        'Content-Type': 'application/json', 
        }
    });

    
  },

  // Bulk apply
  bulkApply: (jobIds, resumeId = null) => {
    return axios.post(`${API_URL}/jobs/bulk_apply/`, {
      job_ids: jobIds,
      resume_id: resumeId
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Auto apply - generate tailored resume and submit using Playwright
  autoApplyQueue: (jobIds, resumeId = null) => {
    return axios.post(`${API_URL}/applications/queue/auto_apply/`, {
      job_ids: jobIds,
      resume_id: resumeId
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Auto Generate - Tailor resumes for all jobs in queue and mark as pending
  autoGenerateQueue: (jobIds, resumeId = null) => {
    return axios.post(`${API_URL}/applications/queue/auto_generate/`, {
      job_ids: jobIds,
      resume_id: resumeId
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  },

  // Get queue status
  getQueueStatus: () => {
    return axios.get(`${API_URL}/applications/queue/status/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      }
    });
  }
};

export default jobApi;
