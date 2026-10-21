import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const jobApi = {

    getresume: () => {
        return axios.get(`${API_URL}/resumes`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },
        });
    },

    // Backend: GET /api/resumes/current
    getCurrentResume: () => {
        return axios.get(`${API_URL}/resumes/current`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },
        });
    },

    // Backend: DELETE /api/resumes/{id}/
    deleteResume: (resumeId) => {
        // Django APPEND_SLASH is enabled, so ensure trailing slash.
        return axios.delete(`${API_URL}/resumes/${resumeId}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json',
            },
        });
    },
};


