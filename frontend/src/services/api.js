import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Interceptor para inyectar automáticamente el Bearer token almacenado
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Interceptor de respuesta para manejar errores 401 (desconexión si el token expiró)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Endpoints de Autenticación
export const authApi = {
  register: (username, password) => api.post('/auth/register', { username, password }),
  login: (username, password) => api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
};

// Endpoints de Películas (TMDB)
export const moviesApi = {
  getMovies: (page = 1, query = '') => {
    const params = { page };
    if (query) params.query = query;
    return api.get('/movies', { params });
  },
  getMovieDetail: (tmdbId) => api.get(`/movies/${tmdbId}`),
};

// Endpoints de Me Gusta
export const likesApi = {
  getLikes: () => api.get('/likes'),
  addLike: (tmdbId, movieData = {}) => api.post(`/likes/${tmdbId}`, movieData),
  removeLike: (tmdbId) => api.delete(`/likes/${tmdbId}`),
};

// Endpoints de Recomendaciones
export const recommendationsApi = {
  requestRecommendation: () => api.post('/recommendations/request'),
  getStatus: (jobId) => api.get(`/recommendations/status/${jobId}`),
  getRecommendations: () => api.get('/recommendations'),
};

export default api;
