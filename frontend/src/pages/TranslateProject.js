// frontend/src/pages/TranslateProject.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  makeStyles,
} from '@material-ui/core';
import Alert from '@material-ui/lab/Alert';
import { getProject, getSupportedLanguages, translateStrings } from '../services/api';
import FileUploader from '../components/FileUploader';

const useStyles = makeStyles((theme) => ({
  container: {
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  paper: {
    padding: theme.spacing(3),
  },
  stepper: {
    marginBottom: theme.spacing(3),
  },
  formControl: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
    minWidth: 200,
  },
  fileSelection: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: theme.spacing(3),
  },
  navButtons: {
    display: 'flex',
    gap: theme.spacing(1),
  },
  loader: {
    display: 'flex',
    justifyContent: 'center',
    padding: theme.spacing(4),
  },
}));

const steps = ['Select Files', 'Choose Languages', 'Translation Settings', 'Generate Translations'];

const TranslateProject = () => {
  const classes = useStyles();
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [activeStep, setActiveStep] = useState(0);
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [languages, setLanguages] = useState({});
  const [selectedLanguages, setSelectedLanguages] = useState([]);
  const [addContexts, setAddContexts] = useState(false);
  const [contexts, setContexts] = useState({});
  const [translating, setTranslating] = useState(false);
  const [translationComplete, setTranslationComplete] = useState(false);

  useEffect(() => {
    fetchProjectDetails();
    fetchSupportedLanguages();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);
      setProject(response.data);
    } catch (err) {
      setError('Failed to load project details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSupportedLanguages = async () => {
    try {
      const response = await getSupportedLanguages();
      setLanguages(response.data);
    } catch (err) {
      console.error('Failed to load supported languages:', err);
    }
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleFileSelect = (filePath) => {
    // Toggle file selection
    setSelectedFiles((prevSelected) => {
      if (prevSelected.includes(filePath)) {
        return prevSelected.filter(p => p !== filePath);
      } else {
        return [...prevSelected, filePath];
      }
    });
  };

  const handleFileUpload = (files) => {
    setUploadedFiles(files);
    // Select all uploaded files
    setSelectedFiles(Object.keys(files));
  };

  const handleLanguageSelect = (event) => {
    setSelectedLanguages(event.target.value);
  };

  const handleContextChange = (key, value) => {
    setContexts(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const getStringsFromFile = (filePath, content) => {
    // Simple XML parsing for demonstration
    // In a real app, you would use a proper XML parser
    const strings = {};
    // Basic regex to extract string elements (a very simple approach)
    const regex = /<string[^>]*name="([^"]*)"[^>]*>([\s\S]*?)<\/string>/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
      strings[match[1]] = match[2].trim();
    }
    return strings;
  };

  const handleTranslate = async () => {
    try {
      setTranslating(true);
      setError('');
      
      // Get strings from selected files
      const allTranslations = {};
      
      // Loop through each selected file
      for (const filePath of selectedFiles) {
        let fileContent;
        let strings;
        
        if (project.files && project.files[filePath]) {
          // Get from project files
          fileContent = project.files[filePath];
          strings = getStringsFromFile(filePath, fileContent);
        } else if (uploadedFiles[filePath]) {
          // Get from uploaded files
          fileContent = uploadedFiles[filePath];
          strings = getStringsFromFile(filePath, fileContent);
        }
        
        if (strings && Object.keys(strings).length > 0) {
          // Store original strings as English
          if (!allTranslations[filePath]) {
            allTranslations[filePath] = { en: strings };
          }
          
          // Translate to each selected language
          for (const langCode of selectedLanguages) {
            if (langCode === 'en') continue; // Skip English
            
            // Prepare contexts for this file's strings
            const fileContexts = {};
            if (addContexts) {
              for (const key of Object.keys(strings)) {
                if (contexts[key]) {
                  fileContexts[key] = contexts[key];
                }
              }
            }
            
            // Call translation API
            const response = await translateStrings({
              strings,
              target_language: Object.keys(languages).find(k => languages[k] === langCode) || langCode,
              contexts: fileContexts
            });
            
            // Store translations
            if (!allTranslations[filePath]) {
              allTranslations[filePath] = {};
            }
            allTranslations[filePath][langCode] = response.data.translations;
          }
        }
      }
      
      // Update project with new translations
      const updatedProject = { ...project };
      
      // Update file translations
      if (!updatedProject.file_translations) {
        updatedProject.file_translations = {};
      }
      
      // Merge new translations with existing ones
      for (const filePath in allTranslations) {
        if (!updatedProject.file_translations[filePath]) {
          updatedProject.file_translations[filePath] = {};
        }
        
        for (const langCode in allTranslations[filePath]) {
          updatedProject.file_translations[filePath][langCode] = {
            ...updatedProject.file_translations[filePath][langCode],
            ...allTranslations[filePath][langCode]
          };
        }
      }
      
      setProject(updatedProject);
      setTranslationComplete(true);
    } catch (err) {
      setError('Translation failed. Please try again.');
      console.error(err);
    } finally {
      setTranslating(false);
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
        <Alert severity="error" style={{ marginBottom: '20px' }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate(`/projects/${projectId}`)}
        >
          Back to Project
        </Button>
      </Container>
    );
  }

  const renderStepContent = (step) => {
    switch (step) {
      case 0: // Select Files
        return (
          <div>
            {project.type === 'GitHub Repository' && project.files && Object.keys(project.files).length > 0 ? (
              <div>
                <Typography variant="h6" gutterBottom>
                  Select files to translate
                </Typography>
                <List className={classes.fileSelection}>
                  {Object.keys(project.files).map((filePath) => (
                    <React.Fragment key={filePath}>
                      <ListItem button onClick={() => handleFileSelect(filePath)}>
                        <Checkbox
                          checked={selectedFiles.includes(filePath)}
                          color="primary"
                        />
                        <ListItemText 
                          primary={filePath.split('/').pop()} 
                          secondary={filePath} 
                        />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              </div>
            ) : (
              <div>
                <Typography variant="h6" gutterBottom>
                  Upload files to translate
                </Typography>
                <FileUploader onUpload={handleFileUpload} />
                
                {Object.keys(uploadedFiles).length > 0 && (
                  <div style={{ marginTop: '20px' }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Uploaded Files:
                    </Typography>
                    <List>
                      {Object.keys(uploadedFiles).map((fileName) => (
                        <ListItem key={fileName}>
                          <ListItemText primary={fileName} />
                        </ListItem>
                      ))}
                    </List>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      
      case 1: // Choose Languages
        return (
          <div>
            <Typography variant="h6" gutterBottom>
              Select target languages
            </Typography>
            <FormControl className={classes.formControl} fullWidth>
              <InputLabel>Target Languages</InputLabel>
              <Select
                multiple
                value={selectedLanguages}
                onChange={handleLanguageSelect}
                renderValue={(selected) => selected.map(code => 
                  Object.keys(languages).find(k => languages[k] === code) || code
                ).join(', ')}
              >
                {Object.entries(languages).map(([language, code]) => (
                  <MenuItem key={code} value={code}>
                    <Checkbox checked={selectedLanguages.includes(code)} />
                    <ListItemText primary={language} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </div>
        );
      
      case 2: // Translation Settings
        return (
          <div>
            <Typography variant="h6" gutterBottom>
              Translation Settings
            </Typography>
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={addContexts}
                  onChange={(e) => setAddContexts(e.target.checked)}
                  color="primary"
                />
              }
              label="Add context to improve translation quality"
            />
            
            {addContexts && (
              <div style={{ marginTop: '20px' }}>
                <Typography variant="subtitle1" gutterBottom>
                  Add context for strings (optional)
                </Typography>
                
                {selectedFiles.map(filePath => {
                  let strings = {};
                  if (project.files && project.files[filePath]) {
                    strings = getStringsFromFile(filePath, project.files[filePath]);
                  } else if (uploadedFiles[filePath]) {
                    strings = getStringsFromFile(filePath, uploadedFiles[filePath]);
                  }
                  
                  return Object.keys(strings).length > 0 ? (
                    <div key={filePath} style={{ marginBottom: '20px' }}>
                      <Typography variant="subtitle2">
                        {filePath.split('/').pop()}
                      </Typography>
                      
                      {Object.entries(strings).map(([key, value]) => (
                        <Grid container spacing={2} key={key} style={{ marginBottom: '10px' }}>
                          <Grid item xs={12} md={4}>
                            <TextField
                              label="String Key"
                              value={key}
                              fullWidth
                              disabled
                              variant="outlined"
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <TextField
                              label="Original Text"
                              value={value}
                              fullWidth
                              disabled
                              variant="outlined"
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <TextField
                              label="Context (e.g., 'Used on login button')"
                              value={contexts[key] || ''}
                              onChange={(e) => handleContextChange(key, e.target.value)}
                              fullWidth
                              variant="outlined"
                              size="small"
                            />
                          </Grid>
                        </Grid>
                      ))}
                    </div>
                  ) : null;
                })}
              </div>
            )}
          </div>
        );
      
      case 3: // Generate Translations
        return (
          <div>
            <Typography variant="h6" gutterBottom>
              Generate Translations
            </Typography>
            
            {translationComplete ? (
              <Alert severity="success" style={{ marginBottom: '20px' }}>
                Translations completed successfully!
              </Alert>
            ) : (
              <div>
                <Typography variant="body1" paragraph>
                  Ready to translate {selectedFiles.length} file(s) into {selectedLanguages.length} language(s).
                </Typography>
                
                {error && (
                  <Alert severity="error" style={{ marginBottom: '20px' }}>
                    {error}
                  </Alert>
                )}
                
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleTranslate}
                  disabled={translating}
                  style={{ marginTop: '20px' }}
                >
                  {translating ? (
                    <>
                      <CircularProgress size={24} style={{ marginRight: '10px' }} />
                      Translating...
                    </>
                  ) : (
                    'Start Translation'
                  )}
                </Button>
              </div>
            )}
            
            {translationComplete && (
              <div style={{ marginTop: '20px' }}>
                <Button
                  variant="contained"
                  // frontend/src/pages/TranslateProject.js (continued)
                  color="primary"
                  onClick={() => navigate(`/projects/${projectId}/review`)}
                >
                  Review Translations
                </Button>
              </div>
            )}
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <Container className={classes.container}>
      <Typography variant="h4" component="h1" gutterBottom>
        Translate Project: {project?.name}
      </Typography>
      
      <Paper className={classes.paper}>
        <Stepper activeStep={activeStep} className={classes.stepper}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {renderStepContent(activeStep)}
        
        <div className={classes.buttonContainer}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>
          
          <div className={classes.navButtons}>
            <Button
              variant="contained"
              color="secondary"
              onClick={() => navigate(`/projects/${projectId}`)}
            >
              Cancel
            </Button>
            
            {activeStep < steps.length - 1 && (
              <Button
                variant="contained"
                color="primary"
                onClick={handleNext}
                disabled={
                  (activeStep === 0 && selectedFiles.length === 0) ||
                  (activeStep === 1 && selectedLanguages.length === 0)
                }
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </Paper>
    </Container>
  );
};

export default TranslateProject;