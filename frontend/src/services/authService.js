import api from './api';
import axios from 'axios';

class AuthService {
  async login(email, password) {
    try {
      const response = await api.post('/auth/login/', { email, password });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  async register(userData) {
    try {
      const response = await api.post('/auth/register/', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  async logout() {
    const refresh = localStorage.getItem('refresh_token');

    try {
      // Backend only needs refresh to blacklist.
      // Don't hard-fail logout if refresh is missing/invalid.
      return await api.post('/users/logout/', { refresh });
    } catch (error) {
      console.error('Logout error:', error);
      return null;
    }
  }



  async resetPassword(email) {
    try {
      const response = await api.post('/users/password-reset/', { email });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Password reset failed');
    }
  }

  async getCurrentUser() {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get user');
    }
  }
}

export default new AuthService();