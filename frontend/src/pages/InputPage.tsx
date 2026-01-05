import React, { useState, useEffect, useRef } from 'react';
import { Box, Button, Typography, Container, Paper, TextField, Alert, Fade, Zoom } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PublicIcon from '@mui/icons-material/Public'; // Agent 1 Icon
import PsychologyIcon from '@mui/icons-material/Psychology'; // Agent 2 Icon
import CheckCircleIcon from '@mui/icons-material/CheckCircle'; // Success Icon

const InputPage: React.FC = () => {
    const [companyName, setCompanyName] = useState('');
    const [dataRequirements, setDataRequirements] = useState('');
    const [loadingStage, setLoadingStage] = useState<'idle' | 'agent1' | 'agent2' | 'success'>('idle');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    
    // Timers ref to clear them if component unmounts or request finishes early
    const transitionTimer = useRef<NodeJS.Timeout | null>(null);

    const handleSubmit = async () => {
        setLoadingStage('agent1'); // Start Animation
        setError(null);

        // 1. UX HACK: Automatically switch to "Agent 2" visual after 4 seconds (Previously 12s)
        // This makes the user feel progress while waiting for the single backend response.
        transitionTimer.current = setTimeout(() => {
            setLoadingStage((prev) => (prev === 'agent1' ? 'agent2' : prev));
        }, 4000); 

        try {
            // ---------------------------------------------------------
            // REAL BACKEND CALL
            // ---------------------------------------------------------
            const response = await fetch('http://127.0.0.1:8000/api/research/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    company_name: companyName, 
                    requirements: dataRequirements 
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to connect to the Agent. Is Django running?');
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message || 'Agent failed to retrieve data');
            }

            // ---------------------------------------------------------
            // SUCCESS: DATA RECEIVED
            // ---------------------------------------------------------
            // Clear the "Agent 2" timer if it hasn't fired yet
            if (transitionTimer.current) clearTimeout(transitionTimer.current);
            
            // Show Success Animation
            setLoadingStage('success');

            // Wait 1.5s for user to see the "Success" checkmark, then navigate
            setTimeout(() => {
                navigate('/results', {
                    state: {
                        apiResponse: data,
                        timestamp: new Date().toISOString()
                    }
                });
            }, 1500);

        } catch (err: any) {
            console.error("API Error:", err);
            setError(err.message || "Something went wrong.");
            setLoadingStage('idle'); // Reset UI on error
            if (transitionTimer.current) clearTimeout(transitionTimer.current);
        }
    };

    // Helper component for the animated circles
    const StatusCircle = ({ active, completed, icon: Icon, label }: any) => (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mx: 2, opacity: active || completed ? 1 : 0.4, transition: 'all 0.5s ease' }}>
            <Box sx={{
                position: 'relative',
                width: 80, height: 80, borderRadius: '50%',
                bgcolor: completed ? '#4caf50' : (active ? 'primary.main' : 'grey.300'),
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: active ? '0 0 20px rgba(0, 197, 193, 0.6)' : 'none',
                transition: 'all 0.5s ease'
            }}>
                {completed ? <CheckCircleIcon sx={{ fontSize: 40, color: 'white' }} /> : <Icon sx={{ fontSize: 40, color: 'white' }} />}
                
                {/* Pulse Animation for Active State */}
                {active && !completed && (
                    <Box sx={{
                        position: 'absolute', top: -4, left: -4, right: -4, bottom: -4,
                        borderRadius: '50%', border: '2px solid', borderColor: 'primary.main',
                        animation: 'pulse 1.5s infinite'
                    }} />
                )}
            </Box>
            <Typography variant="body2" sx={{ mt: 1.5, fontWeight: 600, color: active || completed ? 'text.primary' : 'text.disabled' }}>
                {label}
            </Typography>
        </Box>
    );

    return (
        <Container maxWidth="sm">
            <style>
                {`@keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    100% { transform: scale(1.3); opacity: 0; }
                }`}
            </style>

            <Box sx={{ minHeight: '80vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Paper
                    elevation={0}
                    sx={{
                        p: 6, borderRadius: 3, border: '1px solid', borderColor: 'divider',
                        boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.05)', backgroundColor: 'background.paper',
                        position: 'relative', overflow: 'hidden', minHeight: 500, display: 'flex', flexDirection: 'column', justifyContent: 'center'
                    }}
                >
                    {/* ------------------------------------------------------ */}
                    {/* LOADING OVERLAY (Replaces Form when active)            */}
                    {/* ------------------------------------------------------ */}
                    {loadingStage !== 'idle' ? (
                        <Fade in={true}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'center' }}>
                                
                                <Typography variant="h5" fontWeight={700} gutterBottom sx={{ mb: 6 }}>
                                    {loadingStage === 'success' ? 'Research Complete!' : 'Market Intelligence Agent Running...'}
                                </Typography>

                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 4 }}>
                                    
                                    {/* AGENT 1: SCRAPER */}
                                    <StatusCircle 
                                        icon={PublicIcon} 
                                        label="Agent 1: Web Scraper" 
                                        active={loadingStage === 'agent1'} 
                                        completed={loadingStage === 'agent2' || loadingStage === 'success'} 
                                    />

                                    {/* Connector Line */}
                                    <Box sx={{ width: 60, height: 4, bgcolor: loadingStage === 'agent2' || loadingStage === 'success' ? '#4caf50' : 'grey.200', transition: 'all 1s ease' }} />

                                    {/* AGENT 2: ANALYST */}
                                    <StatusCircle 
                                        icon={PsychologyIcon} 
                                        label="Agent 2: AI Analyst" 
                                        active={loadingStage === 'agent2'} 
                                        completed={loadingStage === 'success'} 
                                    />
                                </Box>

                                <Typography variant="body1" color="text.secondary" sx={{ mt: 2, height: 24, transition: 'all 0.3s ease' }}>
                                    {loadingStage === 'agent1' && `Scanning sources for "${companyName}"...`}
                                    {loadingStage === 'agent2' && "Synthesizing data and extracting insights..."}
                                    {loadingStage === 'success' && "Report generated successfully!"}
                                </Typography>

                            </Box>
                        </Fade>
                    ) : (
                        /* ------------------------------------------------------ */
                        /* INPUT FORM (Visible when idle)                         */
                        /* ------------------------------------------------------ */
                        <Fade in={true}>
                            <Box>
                                <Typography variant="h5" component="h1" align="center" sx={{ mb: 1, fontWeight: 600, color: 'text.primary' }}>
                                    Market Research Agent
                                </Typography>
                                <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 4 }}>
                                    Enter the target company and data points you need
                                </Typography>

                                {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

                                <Box sx={{ mb: 3 }}>
                                    <TextField
                                        fullWidth label="Company Name"
                                        value={companyName} onChange={(e) => setCompanyName(e.target.value)}
                                        placeholder="e.g. Version 1, Google, Microsoft"
                                        variant="outlined" InputLabelProps={{ shrink: true }}
                                    />
                                </Box>

                                <Box sx={{ mb: 4 }}>
                                    <TextField
                                        fullWidth label="Data Requirements"
                                        value={dataRequirements} onChange={(e) => setDataRequirements(e.target.value)}
                                        placeholder="e.g. Who is the CEO and what is their email address?"
                                        multiline rows={4} variant="outlined" InputLabelProps={{ shrink: true }}
                                    />
                                </Box>

                                <Button
                                    variant="contained" size="large" fullWidth
                                    onClick={handleSubmit}
                                    disabled={!companyName || !dataRequirements}
                                    sx={{ py: 1.8, fontSize: '1rem', fontWeight: 700 }}
                                >
                                    Start Research
                                </Button>
                            </Box>
                        </Fade>
                    )}
                </Paper>
            </Box>
        </Container>
    );
};

export default InputPage;