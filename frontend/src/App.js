// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';

// Import contexts
import { ProjectProvider } from './context/ProjectContext';

// Import components
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import ProjectDetails from './pages/ProjectDetails';
import CreateProject from './pages/CreateProject';
import TranslateProject from './pages/TranslateProject';
import ReviewTranslations from './pages/ReviewTranslations';
import NotFound from './pages/NotFound';

// Create theme
const theme = createMuiTheme({
  palette: {
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ProjectProvider>
        <Router>
          <Header />
          <main style={{ padding: '20px' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects/create" element={<CreateProject />} />
              <Route path="/projects/:projectId" element={<ProjectDetails />} />
              <Route path="/projects/:projectId/translate" element={<TranslateProject />} />
              <Route path="/projects/:projectId/review" element={<ReviewTranslations />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
        </Router>
      </ProjectProvider>
    </ThemeProvider>
  );
}

export default App;