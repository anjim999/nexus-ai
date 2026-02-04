import axios from 'axios';

// Get API URL from env with a clear fallback for development
const isProd = import.meta.env.PROD;
let API_URL = import.meta.env.VITE_API_URL || (isProd ? '/api/v1' : 'http://localhost:8000/api/v1');

// Ensure API_URL ends with a slash for proper joining
if (!API_URL.endsWith('/')) {
    API_URL += '/';
}

// Create Axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to handle leading slashes in relative URLs
api.interceptors.request.use((config) => {
    // If the URL starts with / and we have a baseURL, remove the / 
    // to ensure axios prepends the baseURL correctly instead of treating it as domain-root
    if (config.url && config.url.startsWith('/') && config.baseURL) {
        config.url = config.url.substring(1);
    }
    return config;
});

export default api;
