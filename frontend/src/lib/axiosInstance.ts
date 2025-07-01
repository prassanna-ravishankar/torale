import axios from 'axios';
import { supabase } from './supabaseClient'; // Assuming supabaseClient.ts is in the same directory

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to add Supabase JWT to Authorization header
axiosInstance.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => {
    // Handle request error here
    return Promise.reject(error);
  }
);

// Optional: Response interceptor for global error handling (e.g., 401 unauthorized)
axiosInstance.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // Do something with response data
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // Do something with response error
    // For example, you might want to redirect to login on 401 errors
    if (error.response && error.response.status === 401) {
      // Potentially clear session or redirect to login
      // console.error('Unauthorized request, redirecting to login...');
      // window.location.href = '/auth/login'; // Example, adjust as needed
    }
    return Promise.reject(error);
  }
);

export default axiosInstance; 