// frontend/src/components/FileUploader.js
import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Button,
  CircularProgress,
  makeStyles,
} from '@material-ui/core';
import { Alert } from '@material-ui/lab';
import { CloudUpload as UploadIcon } from '@material-ui/icons';

const useStyles = makeStyles((theme) => ({
  uploadArea: {
    padding: theme.spacing(3),
    borderRadius: theme.shape.borderRadius,
    borderStyle: 'dashed',
    borderWidth: 2,
    borderColor: theme.palette.divider,
    textAlign: 'center',
    cursor: 'pointer',
    '&:hover': {
      borderColor: theme.palette.primary.main,
      backgroundColor: theme.palette.action.hover,
    },
  },
  uploadButton: {
    marginTop: theme.spacing(2),
  },
  input: {
    display: 'none',
  },
  uploadIcon: {
    fontSize: 48,
    marginBottom: theme.spacing(1),
  },
}));

const FileUploader = ({ onUpload }) => {
  const classes = useStyles();
  const [files, setFiles] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = async (event) => {
    const selectedFiles = event.target.files;
    
    if (!selectedFiles || selectedFiles.length === 0) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const result = {};
      
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        
        // Check file type
        if (!file.name.endsWith('.xml') && !file.name.endsWith('.json')) {
          setError('Only XML and JSON files are supported');
          setLoading(false);
          return;
        }
        
        // Read file content
        const content = await readFileContent(file);
        result[file.name] = content;
      }
      
      setFiles(result);
      
      // Call the onUpload callback
      if (onUpload) {
        onUpload(result);
      }
    } catch (err) {
      setError('Error reading files: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const readFileContent = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        resolve(event.target.result);
      };
      
      reader.onerror = (error) => {
        reject(error);
      };
      
      reader.readAsText(file);
    });
  };

  return (
    <div>
      <input
        accept=".xml,.json"
        className={classes.input}
        id="file-upload"
        multiple
        type="file"
        onChange={handleFileChange}
      />
      <label htmlFor="file-upload">
        <Paper className={classes.uploadArea} component="div">
          <UploadIcon color="primary" className={classes.uploadIcon} />
          <Typography variant="h6" gutterBottom>
            Drag and drop files here
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            or
          </Typography>
          <Button
            variant="contained"
            color="primary"
            component="span"
            className={classes.uploadButton}
            startIcon={loading ? <CircularProgress size={24} /> : <UploadIcon />}
            disabled={loading}
          >
            Browse Files
          </Button>
          <Typography variant="caption" display="block" color="textSecondary">
            Supported formats: XML, JSON
          </Typography>
        </Paper>
      </label>
      
      {error && (
        <Alert severity="error" style={{ marginTop: '10px' }}>
          {error}
        </Alert>
      )}
      
      {Object.keys(files).length > 0 && (
        <Alert severity="success" style={{ marginTop: '10px' }}>
          {Object.keys(files).length} file(s) uploaded successfully
        </Alert>
      )}
    </div>
  );
};

export default FileUploader;