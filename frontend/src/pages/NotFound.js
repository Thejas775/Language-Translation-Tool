// frontend/src/pages/NotFound.js
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Typography,
  Button,
  makeStyles,
} from '@material-ui/core';

const useStyles = makeStyles((theme) => ({
  container: {
    marginTop: theme.spacing(8),
    textAlign: 'center',
  },
  button: {
    marginTop: theme.spacing(3),
  },
}));

const NotFound = () => {
  const classes = useStyles();

  return (
    <Container className={classes.container}>
      <Typography variant="h2" component="h1" gutterBottom>
        404
      </Typography>
      <Typography variant="h5" component="h2" gutterBottom>
        Page Not Found
      </Typography>
      <Typography variant="body1" paragraph>
        The page you are looking for does not exist or has been moved.
      </Typography>
      <Button
        variant="contained"
        color="primary"
        component={RouterLink}
        to="/"
        className={classes.button}
      >
        Go to Dashboard
      </Button>
    </Container>
  );
};

export default NotFound;