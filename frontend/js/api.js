// Central API Client for HealthSenseAI
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : ''; // Use relative path in production (same origin)

const api = {
  // Helper to make API requests with JWT authentication automatically injected
  async fetch(endpoint, options = {}) {
    const token = localStorage.getItem('hs_token');
    
    // Set headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const url = `${API_BASE_URL}${endpoint}`;
    const method = options.method || 'GET';
    
    console.log(`[API] Request -> ${method} ${url}`);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      const responseText = await response.text();
      let data = null;
      
      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch (parseError) {
          data = responseText;
        }
      }
      
      console.log(`[API] Response <- ${method} ${url} status=${response.status}`);
      console.log(`[API] Response body <- ${method} ${url}:`, data);
      
      // Handle unauthorized (expired token)
      if (response.status === 401 && !endpoint.includes('/api/auth/')) {
        this.logout();
        window.location.href = 'login.html?expired=true';
        throw new Error('Session expired. Please log in again.');
      }
      
      if (!response.ok) {
        throw new Error((data && data.detail) || 'An error occurred.');
      }
      
      return data;
    } catch (error) {
      console.error(`[API] Error (${endpoint}):`, error);
      throw error;
    }
  },

  // Authentication
  async register(fullName, email, password, confirmPassword) {
    return this.fetch('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword
      })
    });
  },

  async login(email, password) {
    const data = await this.fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    // Save details to localStorage
    localStorage.setItem('hs_token', data.access_token);
    localStorage.setItem('hs_user', JSON.stringify(data.user));
    return data;
  },

  logout() {
    localStorage.removeItem('hs_token');
    localStorage.removeItem('hs_user');
  },

  getUser() {
    const userStr = localStorage.getItem('hs_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  isAuthenticated() {
    return !!localStorage.getItem('hs_token');
  },

  // Symptom Checker & ML Prediction
  async getSymptomsList() {
    const data = await this.fetch('/api/symptoms-list');
    const symptoms = Array.isArray(data)
      ? data
      : (data && Array.isArray(data.symptoms) ? data.symptoms : []);

    console.log(`[API] Symptoms loaded from /api/symptoms-list: ${symptoms.length}`);
    return symptoms;
  },

  async predict(symptoms) {
    return this.fetch('/api/predict', {
      method: 'POST',
      body: JSON.stringify({ symptoms })
    });
  },

  // History
  async getHistory(page = 1, limit = 10, search = '', sort = 'desc') {
    let query = `?page=${page}&limit=${limit}&sort=${sort}`;
    if (search) {
      query += `&search=${encodeURIComponent(search)}`;
    }
    return this.fetch(`/api/history${query}`);
  },

  // Profile
  async getProfile() {
    return this.fetch('/api/profile');
  },

  async updateProfile(fullName, age, gender) {
    return this.fetch('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({
        full_name: fullName,
        age: age ? parseInt(age) : null,
        gender: gender || null
      })
    });
  },

  // Reports
  async generateReport(predictionId) {
    return this.fetch('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ prediction_id: predictionId })
    });
  },

  getReportDownloadUrl(predictionId) {
    const token = localStorage.getItem('hs_token');
    return `${API_BASE_URL}/api/reports/download/${predictionId}?token=${token}`;
  },
  
  // Custom fetch helper for PDF download
  async downloadReportPDF(predictionId, filename) {
    const token = localStorage.getItem('hs_token');
    const url = `${API_BASE_URL}/api/reports/download/${predictionId}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || `healthsense_report_${predictionId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error("PDF Download Error:", error);
      throw error;
    }
  },

  // Admin Dashboard
  async getAdminStats() {
    return this.fetch('/api/admin/stats');
  }
};
