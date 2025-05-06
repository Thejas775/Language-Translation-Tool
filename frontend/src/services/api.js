// frontend/src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Projects API
export const createProject = (projectData) => {
  return api.post('/api/projects/', projectData);
};

export const getProjects = () => {
  return api.get('/api/projects/');
};

export const getProject = (projectId) => {
  return api.get(`/api/projects/${projectId}`);
};

export const updateProject = (projectId, projectData) => {
  return api.put(`/api/projects/${projectId}`, projectData);
};

export const deleteProject = (projectId) => {
  return api.delete(`/api/projects/${projectId}`);
};

// GitHub API
export const scanGithubRepository = (scanData) => {
  return api.post('/api/github/scan', scanData);
};

// Translations API
export const translateStrings = (translationData) => {
  return api.post('/api/translations/translate', translationData);
};

export const getSupportedLanguages = () => {
  return api.get('/api/translations/languages');
};

export default api;