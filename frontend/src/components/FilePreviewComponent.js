// frontend/src/components/FilePreviewComponent.js
import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  makeStyles,
} from '@material-ui/core';

const useStyles = makeStyles((theme) => ({
  paper: {
    padding: theme.spacing(2),
  },
  table: {
    marginTop: theme.spacing(2),
  },
  codeBlock: {
    backgroundColor: theme.palette.grey[100],
    padding: theme.spacing(2),
    borderRadius: theme.shape.borderRadius,
    overflowX: 'auto',
    fontFamily: 'monospace',
  },
  buttonContainer: {
    marginTop: theme.spacing(2),
    display: 'flex',
    justifyContent: 'flex-end',
  },
}));

const FilePreviewComponent = ({ filePath, content, projectId }) => {
  const classes = useStyles();
  const [parsedStrings, setParsedStrings] = useState({});
  const [viewRaw, setViewRaw] = useState(false);

  useEffect(() => {
    if (content) {
      parseContent();
    }
  }, [filePath, content]);

  const parseContent = () => {
    if (filePath.endsWith('.xml')) {
      // Parse XML strings
      const strings = {};
      const regex = /<string[^>]*name="([^"]*)"[^>]*>([\s\S]*?)<\/string>/g;
      let match;
      
      while ((match = regex.exec(content)) !== null) {
        strings[match[1]] = match[2].trim();
      }
      
      setParsedStrings(strings);
    } else if (filePath.endsWith('.json')) {
      // Parse JSON strings
      try {
        const json = JSON.parse(content);
        setParsedStrings(json);
      } catch (err) {
        console.error('Error parsing JSON:', err);
        setParsedStrings({});
      }
    }
  };

  const toggleView = () => {
    setViewRaw(!viewRaw);
  };

  return (
    <div>
      <Paper className={classes.paper}>
        <Typography variant="subtitle1" gutterBottom>
          {filePath.split('/').pop()}
        </Typography>
        
        <Button
          variant="outlined"
          color="primary"
          onClick={toggleView}
          size="small"
        >
          {viewRaw ? 'Show Parsed View' : 'Show Raw Content'}
        </Button>
        
        {viewRaw ? (
          <pre className={classes.codeBlock}>
            {content}
          </pre>
        ) : (
          <TableContainer component={Paper} className={classes.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>String Key</strong></TableCell>
                  <TableCell><strong>Value</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(parsedStrings).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell component="th" scope="row">
                      {key}
                    </TableCell>
                    <TableCell>{value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </div>
  );
};

export default FilePreviewComponent;