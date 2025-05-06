// frontend/src/pages/CreateProject.js
import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  CircularProgress,
  makeStyles,
} from '@material-ui/core';
import { ProjectContext } from '../context/ProjectContext';

const useStyles = makeStyles((theme) => ({
  container: {
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  paper: {
    padding: theme.spacing(3),
  },
  form: {
    marginTop: theme.spacing(2),
  },
  formControl: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  submitButton: {
    marginTop: theme.spacing(3),
  },
  githubField: {
    marginTop: theme.spacing(2),
  },
}));

const CreateProject = () => {
  const classes = useStyles();
  const navigate = useNavigate();
  const { addProject } = useContext(ProjectContext);

  const [projectName, setProjectName] = useState('');
  const [projectType, setProjectType] = useState('Manual Upload');
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate form
    if (!projectName.trim()) {
      setError('Project name is required');
      return;
    }

    if (projectType === 'GitHub Repository' && !repoUrl.trim()) {
      setError('Repository URL is required for GitHub projects');
      return;
    }

    try {
      setLoading(true);
      const projectData = {
        name: projectName,
        type: projectType,
        repo_url: projectType === 'GitHub Repository' ? repoUrl : null,
      };

      const newProject = await addProject(projectData);
      navigate(`/projects/${newProject.id}`);
    } catch (err) {
      setError('Failed to create project. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" className={classes.container}>
      <Typography variant="h4" component="h1" gutterBottom>
        Create New Project
      </Typography>
      <Paper className={classes.paper}>
        <form className={classes.form} onSubmit={handleSubmit}>
          <TextField
            label="Project Name"
            variant="outlined"
            fullWidth
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            required
          />

          <FormControl component="fieldset" className={classes.formControl}>
            <FormLabel component="legend">Project Type</FormLabel>
            <RadioGroup
              aria-label="project-type"
              name="project-type"
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
            >
              <FormControlLabel
                value="Manual Upload"
                control={<Radio />}
                label="Manual Upload"
              />
              <FormControlLabel
                value="GitHub Repository"
                control={<Radio />}
                label="GitHub Repository"
              />
            </RadioGroup>
          </FormControl>

          {projectType === 'GitHub Repository' && (
            <TextField
              className={classes.githubField}
              label="Repository URL"
              variant="outlined"
              fullWidth
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              required
              helperText="For non-default branches, include /tree/branch-name"
            />
          )}

          {error && (
            <Typography color="error" variant="body2" gutterBottom>
              {error}
            </Typography>
          )}

          <Button
            type="submit"
            variant="contained"
            color="primary"
            className={classes.submitButton}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Create Project'}
          </Button>
        </form>
      </Paper>
    </Container>
  );
};

export default CreateProject;