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

export type ErrorObserver = (error: APIError, rawAxiosError: any) => void;

let _errorObserver: ErrorObserver = (err) => {
  if (__DEV__) {
    console.warn(`[API Error Observed: ${err.error.code}]`, err.error.message);
  }
};

export const registerErrorObserver = (observer: ErrorObserver): void => {
  _errorObserver = observer;
};

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let apiErr: APIError;
    if (error.response?.data?.error) {
      apiErr = error.response.data;
    } else {
      apiErr = {
        error: {
          code: 'INTERNAL_ERROR',
          message: error.message || 'Unable to communicate with the server.',
        },
      };
    }
    try {
      _errorObserver(apiErr, error);
    } catch (_) {
      // Observers must not swallow or crash the promise rejection
    }
    return Promise.reject(apiErr);
  }
);
