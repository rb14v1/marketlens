import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import {
    Box, Container, Typography, Card, CardContent, Grid, Button,
    Menu, MenuItem, ListItemIcon, Dialog, DialogTitle, DialogContent,
    List, ListItem, ListItemText, TextField, Avatar
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import LinkIcon from '@mui/icons-material/Link';
import TimelineIcon from '@mui/icons-material/Timeline';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';
import DomainIcon from '@mui/icons-material/Domain';
import PublicIcon from '@mui/icons-material/Public';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import GroupsIcon from '@mui/icons-material/Groups';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DescriptionIcon from '@mui/icons-material/Description';
import ArticleIcon from '@mui/icons-material/Article';
import EditIcon from '@mui/icons-material/Edit';
import CheckIcon from '@mui/icons-material/Check';

const ResultPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // 1. GET DATA
    const { apiResponse } = location.state || {};

    // Safety Check
    if (!apiResponse || !apiResponse.final_answer) {
        return (
            <Container maxWidth="md" sx={{ mt: 10, textAlign: 'center' }}>
                <Typography variant="h5" color="error">No Data Found</Typography>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
                    Go Back
                </Button>
            </Container>
        );
    }

    // --- PDF TEXT CLEANER ---
    const cleanTextForPDF = (text: string) => {
        if (!text) return "";
        return text
            .replace(/₹/g, 'Rs. ')   // Replace Rupee symbol with 'Rs.'
            .replace(/•/g, '- ')    // Replace bullet points with dash
            .replace(/[^\x00-\x7F]/g, ""); // Remove other non-ASCII characters
    };

    // 2. DESTRUCTURE DATA
    const { company, final_answer, scraped_sources, comparison } = apiResponse;
    const { summary, extracted_data } = final_answer || { summary: "Analysis failed or incomplete.", extracted_data: {} };

    // --- HELPER FUNCTIONS ---
    const isValidValue = (val: any) => {
        if (!val) return false;
        const s = String(val).toLowerCase();
        return !s.includes('not provided') &&
            !s.includes('no data') &&
            !s.includes('unknown') &&
            !s.includes('n/a');
    };

    const processValue = (val: any): string | null => {
        if (Array.isArray(val)) return val.join(', ');
        if (typeof val === 'string' || typeof val === 'number') return String(val);
        return null;
    };

    // 3. FLATTEN DATA (RESTORED BASE CODE LOGIC)
    const getInitialMetrics = () => {
        let initialMetrics: Record<string, string> = {};

        if (extracted_data) {
            // STRATEGY 1: Check "Key_Answer" First (High Priority)
            if (extracted_data.Key_Answer) {
                if (isValidValue(extracted_data.Key_Answer) && typeof extracted_data.Key_Answer !== 'object') {
                    initialMetrics["Answer"] = String(extracted_data.Key_Answer);
                }
                else if (typeof extracted_data.Key_Answer === 'object' && !Array.isArray(extracted_data.Key_Answer)) {
                    Object.entries(extracted_data.Key_Answer).forEach(([k, v]) => {
                        const strVal = processValue(v);
                        if (strVal && isValidValue(strVal)) {
                            initialMetrics[k] = strVal;
                        }
                    });
                }
            }

            // STRATEGY 2: Fallback to General Data
            if (Object.keys(initialMetrics).length === 0) {
                Object.entries(extracted_data).forEach(([k, v]) => {
                    if (k === 'Details' || k === 'Summary' || k === 'Key_Answer') return;
                    const strVal = processValue(v);
                    if (strVal && strVal.length < 200 && isValidValue(strVal)) {
                        initialMetrics[k] = strVal;
                    }
                });
            }
        }
        return initialMetrics;
    };

    // --- STATE ---
    const [metrics, setMetrics] = useState<Record<string, string>>(getInitialMetrics);
    const [editableSummary, setEditableSummary] = useState<string>(summary || "");
    const [editableDetails, setEditableDetails] = useState<string>(
        (extracted_data && extracted_data.Details && typeof extracted_data.Details === 'string') ? extracted_data.Details : ""
    );
    const [isEditMode, setIsEditMode] = useState(false);
    const [openSources, setOpenSources] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);

    // --- ICONS ---
    const getIconForKey = (key: string) => {
        const k = key.toLowerCase();
        if (k.includes('ceo') || k.includes('leader') || k.includes('founder') || k.includes('answer')) return <PersonIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('revenue') || k.includes('worth') || k.includes('financial')) return <MonetizationOnIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('hq') || k.includes('location')) return <BusinessIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('date') || k.includes('year')) return <TimelineIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('competitor')) return <GroupsIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('industry')) return <DomainIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('public') || k.includes('private')) return <PublicIcon sx={{ color: '#4caf50' }} />;
        return <LightbulbIcon sx={{ color: '#4caf50' }} />;
    };

    // --- DOWNLOAD HANDLER ---
    const handleClose = () => setAnchorEl(null);
    const handleDownload = (format: string) => {
        if (format === 'PDF') {
            const doc = new jsPDF();
            const pageWidth = doc.internal.pageSize.width;

            // Title
            doc.setFontSize(20);
            doc.setTextColor(0, 150, 136);
            doc.text(`Market Intelligence Report: ${company}`, 14, 20);

            // Date
            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 28);

            let yPos = 40;

            // ... inside handleDownload ...

            // Metrics Table
            if (Object.keys(metrics).length > 0) {
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Key Statistics", 14, yPos);
                yPos += 5;

                // 🟢 APPLY CLEANER HERE
                const statsData = Object.entries(metrics).map(([k, v]) => [
                    cleanTextForPDF(k.replace(/_/g, ' ')),
                    cleanTextForPDF(v)
                ]);

                autoTable(doc, {
                    startY: yPos,
                    head: [['Metric', 'Value']],
                    body: statsData,
                    theme: 'striped',
                    headStyles: { fillColor: [0, 150, 136] },
                    margin: { left: 14 }
                });
                yPos = (doc as any).lastAutoTable.finalY + 15;
            }

            // Summary
            doc.setFontSize(14);
            doc.setTextColor(0);
            doc.text("Executive Summary", 14, yPos);
            yPos += 7;

            doc.setFontSize(11);
            doc.setTextColor(60);

            // 🟢 APPLY CLEANER HERE TOO
            const cleanSummary = cleanTextForPDF(editableSummary || "No summary available.");
            const summaryLines = doc.splitTextToSize(cleanSummary, pageWidth - 28);

            doc.text(summaryLines, 14, yPos);
            yPos += (summaryLines.length * 5) + 15;

            // ... (rest of the code remains the same)

            // Details
            if (editableDetails) {
                const detailLines = doc.splitTextToSize(editableDetails, pageWidth - 28);
                if (yPos + (detailLines.length * 5) > 270) { doc.addPage(); yPos = 20; }
                doc.text(detailLines, 14, yPos);
                yPos += (detailLines.length * 5) + 15;
            }

            // Sources
            if (scraped_sources && scraped_sources.length > 0) {
                if (yPos > 250) { doc.addPage(); yPos = 20; }
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Verified Sources", 14, yPos);
                yPos += 7;
                doc.setFontSize(10);
                doc.setTextColor(100);
                scraped_sources.forEach((src: any) => {
                    const title = typeof src === 'string' ? src : src.title || src.url;
                    doc.text(`- ${title}`, 14, yPos);
                    yPos += 5;
                });
            }

            doc.save(`${company}_Report.pdf`);
        }
        handleClose();
    };

    const handleMetricChange = (key: string, newValue: string) => {
        setMetrics(prev => ({ ...prev, [key]: newValue }));
    };

    return (
        <Container maxWidth="lg" sx={{ pb: 8, mt: 4 }}>
            {/* NAVIGATION & TABS */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, borderBottom: '1px solid #eee', pb: 2 }}>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ textTransform: 'none', color: 'text.secondary', fontWeight: 600, mr: 2 }}>
                    Back
                </Button>
                <Box sx={{ display: 'flex', gap: 1, bgcolor: '#f4f6f8', p: 0.5, borderRadius: 2 }}>
                    <Button variant="contained" sx={{ textTransform: 'none', fontWeight: 700, boxShadow: 'none', bgcolor: 'white', color: 'primary.main', '&:hover': { bgcolor: 'white' } }}>
                        Market Intelligence Report
                    </Button>
                    {comparison && (
                        <Button variant="text" onClick={() => navigate('/comparison', { state: { apiResponse } })} sx={{ textTransform: 'none', fontWeight: 600, color: 'text.secondary' }}>
                            Competitive Report
                        </Button>
                    )}
                </Box>
            </Box>

            {/* HEADER AREA */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1, mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>

                    {/* 🟢 REPLACED LOGO WITH GENERIC AVATAR */}
                    <Avatar
                        sx={{
                            width: 72,
                            height: 72,
                            bgcolor: '#009688', // Teal color
                            fontSize: '2rem',
                            fontWeight: 700,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                        }}
                    >
                        {company ? company.charAt(0).toUpperCase() : 'C'}
                    </Avatar>

                    <Box>
                        <Typography variant="h2" component="h1" sx={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: -1, lineHeight: 1 }}>
                            {company}
                        </Typography>
                        {apiResponse?.scraped_sources?.[0] && (
                            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                                Source: {apiResponse.scraped_sources[0].title || apiResponse.scraped_sources[0].url || "Web Search"}
                            </Typography>
                        )}
                    </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button variant={isEditMode ? "contained" : "outlined"} color={isEditMode ? "primary" : "inherit"} startIcon={isEditMode ? <CheckIcon /> : <EditIcon />} onClick={() => setIsEditMode(!isEditMode)} sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}>
                        {isEditMode ? "Save Changes" : "Edit Report"}
                    </Button>
                    <Button variant="outlined" startIcon={<LinkIcon />} onClick={() => setOpenSources(true)} sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}>
                        View Sources
                    </Button>
                    <Button variant="contained" color="secondary" startIcon={<DownloadIcon />} onClick={(e) => setAnchorEl(e.currentTarget)} sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, bgcolor: '#00C4CC' }}>
                        Download Report
                    </Button>
                    <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
                        <MenuItem onClick={() => handleDownload('PDF')}><ListItemIcon><PictureAsPdfIcon fontSize="small" /></ListItemIcon> PDF Report</MenuItem>
                        <MenuItem onClick={() => handleDownload('DOCX')}><ListItemIcon><DescriptionIcon fontSize="small" /></ListItemIcon> Word Document</MenuItem>
                    </Menu>
                </Box>
            </Box>

            {/* METRICS GRID */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {Object.entries(metrics).map(([key, value], index) => (
                    <Grid item xs={12} md={4} key={index}>
                        <Card elevation={0} sx={{ height: '100%', border: '1px solid #eee', borderRadius: 4, p: 1 }}>
                            <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                                <Box sx={{ bgcolor: '#f5f9f9', p: 1.5, borderRadius: 3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    {getIconForKey(key)}
                                </Box>
                                <Box sx={{ width: '100%' }}>
                                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5, textTransform: 'uppercase' }}>
                                        {key.replace(/_/g, ' ')}
                                    </Typography>
                                    {isEditMode ? (
                                        <TextField fullWidth variant="standard" value={value} onChange={(e) => handleMetricChange(key, e.target.value)} InputProps={{ style: { fontSize: '1.25rem', fontWeight: 700 } }} />
                                    ) : (
                                        <Typography
                                            variant="body1"
                                            fontWeight={600}
                                            sx={{
                                                lineHeight: 1.6,
                                                whiteSpace: 'pre-line',  // <--- THIS IS THE MAGIC FIX
                                                wordBreak: 'break-word'
                                            }}
                                        >
                                            {value}
                                        </Typography>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
                {Object.keys(metrics).length === 0 && (
                    <Grid item xs={12}><Typography color="text.secondary" fontStyle="italic">No specific metrics extracted. See summary below.</Typography></Grid>
                )}
            </Grid>

            {/* EXECUTIVE SUMMARY */}
            <Card elevation={0} sx={{ border: '1px solid #eee', borderRadius: 4 }}>
                <CardContent sx={{ p: 4 }}>
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Executive Summary</Typography>
                    {isEditMode ? (
                        <TextField fullWidth multiline minRows={4} variant="outlined" value={editableSummary} onChange={(e) => setEditableSummary(e.target.value)} sx={{ mb: 2 }} />
                    ) : (
                        <Typography paragraph sx={{ color: 'text.secondary', lineHeight: 1.7, whiteSpace: 'pre-line' }}>{editableSummary}</Typography>
                    )}

                    {editableDetails && (
                        isEditMode ? (
                            <TextField fullWidth multiline minRows={2} variant="outlined" label="Additional Details" value={editableDetails} onChange={(e) => setEditableDetails(e.target.value)} sx={{ mt: 2 }} />
                        ) : (
                            <Typography paragraph sx={{ color: 'text.secondary', lineHeight: 1.7, mt: 2 }}>{editableDetails}</Typography>
                        )
                    )}
                </CardContent>
            </Card>

            {/* SOURCES DIALOG */}
            <Dialog open={openSources} onClose={() => setOpenSources(false)} maxWidth="sm" fullWidth>
                <DialogTitle sx={{ fontWeight: 700 }}>Data Sources Used</DialogTitle>
                <DialogContent>
                    <List>
                        {scraped_sources && scraped_sources.length > 0 ? (
                            scraped_sources.map((src: any, index: number) => (
                                <ListItem key={index} component="a" href={typeof src === 'string' ? '#' : src.url} target="_blank" disablePadding sx={{ py: 1, textDecoration: 'none', color: 'inherit', '&:hover': { bgcolor: 'action.hover' } }}>
                                    <ListItemIcon sx={{ minWidth: 36 }}><ArticleIcon fontSize="small" color="primary" /></ListItemIcon>
                                    <ListItemText
                                        primary={typeof src === 'string' ? src : src.title}
                                        secondary={typeof src === 'string' ? null : src.url}
                                        primaryTypographyProps={{ fontWeight: 600, color: 'primary.main' }}
                                        secondaryTypographyProps={{ noWrap: true, display: 'block' }}
                                    />
                                </ListItem>
                            ))
                        ) : (
                            <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>Sources not explicitly listed.</Typography>
                        )}
                    </List>
                </DialogContent>
            </Dialog>
        </Container>
    );
};

export default ResultPage;