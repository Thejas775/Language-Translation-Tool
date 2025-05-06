// frontend/src/components/Header.js
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  makeStyles 
} from '@material-ui/core';
import TranslateIcon from '@material-ui/icons/Translate';

const useStyles = makeStyles((theme) => ({
  title: {
    flexGrow: 1,
    display: 'flex',
    alignItems: 'center',
  },
  icon: {
    marginRight: theme.spacing(1),
  },
  link: {
    color: 'white',
    textDecoration: 'none',
  },
  button: {
    marginLeft: theme.spacing(1),
  },
}));

const Header = () => {
  const classes = useStyles();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" className={classes.title}>
          <RouterLink to="/" className={classes.link}>
            <TranslateIcon className={classes.icon} />
            UI String Translator
          </RouterLink>
        </Typography>
        <Button 
          component={RouterLink} 
          to="/projects/create" 
          color="inherit" 
          className={classes.button}
        >
          Create Project
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Header;