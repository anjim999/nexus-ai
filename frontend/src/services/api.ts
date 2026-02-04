import axios from 'axios';

// Use the variable you added to Vercel/Local env
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create Axios instance with clean baseURL
const api = axios.create({
    baseURL: API_URL.endsWith('/') ? API_URL : `${API_URL}/`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Keep this interceptor to prevent URL joining errors if requests start with /
api.interceptors.request.use((config) => {
    if (config.url && config.url.startsWith('/') && config.baseURL) {
        config.url = config.url.substring(1);
    }
    return config;
});

export default api;
