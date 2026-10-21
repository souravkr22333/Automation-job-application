// frontend/src/services/profileService.js
import api from '../lib/api';
import axios from 'axios'

// ============================================================
// PROFILE SERVICES
// ============================================================

export const profileService = {
  // Get complete profile
  getCompleteProfile: async () => {
    const response = await axios.get('http://localhost:8000/api/users/profile/complete/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        }
    );
    console.log(response.data)
    return response.data;
  },

  // Update profile
  updateProfile: async (data) => {
    const response = await axios.put('http://localhost:8000/api/users/profile/', data,{
       headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },
    });
    return response.data;
  },

  // Update preferences
  updatePreferences: async (data) => {
    const response = await axios.put('http://localhost:8000/api/users/preferences/', data,{
       headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },
    });
    return response.data;
  },

  // Skills
  getSkills: async () => {
    const response = await axios.get('http://localhost:8000/api/users/skills/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  addSkills: async (skills) => {
    const response = await axios.post('http://localhost:8000/api/users/skills/', { skills },{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  removeSkills: async (skills) => {
    const response = await axios.delete('http://localhost:8000/api/users/skills/', { data: { skills } },{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // Preferred Jobs
  getPreferredJobs: async () => {
    const response = await axios.get('http://localhost:8000/api/users/preferred-jobs/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  addPreferredJobs: async (jobs) => {
    const response = await axios.post('http://localhost:8000/api/users/preferred-jobs/', { jobs },{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // Preferred Locations
  getPreferredLocations: async () => {
    const response = await axios.get('http://localhost:8000/api/users/preferred-locations/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  addPreferredLocations: async (locations) => {
    const response = await axios.post('http://localhost:8000/api/users/preferred-locations/', { locations },{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // ============================================================
  // EDUCATION SERVICES
  // ============================================================
  
  getEducations: async () => {
    const response = await axios.get('http://localhost:8000/api/users/educations/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  createEducation: async (data) => {
    const response = await axios.post('http://localhost:8000/api/users/educations/', data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  updateEducation: async (id, data) => {
    const response = await axios.put(`http://localhost:8000/api/users/educations/${id}/`, data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  deleteEducation: async (id) => {
    const response = await axios.delete(`http://localhost:8000/api/users/educations/${id}/`,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // ============================================================
  // EXPERIENCE SERVICES
  // ============================================================
  
  getExperiences: async () => {
    const response = await axios.get('http://localhost:8000/api/users/experiences/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  createExperience: async (data) => {
    const response = await axios.post('http://localhost:8000/api/users/experiences/', data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  updateExperience: async (id, data) => {
    const response = await axios.put(`http://localhost:8000/api/users/experiences/${id}/`, data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  deleteExperience: async (id) => {
    const response = await axios.delete(`http://localhost:8000/api/users/experiences/${id}/`,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // ============================================================
  // PROJECT SERVICES
  // ============================================================
  
  getProjects: async () => {
    const response = await axios.get('http://localhost:8000/api/users/projects/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  createProject: async (data) => {
    const response = await axios.post('http://localhost:8000/api/users/projects/', data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  updateProject: async (id, data) => {
    const response = await axios.put(`http://localhost:8000/api/users/projects/${id}/`, data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  deleteProject: async (id) => {
    const response = await axios.delete(`http://localhost:8000/api/users/projects/${id}/`,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // ============================================================
  // CERTIFICATION SERVICES
  // ============================================================
  
  getCertifications: async () => {
    const response = await axios.get('http://localhost:8000/api/users/certifications/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  createCertification: async (data) => {
    const response = await axios.post('http://localhost:8000/api/users/certifications/', data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  updateCertification: async (id, data) => {
    const response = await axios.put(`http://localhost:8000/api/users/certifications/${id}/`, data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  deleteCertification: async (id) => {
    const response = await axios.delete(`http://localhost:8000/api/users/certifications/${id}/`,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  // ============================================================
  // LANGUAGE SERVICES
  // ============================================================
  
  getLanguages: async () => {
    const response = await axios.get('http://localhost:8000/api/users/languages/',{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  createLanguage: async (data) => {
    const response = await axios.post('http://localhost:8000/api/users/languages/', data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  updateLanguage: async (id, data) => {
    const response = await axios.put(`http://localhost:8000/api/users/languages/${id}/`, data,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },

  deleteLanguage: async (id) => {
    const response = await axios.delete(`http://localhost:8000/api/users/languages/${id}/`,{
        headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },

        });
    return response.data;
  },
};