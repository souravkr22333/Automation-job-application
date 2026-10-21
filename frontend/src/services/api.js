import axios from 'axios';

const api = axios.create({
  // In Vite, use import.meta.env instead of process.env
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  
  headers: {
    'Content-Type': 'application/json',
  },
});


// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Prefer app-issued access token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle 401 Unauthorized
      if (error.response.status === 401) {
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      
      // Handle rate limiting
      if (error.response.status === 429) {
        console.error('Too many requests, please try again later');
      }
    }
    return Promise.reject(error);
  }
);




export default api;