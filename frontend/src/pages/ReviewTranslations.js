// frontend/src/pages/ReviewTranslations.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Button,
  Tabs,
  Tab,
  Box,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  InputAdornment,
  makeStyles,
} from '@material-ui/core';
import { 
  Search as SearchIcon,
  GetApp as DownloadIcon,
  Save as SaveIcon,
} from '@material-ui/icons';
import Alert from '@material-ui/lab/Alert';
import { getProject, updateProject } from '../services/api';

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
  tabs: {
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 200,
  },
  searchField: {
    marginBottom: theme.spacing(2),
  },
  tableContainer: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: theme.spacing(1),
    marginTop: theme.spacing(2),
  },
  loader: {
    display: 'flex',
    justifyContent: 'center',
    padding: theme.spacing(4),
  },
}));

const ReviewTranslations = () => {
  const classes = useStyles();
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [selectedFile, setSelectedFile] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [editedTranslations, setEditedTranslations] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);
      setProject(response.data);
      
      // Set initial selection if available
      if (response.data.file_translations && Object.keys(response.data.file_translations).length > 0) {
        const firstFile = Object.keys(response.data.file_translations)[0];
        setSelectedFile(firstFile);
        
        const fileTranslations = response.data.file_translations[firstFile];
        if (fileTranslations && Object.keys(fileTranslations).length > 0) {
          // Prefer a non-English language if available
          const nonEnglish = Object.keys(fileTranslations).find(lang => lang !== 'en');
          setSelectedLanguage(nonEnglish || Object.keys(fileTranslations)[0]);
        }
      } else if (response.data.translations && Object.keys(response.data.translations).length > 0) {
        // If there are project-wide translations, show them first
        setTabValue(1);
        
        // Prefer a non-English language if available
        const nonEnglish = Object.keys(response.data.translations).find(lang => lang !== 'en');
        setSelectedLanguage(nonEnglish || Object.keys(response.data.translations)[0]);
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
    
    // Reset selections when changing tabs
    if (newValue === 0) {
      // File translations tab
      if (project?.file_translations && Object.keys(project.file_translations).length > 0) {
        const firstFile = Object.keys(project.file_translations)[0];
        setSelectedFile(firstFile);
        
        const fileTranslations = project.file_translations[firstFile];
        if (fileTranslations && Object.keys(fileTranslations).length > 0) {
          const nonEnglish = Object.keys(fileTranslations).find(lang => lang !== 'en');
          setSelectedLanguage(nonEnglish || Object.keys(fileTranslations)[0]);
        }
      }
    } else {
      // Project-wide translations tab
      if (project?.translations && Object.keys(project.translations).length > 0) {
        const nonEnglish = Object.keys(project.translations).find(lang => lang !== 'en');
        setSelectedLanguage(nonEnglish || Object.keys(project.translations)[0]);
      }
    }
    
    // Reset edited translations
    setEditedTranslations({});
    setSaveSuccess(false);
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.value);
    
    // Reset language selection for the new file
    if (project?.file_translations?.[event.target.value]) {
      const fileTranslations = project.file_translations[event.target.value];
      const nonEnglish = Object.keys(fileTranslations).find(lang => lang !== 'en');
      setSelectedLanguage(nonEnglish || Object.keys(fileTranslations)[0]);
    } else {
      setSelectedLanguage('');
    }
    
    // Reset edited translations
    setEditedTranslations({});
    setSaveSuccess(false);
  };

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    
    // Reset edited translations
    setEditedTranslations({});
    setSaveSuccess(false);
  };

  const handleTranslationChange = (key, value) => {
    setEditedTranslations(prev => ({
      ...prev,
      [key]: value
    }));
    
    // Reset save success
    setSaveSuccess(false);
  };

  const handleSaveTranslations = async () => {
    try {
      setSaving(true);
      setSaveSuccess(false);
      
      const updatedProject = { ...project };
      
      if (tabValue === 0) {
        // Save file translations
        if (selectedFile && selectedLanguage) {
          // Update the translations with edited values
          for (const [key, value] of Object.entries(editedTranslations)) {
            updatedProject.file_translations[selectedFile][selectedLanguage][key] = value;
          }
        }
      } else {
        // Save project-wide translations
        if (selectedLanguage) {
          // Update the translations with edited values
          for (const [key, value] of Object.entries(editedTranslations)) {
            updatedProject.translations[selectedLanguage][key] = value;
          }
        }
      }
      
      // Save the updated project
      await updateProject(projectId, updatedProject);
      
      // Update the local state
      setProject(updatedProject);
      
      // Reset edited translations and show success message
      setEditedTranslations({});
      setSaveSuccess(true);
    } catch (err) {
      setError('Failed to save translations');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleExportXml = () => {
    try {
      let xmlContent = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n';
      
      let translations = {};
      
      if (tabValue === 0 && selectedFile && selectedLanguage) {
        // Get file translations
        translations = project.file_translations[selectedFile][selectedLanguage];
      } else if (tabValue === 1 && selectedLanguage) {
        // Get project-wide translations
        translations = project.translations[selectedLanguage];
      }
      
      // Build XML content
      for (const [key, value] of Object.entries(translations)) {
        xmlContent += `  <string name="${key}">${value}</string>\n`;
      }
      
      xmlContent += '</resources>';
      
      // Create download link
      const blob = new Blob([xmlContent], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Set filename
      const filename = tabValue === 0
        ? `${selectedFile.split('/').pop().replace('.xml', '')}_${selectedLanguage}.xml`
        : `strings_${selectedLanguage}.xml`;
      
      a.download = filename;
      a.click();
      
      // Clean up
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting XML:', err);
      alert('Failed to export XML file.');
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

  const hasFileTranslations = project?.file_translations && Object.keys(project.file_translations).length > 0;
  const hasProjectTranslations = project?.translations && Object.keys(project.translations).length > 0;

  if (!hasFileTranslations && !hasProjectTranslations) {
    return (
      <Container className={classes.container}>
        <Typography variant="h4" component="h1" gutterBottom>
          Review Translations: {project?.name}
        </Typography>
        <Paper className={classes.paper}>
          <Alert severity="info">
            No translations found for this project. Go to the Translate tab to generate translations.
          </Alert>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate(`/projects/${projectId}/translate`)}
            style={{ marginTop: '20px' }}
          >
            Translate Project
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container className={classes.container}>
      <Typography variant="h4" component="h1" gutterBottom>
        Review Translations: {project?.name}
      </Typography>
      
      <Paper className={classes.paper}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          className={classes.tabs}
        >
          <Tab 
            label="File Translations" 
            disabled={!hasFileTranslations} 
          />
          <Tab 
            label="Project Translations" 
            disabled={!hasProjectTranslations} 
          />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          {hasFileTranslations && (
            <div>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl className={classes.formControl} fullWidth>
                    <InputLabel>Select File</InputLabel>
                    <Select
                      value={selectedFile}
                      onChange={handleFileChange}
                    >
                      {Object.keys(project.file_translations).map((filePath) => (
                        <MenuItem key={filePath} value={filePath}>
                          {filePath.split('/').pop()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl className={classes.formControl} fullWidth disabled={!selectedFile}>
                    <InputLabel>Select Language</InputLabel>
                    <Select
                      value={selectedLanguage}
                      onChange={handleLanguageChange}
                    >
                      {selectedFile && project.file_translations[selectedFile] &&
                        Object.keys(project.file_translations[selectedFile]).map((langCode) => (
                          <MenuItem key={langCode} value={langCode}>
                            {langCode}
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
              
              {selectedFile && selectedLanguage && (
                <div>
                  <TextField
                    className={classes.searchField}
                    label="Search"
                    variant="outlined"
                    fullWidth
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                  
                  <TableContainer component={Paper} className={classes.tableContainer}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Key</TableCell>
                          <TableCell>Original (en)</TableCell>
                          <TableCell>Translation ({selectedLanguage})</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(project.file_translations[selectedFile][selectedLanguage] || {})
                          .filter(([key, value]) => {
                            if (!searchQuery) return true;
                            const lowerQuery = searchQuery.toLowerCase();
                            const originalValue = project.file_translations[selectedFile].en?.[key] || '';
                            return key.toLowerCase().includes(lowerQuery) ||
                              value.toLowerCase().includes(lowerQuery) ||
                              originalValue.toLowerCase().includes(lowerQuery);
                          })
                          .map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell component="th" scope="row">
                                {key}
                              </TableCell>
                              <TableCell>
                                {project.file_translations[selectedFile].en?.[key] || ''}
                              </TableCell>
                              <TableCell>
                                <TextField
                                  fullWidth
                                  multiline
                                  variant="outlined"
                                  value={editedTranslations[key] !== undefined ? editedTranslations[key] : value}
                                  onChange={(e) => handleTranslationChange(key, e.target.value)}
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  <div className={classes.buttonContainer}>
                    {saveSuccess && (
                      <Alert severity="success" style={{ marginRight: 'auto' }}>
                        Translations saved successfully!
                      </Alert>
                    )}
                    
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportXml}
                    >
                      Export XML
                    </Button>
                    
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<SaveIcon />}
                      onClick={handleSaveTranslations}
                      disabled={saving || Object.keys(editedTranslations).length === 0}
                    >
                      {saving ? <CircularProgress size={24} /> : 'Save Changes'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {hasProjectTranslations && (
            <div>
              <FormControl className={classes.formControl} fullWidth>
                <InputLabel>Select Language</InputLabel>
                <Select
                  value={selectedLanguage}
                  onChange={handleLanguageChange}
                >
                  {Object.keys(project.translations).map((langCode) => (
                    <MenuItem key={langCode} value={langCode}>
                      {langCode}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {selectedLanguage && (
                <div>
                  <TextField
                    className={classes.searchField}
                    label="Search"
                    variant="outlined"
                    fullWidth
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                  
                  <TableContainer component={Paper} className={classes.tableContainer}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Key</TableCell>
                          <TableCell>Original (en)</TableCell>
                          <TableCell>Translation ({selectedLanguage})</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(project.translations[selectedLanguage] || {})
                          .filter(([key, value]) => {
                            if (!searchQuery) return true;
                            const lowerQuery = searchQuery.toLowerCase();
                            const originalValue = project.translations.en?.[key] || '';
                            return key.toLowerCase().includes(lowerQuery) ||
                              value.toLowerCase().includes(lowerQuery) ||
                              originalValue.toLowerCase().includes(lowerQuery);
                          })
                          .map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell component="th" scope="row">
                                {key}
                              </TableCell>
                              <TableCell>
                                {project.translations.en?.[key] || ''}
                              </TableCell>
                              <TableCell>
                                <TextField
                                  fullWidth
                                  multiline
                                  variant="outlined"
                                  value={editedTranslations[key] !== undefined ? editedTranslations[key] : value}
                                  onChange={(e) => handleTranslationChange(key, e.target.value)}
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  <div className={classes.buttonContainer}>
                    {saveSuccess && (
                      <Alert severity="success" style={{ marginRight: 'auto' }}>
                        Translations saved successfully!
                      </Alert>
                    )}
                    
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportXml}
                    >
                      Export XML
                    </Button>
                    
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<SaveIcon />}
                      onClick={handleSaveTranslations}
                      disabled={saving || Object.keys(editedTranslations).length === 0}
                    >
                      {saving ? <CircularProgress size={24} /> : 'Save Changes'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default ReviewTranslations;