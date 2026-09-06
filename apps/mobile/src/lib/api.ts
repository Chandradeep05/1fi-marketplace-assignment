import axios from 'axios';
import { APIError } from '@1fi/contracts';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      const apiErr: APIError = error.response.data;
      return Promise.reject(apiErr);
    }
    const fallbackErr: APIError = {
      error: {
        code: 'INTERNAL_ERROR',
        message: error.message || 'Unable to communicate with the server.',
      },
    };
    return Promise.reject(fallbackErr);
  }
);
