import React, { useState, useEffect, useRef } from 'react';
import { Box, Button, Typography, Container, Paper, TextField, Alert, Fade } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PublicIcon from '@mui/icons-material/Public'; // Agent 1 Icon
import PsychologyIcon from '@mui/icons-material/Psychology'; // Agent 2 Icon
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'; // Agent 3 Icon
import CheckCircleIcon from '@mui/icons-material/CheckCircle'; // Success Icon

const InputPage: React.FC = () => {
    const [companyName, setCompanyName] = useState('');
    const [dataRequirements, setDataRequirements] = useState('');
    const [loadingStage, setLoadingStage] = useState<'idle' | 'agent1' | 'agent2' | 'agent3' | 'success'>('idle');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    // Timers ref to clear them if component unmounts or request finishes early
    // const transitionTimer = useRef<NodeJS.Timeout | null>(null);

    const [enableComparison, setEnableComparison] = useState(false);
    const [competitors, setCompetitors] = useState('');



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

    // --- LOGGING STATES ---
    const [logs, setLogs] = useState<string[]>([]);

    // Auto-scroll to bottom of logs
    const logsEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const handleSubmit = async () => {
        setLoadingStage('agent1');
        setError(null);
        setLogs([]);

        try {
            const response = await fetch('http://54.210.254.63:8000/api/research/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: companyName,
                    requirements: dataRequirements,
                    enable_comparison: enableComparison,
                    competitor_names: competitors
                }),
            });

            if (!response.ok) throw new Error('Failed to connect to the Agent.');
            if (!response.body) throw new Error('No response body received.');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // Split by double newline (SSE standard separator)
                const events = chunk.split('\n\n');

                for (const eventStr of events) {
                    if (!eventStr.trim().startsWith('data: ')) continue;

                    try {
                        const jsonStr = eventStr.replace('data: ', '').trim();
                        if (!jsonStr) continue;

                        const event = JSON.parse(jsonStr);

                        if (event.type === 'log') {
                            setLogs(prev => [...prev, event.message]);
                            // Update stage based on message keywords (Simple heuristics)
                            if (event.message.includes("Agent 2")) setLoadingStage('agent2');
                            if (event.message.includes("Agent 3")) setLoadingStage('agent3');
                        }
                        else if (event.type === 'complete') {
                            setLoadingStage('success');
                            // Delay navigation slightly to show success
                            setTimeout(() => {
                                navigate('/results', {
                                    state: {
                                        apiResponse: event.payload,
                                        timestamp: new Date().toISOString()
                                    }
                                });
                            }, 1000);
                            return; // Stop processing
                        }
                        else if (event.type === 'error') {
                            throw new Error(event.message);
                        }

                    } catch (e) {
                        console.warn("Error parsing stream event:", e);
                    }
                }
            }

            // CHECK: Did we finish successfully?
            if (loadingStage !== 'success') {
                // Check if we probably have a silent failure
                throw new Error("Stream connection checked out early. Agent stopped unexpectedly.");
            }

        } catch (err: any) {
            console.error("API Error:", err);
            setError(err.message || "Something went wrong.");
            setLoadingStage('idle');
        }
    };

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
                                        completed={loadingStage === 'agent3' || loadingStage === 'success'}
                                    />

                                    {/* Connector Line 2 (Only if Comparison Enabled) */}
                                    {enableComparison && (
                                        <>
                                            <Box sx={{ width: 60, height: 4, bgcolor: loadingStage === 'agent3' || loadingStage === 'success' ? '#4caf50' : 'grey.200', transition: 'all 1s ease' }} />
                                            {/* AGENT 3: COMPARATOR */}
                                            <StatusCircle
                                                icon={CompareArrowsIcon}
                                                label="Agent 3: Comparator"
                                                active={loadingStage === 'agent3'}
                                                completed={loadingStage === 'success'}
                                            />
                                        </>
                                    )}
                                </Box>

                                {/* LOGGING WINDOW - SINGLE LINE UPDATE */}
                                <Box sx={{
                                    width: '100%',
                                    minHeight: 60, // Fixed height to prevent layout jump
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    textAlign: 'center',
                                    mt: 2,
                                    px: 2
                                }}>
                                    {loadingStage === 'success' ? (
                                        <Typography color="success.main" fontWeight={700} variant="h6">
                                            ✓ Research Complete.
                                        </Typography>
                                    ) : (
                                        <Typography
                                            key={logs.length} // Key change triggers animation restart
                                            color="primary.main"
                                            fontWeight={600}
                                            sx={{
                                                animation: 'fadeIn 0.5s ease-in-out',
                                                fontSize: '1.1rem',
                                                textShadow: '0px 0px 1px rgba(0,0,0,0.1)'
                                            }}
                                        >
                                            {logs.length > 0 ? logs[logs.length - 1] : "Initializing..."}
                                        </Typography>
                                    )}
                                </Box>
                                <style>
                                    {`@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }`}
                                </style>

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

                                <TextField
                                    fullWidth label="Data Requirements"
                                    value={dataRequirements} onChange={(e) => setDataRequirements(e.target.value)}
                                    placeholder="e.g. Who is the CEO and what is their email address?"
                                    multiline rows={4} variant="outlined" InputLabelProps={{ shrink: true }}
                                />


                                {/* COMPARISON TOGGLE - MOVED UP */}
                                <Box sx={{ mt: 4, mb: 3, p: 2, bgcolor: '#f9fafb', borderRadius: 2, border: '1px solid #eee' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        <input
                                            type="checkbox"
                                            id="enableComp"
                                            checked={enableComparison}
                                            onChange={(e) => setEnableComparison(e.target.checked)}
                                            style={{ width: 18, height: 18, marginRight: 10, cursor: 'pointer' }}
                                        />
                                        <label htmlFor="enableComp" style={{ cursor: 'pointer', fontWeight: 600, color: '#333' }}>
                                            Enable Company Comparison
                                        </label>
                                    </Box>

                                    {enableComparison && (
                                        <Fade in={true}>
                                            <Box sx={{ mt: 2 }}>
                                                <TextField
                                                    fullWidth
                                                    size="small"
                                                    label="Competitors (Optional)"
                                                    placeholder="Leave empty to auto-detect top competitors"
                                                    value={competitors}
                                                    onChange={(e) => setCompetitors(e.target.value)}
                                                />
                                            </Box>
                                        </Fade>
                                    )}
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
        </Container >
    );
};

export default InputPage;