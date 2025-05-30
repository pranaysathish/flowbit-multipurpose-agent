import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = {
  processData: async (formData) => {
    const response = await axios.post(`${API_BASE_URL}/process`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  
  getStatus: async (requestId) => {
    const response = await axios.get(`${API_BASE_URL}/status/${requestId}`);
    return response.data;
  }
};

export default api;