// frontend/src/pages/Dashboard.js
import React, { useContext } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  makeStyles,
} from '@material-ui/core';
import { ProjectContext } from '../context/ProjectContext';

const useStyles = makeStyles((theme) => ({
  container: {
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  title: {
    marginBottom: theme.spacing(4),
  },
  card: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  cardContent: {
    flexGrow: 1,
  },
  chip: {
    margin: theme.spacing(0.5),
  },
  loader: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: theme.spacing(4),
  },
  noProjects: {
    marginTop: theme.spacing(4),
    textAlign: 'center',
  },
}));

const Dashboard = () => {
  const classes = useStyles();
  const { projects, loading, error, removeProject } = useContext(ProjectContext);

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await removeProject(projectId);
      } catch (err) {
        console.error('Error deleting project:', err);
      }
    }
  };

  if (loading) {
    return (
      <div className={classes.loader}>
        <CircularProgress />
      </div>
    );
  }

  if (error) {
    return (
      <Container className={classes.container}>
        <Typography variant="h6" color="error" align="center">
          {error}
        </Typography>
      </Container>
    );
  }

  return (
    <Container className={classes.container}>
      <Typography variant="h4" component="h1" className={classes.title}>
        Translation Projects Dashboard
      </Typography>

      {projects.length === 0 ? (
        <div className={classes.noProjects}>
          <Typography variant="h6" gutterBottom>
            No projects yet
          </Typography>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/projects/create"
          >
            Create Your First Project
          </Button>
        </div>
      ) : (
        <Grid container spacing={4}>
          {projects.map((project) => (
            <Grid item key={project.id} xs={12} sm={6} md={4}>
              <Card className={classes.card}>
                <CardContent className={classes.cardContent}>
                  <Typography variant="h5" component="h2" gutterBottom>
                    {project.name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Type: {project.type}
                  </Typography>
                  
                  {project.repo_url && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Repository: {project.repo_url}
                    </Typography>
                  )}
                  
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Files: {Object.keys(project.files || {}).length}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary">
                    Languages:
                  </Typography>
                  <div>
                    {Object.keys(project.translations || {}).map((lang) => (
                      <Chip
                        key={lang}
                        label={lang}
                        size="small"
                        className={classes.chip}
                      />
                    ))}
                    {Object.keys(project.file_translations || {}).length > 0 && (
                      <Chip
                        label={`${Object.keys(project.file_translations || {}).length} files`}
                        size="small"
                        className={classes.chip}
                      />
                    )}
                  </div>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    color="primary"
                    component={RouterLink}
                    to={`/projects/${project.id}`}
                  >
                    View Details
                  </Button>
                  <Button
                    size="small"
                    color="secondary"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
};

export default Dashboard;