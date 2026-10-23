import axios from 'axios';
const API_URL = 'https://automation-job-application-production.up.railway.app';
// API_URL = 'http://localhost:8000';


class AuthService {
  // ==========================
  // LOGIN
  // ==========================
  async login(email, password) {
    try {
      const response = await axios.post(
        `${API_URL}/api/auth/login/`,
        { email, password },
        { headers: { 'Content-Type': 'application/json' } }
      );
      return response.data;
    } catch (error) {
      throw new Error(extractError(error, 'Login failed'));
    }
  }

  // ==========================
  // REGISTER
  // ==========================
  async register(userData) {
    try {
      const response = await axios.post(
        `${API_URL}/api/auth/register/`,
        userData,
        { headers: { 'Content-Type': 'application/json' } }
      );
      return response.data;
    } catch (error) {
      throw new Error(extractError(error, 'Registration failed'));
    }
  }

  // ==========================
  // LOGOUT
  // ==========================
  async logout() {
    const refresh = localStorage.getItem('refresh_token');

    try {
      // Backend only needs refresh to blacklist.
      // Don't hard-fail logout if refresh is missing/invalid.
      const response = await axios.post(
        `${API_URL}/api/users/logout/`,
        { refresh },
        {
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader(),
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Logout error:', error);
      return null;
    }
  }

  // ==========================
  // RESET PASSWORD
  // ==========================
  async resetPassword(email) {
    try {
      const response = await axios.post(
        `${API_URL}/api/users/password-reset/`,
        { email },
        { headers: { 'Content-Type': 'application/json' } }
      );
      return response.data;
    } catch (error) {
      throw new Error(extractError(error, 'Password reset failed'));
    }
  }

  // ==========================
  // GET CURRENT USER
  // ==========================
  async getCurrentUser() {
    try {
      const response = await axios.get(
        `${API_URL}/api/auth/me/`,
        { headers: getAuthHeader() }
      );
      return response.data;
    } catch (error) {
      throw new Error(extractError(error, 'Failed to get user'));
    }
  }

  // ==========================
  // REFRESH TOKEN (Bonus)
  // ==========================
  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) throw new Error('No refresh token available');

    try {
      const response = await axios.post(
        `${API_URL}/api/auth/refresh/`,
        { refresh },
        { headers: { 'Content-Type': 'application/json' } }
      );
      return response.data;
    } catch (error) {
      throw new Error(extractError(error, 'Token refresh failed'));
    }
  }
}

export default new AuthService();