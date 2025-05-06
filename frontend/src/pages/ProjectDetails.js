// frontend/src/pages/ProjectDetails.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Button,
  Tabs,
  Tab,
  Box,
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  makeStyles,
} from '@material-ui/core';
import { 
  Refresh as RefreshIcon,
  Translate as TranslateIcon,
  RateReview as ReviewIcon
} from '@material-ui/icons';
import { getProject, scanGithubRepository } from '../services/api';
import FilePreviewComponent from '../components/FilePreviewComponent';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box p={3}>{children}</Box>}
    </div>
  );
}

const useStyles = makeStyles((theme) => ({
  container: {
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  paper: {
    padding: theme.spacing(3),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing(3),
  },
  buttonContainer: {
    display: 'flex',
    gap: theme.spacing(1),
  },
  tabs: {
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
  chip: {
    margin: theme.spacing(0.5),
  },
  noFiles: {
    textAlign: 'center',
    padding: theme.spacing(3),
  },
  loader: {
    display: 'flex',
    justifyContent: 'center',
    padding: theme.spacing(4),
  },
}));

const ProjectDetails = () => {
  const classes = useStyles();
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [selectedFile, setSelectedFile] = useState('');
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);
      setProject(response.data);
      
      // Set the first file as selected file if available
      const files = response.data.files || {};
      if (Object.keys(files).length > 0) {
        setSelectedFile(Object.keys(files)[0]);
      }
    } catch (err) {
      setError('Failed to load project details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleScanRepository = async () => {
    if (!project || !project.repo_url) return;
    
    try {
      setScanning(true);
      const response = await scanGithubRepository({
        repo_url: project.repo_url,
        pattern_search: true,
      });
      
      // Update project with new files
      const updatedProject = {
        ...project,
        files: response.data.files,
      };
      setProject(updatedProject);
      
      // Set the first file as selected
      if (Object.keys(response.data.files).length > 0) {
        setSelectedFile(Object.keys(response.data.files)[0]);
      }
    } catch (err) {
      console.error('Error scanning repository:', err);
      alert('Failed to scan repository. Please check your token and try again.');
    } finally {
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className={classes.loader}>
        <CircularProgress />
      </div>
    );
  }

  if (error || !project) {
    return (
      <Container className={classes.container}>
        <Typography variant="h6" color="error" align="center">
          {error || 'Project not found'}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          component={RouterLink}
          to="/"
          style={{ display: 'block', margin: '20px auto' }}
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  const fileCount = Object.keys(project.files || {}).length;
  const translationCount = Object.keys(project.translations || {}).length;
  const fileTranslationCount = Object.keys(project.file_translations || {}).length;

  return (
    <Container className={classes.container}>
      <div className={classes.header}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            {project.name}
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Type: {project.type}
          </Typography>
          {project.repo_url && (
            <Typography variant="subtitle1" color="textSecondary">
              Repository: {project.repo_url}
            </Typography>
          )}
        </div>
        <div className={classes.buttonContainer}>
          {project.type === 'GitHub Repository' && (
            <Button
              variant="outlined"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={handleScanRepository}
              disabled={scanning}
            >
              {scanning ? <CircularProgress size={24} /> : 'Scan Repository'}
            </Button>
          )}
          <Button
            variant="contained"
            color="primary"
            startIcon={<TranslateIcon />}
            component={RouterLink}
            to={`/projects/${projectId}/translate`}
            disabled={fileCount === 0}
          >
            Translate
          </Button>
          {(translationCount > 0 || fileTranslationCount > 0) && (
            <Button
              variant="contained"
              color="secondary"
              startIcon={<ReviewIcon />}
              component={RouterLink}
              to={`/projects/${projectId}/review`}
            >
              Review Translations
            </Button>
          )}
        </div>
      </div>

      <Paper className={classes.paper}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          className={classes.tabs}
        >
          <Tab label={`Files (${fileCount})`} />
          <Tab label={`Translations (${translationCount + fileTranslationCount})`} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {fileCount === 0 ? (
            <div className={classes.noFiles}>
              <Typography variant="body1" gutterBottom>
                No files found in this project.
              </Typography>
              {project.type === 'GitHub Repository' ? (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleScanRepository}
                  disabled={scanning}
                >
                  {scanning ? <CircularProgress size={24} /> : 'Scan Repository'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  color="primary"
                  component={RouterLink}
                  to={`/projects/${projectId}/translate`}
                >
                  Upload Files
                </Button>
              )}
            </div>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Project Files
                </Typography>
                <List>
                  {Object.keys(project.files || {}).map((filePath) => (
                    <React.Fragment key={filePath}>
                      <ListItem 
                        button 
                        selected={selectedFile === filePath}
                        onClick={() => setSelectedFile(filePath)}
                      >
                        <ListItemText 
                          primary={filePath.split('/').pop()} 
                          secondary={filePath} 
                        />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              </Grid>
              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>
                  File Preview
                </Typography>
                {selectedFile ? (
                  <FilePreviewComponent 
                    filePath={selectedFile} 
                    content={project.files[selectedFile]} 
                    projectId={projectId}
                  />
                ) : (
                  <Typography variant="body1">
                    Select a file to preview
                  </Typography>
                )}
              </Grid>
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Available Translations
          </Typography>

          {translationCount === 0 && fileTranslationCount === 0 ? (
            <div className={classes.noFiles}>
              <Typography variant="body1" gutterBottom>
                No translations available for this project.
              </Typography>
              <Button
                variant="contained"
                color="primary"
                component={RouterLink}
                to={`/projects/${projectId}/translate`}
                disabled={fileCount === 0}
              >
                Translate Now
              </Button>
            </div>
          ) : (
            <div>
              {translationCount > 0 && (
                <div>
                  <Typography variant="subtitle1" gutterBottom>
                    Project-wide Translations:
                  </Typography>
                  <div>
                    {Object.keys(project.translations || {}).map((lang) => (
                      <Chip
                        key={lang}
                        label={lang}
                        className={classes.chip}
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </div>
                </div>
              )}

              {fileTranslationCount > 0 && (
                <div style={{ marginTop: '20px' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    File-specific Translations:
                  </Typography>
                  <List>
                    {Object.keys(project.file_translations || {}).map((filePath) => (
                      <ListItem key={filePath}>
                        <ListItemText 
                          primary={filePath.split('/').pop()}
                          secondary={`Languages: ${Object.keys(project.file_translations[filePath]).join(', ')}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              )}

              <Button
                variant="contained"
                color="secondary"
                component={RouterLink}
                to={`/projects/${projectId}/review`}
                style={{ marginTop: '20px' }}
              >
                Review Translations
              </Button>
            </div>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default ProjectDetails;