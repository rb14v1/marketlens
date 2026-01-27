import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import InputPage from './pages/InputPage';
import ResultPage from './pages/ResultPage';
<<<<<<< HEAD
=======
import ComparisonPage from './pages/ComparisonPage';
>>>>>>> final_version
import Footer from './components/Footer';
import Header from './components/Header';

function App() {
  return (
    <Router>
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
        <Header />
        <Box component="main" sx={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/" element={<InputPage />} />
            <Route path="/results" element={<ResultPage />} />
<<<<<<< HEAD
=======
            <Route path="/comparison" element={<ComparisonPage />} />
>>>>>>> final_version
          </Routes>
        </Box>
        <Footer />
      </Box>
    </Router>
  )
}

export default App
