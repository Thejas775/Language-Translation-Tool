// frontend/src/context/ProjectContext.js
import React, { createContext, useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject } from '../services/api';

export const ProjectContext = createContext();

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await getProjects();
      setProjects(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch projects');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const addProject = async (projectData) => {
    try {
      setLoading(true);
      const response = await createProject(projectData);
      setProjects([...projects, response.data]);
      return response.data;
    } catch (err) {
      setError('Failed to create project');
      console.error(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeProject = async (projectId) => {
    try {
      setLoading(true);
      await deleteProject(projectId);
      setProjects(projects.filter(project => project.id !== projectId));
    } catch (err) {
      setError('Failed to delete project');
      console.error(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        loading,
        error,
        fetchProjects,
        addProject,
        removeProject
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};