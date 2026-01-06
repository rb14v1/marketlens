import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import {
    Box, Container, Typography, Card, CardContent, Grid, Button,
    Menu, MenuItem, ListItemIcon, Dialog, DialogTitle, DialogContent,
    List, ListItem, ListItemText, Paper, TextField
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

    // 2. DESTRUCTURE DATA
    const { company, final_answer, scraped_sources } = apiResponse;
    const { summary, extracted_data } = final_answer || { summary: "Analysis failed or incomplete.", extracted_data: {} };

    // --- NEW HELPER FUNCTION ---
    // Checks if a value is meaningful. Returns false for "not provided", "unknown", etc.
    const isValidValue = (val: any) => {
        if (!val) return false;
        const s = String(val).toLowerCase();
        return !s.includes('not provided') &&
            !s.includes('no data') &&
            !s.includes('unknown') &&
            !s.includes('n/a');
    };

    // 3. FLATTEN DATA FOR DISPLAY
    // We compute the initial metrics ONCE, then copy them to state.
    // This allows us to edit them.
    const getInitialMetrics = () => {
        let initialMetrics: Record<string, string> = {};
        if (extracted_data) {
            if (extracted_data.Key_Answer) {
                if (isValidValue(extracted_data.Key_Answer) && typeof extracted_data.Key_Answer !== 'object') {
                    initialMetrics["Answer"] = String(extracted_data.Key_Answer);
                } else if (typeof extracted_data.Key_Answer === 'object') {
                    Object.entries(extracted_data.Key_Answer).forEach(([k, v]) => {
                        if ((typeof v === 'string' || typeof v === 'number') && isValidValue(v)) {
                            initialMetrics[k] = String(v);
                        }
                    });
                }
            }
            if (Object.keys(initialMetrics).length === 0) {
                Object.entries(extracted_data).forEach(([k, v]) => {
                    if (k !== 'Details' && k !== 'Summary' && k !== 'Key_Answer' && typeof v === 'string' && v.length < 100 && isValidValue(v)) {
                        initialMetrics[k] = v;
                    }
                });
            }
        }
        return initialMetrics;
    };

    // --- STATE FOR EDITABLE FIELDS ---
    // Initialize with the data we parsed
    const [metrics, setMetrics] = useState<Record<string, string>>(getInitialMetrics);
    const [editableSummary, setEditableSummary] = useState<string>(summary || "");
    const [editableDetails, setEditableDetails] = useState<string>(
        (extracted_data && extracted_data.Details && typeof extracted_data.Details === 'string') ? extracted_data.Details : ""
    );

    // Toggle for Edit Mode
    const [isEditMode, setIsEditMode] = useState(false);

    // 4. SMART ICON HELPER
    const getIconForKey = (key: string) => {
        const k = key.toLowerCase();
        if (k.includes('ceo') || k.includes('leader') || k.includes('founder')) return <PersonIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('revenue') || k.includes('worth') || k.includes('financial')) return <MonetizationOnIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('hq') || k.includes('location') || k.includes('headquarter')) return <BusinessIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('date') || k.includes('year') || k.includes('est')) return <TimelineIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('competitor') || k.includes('rival')) return <GroupsIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('industry') || k.includes('sector')) return <DomainIcon sx={{ color: '#4caf50' }} />;
        if (k.includes('public') || k.includes('private') || k.includes('type')) return <PublicIcon sx={{ color: '#4caf50' }} />;
        return <LightbulbIcon sx={{ color: '#4caf50' }} />;
    };

    // 5. VIEW SOURCES DIALOG STATE
    const [openSources, setOpenSources] = useState(false);

    // 6. DOWNLOAD MENU & PDF LOGIC
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);

    const handleClose = () => {
        setAnchorEl(null);
    };

    const handleDownload = (format: string) => {
        if (format === 'PDF') {
            const doc = new jsPDF();
            const pageWidth = doc.internal.pageSize.width;

            // Header
            doc.setFontSize(20);
            doc.setTextColor(0, 150, 136); // Teal color
            doc.text(`Market Intelligence Report: ${company}`, 14, 20);

            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 28);

            let yPos = 40;

            // Key Stats Table (Using metrics state)
            if (Object.keys(metrics).length > 0) {
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Key Statistics", 14, yPos);
                yPos += 5;

                const statsData = Object.entries(metrics).map(([k, v]) => [k.replace(/_/g, ' '), v]);

                autoTable(doc, {
                    startY: yPos,
                    head: [['Metric', 'Value']],
                    body: statsData,
                    theme: 'striped',
                    headStyles: { fillColor: [0, 150, 136] },
                    margin: { left: 14 }
                });

                // Update yPos based on where the table ended
                yPos = (doc as any).lastAutoTable.finalY + 15;
            }

            // Executive Summary (Using editableSummary state)
            doc.setFontSize(14);
            doc.setTextColor(0);
            doc.text("Executive Summary", 14, yPos);
            yPos += 7;

            doc.setFontSize(11);
            doc.setTextColor(60);
            const summaryLines = doc.splitTextToSize(editableSummary || "No summary available.", pageWidth - 28);
            doc.text(summaryLines, 14, yPos);
            yPos += (summaryLines.length * 5) + 15;

            // Details (Using editableDetails state)
            if (editableDetails) {
                const detailLines = doc.splitTextToSize(editableDetails, pageWidth - 28);
                // Check page break
                if (yPos + (detailLines.length * 5) > 270) { doc.addPage(); yPos = 20; }
                doc.text(detailLines, 14, yPos);
                yPos += (detailLines.length * 5) + 15;
            }

            // Sources
            if (scraped_sources && scraped_sources.length > 0) {
                // Check if we need a new page
                if (yPos > 250) { doc.addPage(); yPos = 20; }

                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Verified Sources", 14, yPos);
                yPos += 7;

                doc.setFontSize(10);
                doc.setTextColor(100);

                scraped_sources.forEach((src: string) => {
                    doc.text(`- ${src}`, 14, yPos);
                    yPos += 5;
                });
            }

            doc.save(`${company}_Report.pdf`);
        } else {
            alert(`Downloading report for ${company} in ${format} format is coming soon!`);
        }
        handleClose();
    };

    // Helper to update a specific metric
    const handleMetricChange = (key: string, newValue: string) => {
        setMetrics(prev => ({
            ...prev,
            [key]: newValue
        }));
    };

    return (
        <Container maxWidth="lg" sx={{ pb: 8, mt: 4 }}>

            {/* TOP HEADER */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate('/')}
                    sx={{ textTransform: 'none', color: 'text.secondary', '&:hover': { color: 'primary.main', bgcolor: 'transparent' } }}
                >
                    Back to Search
                </Button>
                <Typography variant="caption" color="primary.main" fontWeight={700} letterSpacing={1}>
                    MARKET INTELLIGENCE REPORT
                </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1, mb: 4 }}>
                <Typography variant="h2" component="h1" sx={{ fontWeight: 800, textTransform: 'lowercase' }}>
                    {company}
                </Typography>

                <Box sx={{ display: 'flex', gap: 2 }}>

                    {/* EDIT TOGGLE BUTTON */}
                    <Button
                        variant={isEditMode ? "contained" : "outlined"}
                        color={isEditMode ? "primary" : "inherit"}
                        startIcon={isEditMode ? <CheckIcon /> : <EditIcon />}
                        onClick={() => setIsEditMode(!isEditMode)}
                        sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, borderColor: '#ccc' }}
                    >
                        {isEditMode ? "Save Changes" : "Edit Report"}
                    </Button>

                    {/* VIEW SOURCES BUTTON */}
                    <Button
                        variant="outlined"
                        startIcon={<LinkIcon />}
                        onClick={() => setOpenSources(true)}
                        sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
                    >
                        View Sources
                    </Button>

                    {/* DOWNLOAD BUTTON */}
                    <Button
                        variant="contained"
                        color="secondary"
                        startIcon={<DownloadIcon />}
                        onClick={(e) => setAnchorEl(e.currentTarget)}
                        sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, bgcolor: '#00C4CC', '&:hover': { bgcolor: '#00afb5' } }}
                    >
                        Download Report
                    </Button>
                    <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
                        <MenuItem onClick={() => handleDownload('PDF')}>
                            <ListItemIcon><PictureAsPdfIcon fontSize="small" /></ListItemIcon> PDF Report
                        </MenuItem>
                        <MenuItem onClick={() => handleDownload('DOCX')}>
                            <ListItemIcon><DescriptionIcon fontSize="small" /></ListItemIcon> Word Document
                        </MenuItem>
                    </Menu>
                </Box>
            </Box>

            {/* SOURCES DIALOG POPUP */}
            <Dialog
                open={openSources}
                onClose={() => setOpenSources(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle sx={{ fontWeight: 700 }}>Data Sources Used</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        The following sources were analyzed to generate this report:
                    </Typography>
                    <List>
                        {scraped_sources && scraped_sources.length > 0 ? (
                            scraped_sources.map((src: string, index: number) => (
                                <ListItem key={index} disablePadding sx={{ py: 1 }}>
                                    <ListItemIcon sx={{ minWidth: 36 }}>
                                        <ArticleIcon fontSize="small" color="primary" />
                                    </ListItemIcon>
                                    <ListItemText primary={src} />
                                </ListItem>
                            ))
                        ) : (
                            <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                                Sources not explicitly listed.
                            </Typography>
                        )}
                    </List>
                </DialogContent>
            </Dialog>

            {/* DYNAMIC CARDS GRID */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {Object.entries(metrics).map(([key, value], index) => (
                    <Grid item xs={12} md={4} key={index}>
                        <Card elevation={0} sx={{
                            height: '100%',
                            border: '1px solid #eee',
                            borderRadius: 4,
                            p: 1
                        }}>
                            <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                                <Box sx={{
                                    bgcolor: '#f5f9f9',
                                    p: 1.5,
                                    borderRadius: 3,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}>
                                    {getIconForKey(key)}
                                </Box>
                                <Box sx={{ width: '100%' }}>
                                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5, textTransform: 'uppercase' }}>
                                        {key.replace(/_/g, ' ')}
                                    </Typography>

                                    {isEditMode ? (
                                        <TextField
                                            fullWidth
                                            variant="standard"
                                            value={value}
                                            onChange={(e) => handleMetricChange(key, e.target.value)}
                                            InputProps={{ style: { fontSize: '1.25rem', fontWeight: 700 } }}
                                        />
                                    ) : (
                                        <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.2 }}>
                                            {value}
                                        </Typography>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}

                {Object.keys(metrics).length === 0 && (
                    <Grid item xs={12}>
                        <Typography color="text.secondary" fontStyle="italic">
                            No specific metrics extracted. See summary below.
                        </Typography>
                    </Grid>
                )}
            </Grid>


            {/* EXECUTIVE SUMMARY */}
            <Card elevation={0} sx={{ border: '1px solid #eee', borderRadius: 4 }}>
                <CardContent sx={{ p: 4 }}>
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
                        Executive Summary
                    </Typography>

                    {isEditMode ? (
                        <TextField
                            fullWidth
                            multiline
                            minRows={4}
                            variant="outlined"
                            value={editableSummary}
                            onChange={(e) => setEditableSummary(e.target.value)}
                            sx={{ mb: 2 }}
                        />
                    ) : (
                        <Typography paragraph sx={{ color: 'text.secondary', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
                            {editableSummary}
                        </Typography>
                    )}

                    {/* Details Section - also editable */}
                    {editableDetails && (
                        isEditMode ? (
                            <TextField
                                fullWidth
                                multiline
                                minRows={2}
                                variant="outlined"
                                label="Additional Details"
                                value={editableDetails}
                                onChange={(e) => setEditableDetails(e.target.value)}
                                sx={{ mt: 2 }}
                            />
                        ) : (
                            <Typography paragraph sx={{ color: 'text.secondary', lineHeight: 1.7, mt: 2 }}>
                                {editableDetails}
                            </Typography>
                        )
                    )}
                </CardContent>
            </Card>


        </Container>
    );
};

export default ResultPage;