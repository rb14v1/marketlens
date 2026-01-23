import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    Container, Box, Typography, Button, Avatar,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    List, ListItem, ListItemIcon, ListItemText, Paper, TextField,
    Dialog, DialogTitle, DialogContent, Menu, MenuItem
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckIcon from '@mui/icons-material/Check';
import EditIcon from '@mui/icons-material/Edit';
import LinkIcon from '@mui/icons-material/Link';
import DownloadIcon from '@mui/icons-material/Download';
import ArticleIcon from '@mui/icons-material/Article';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Fix for autoTable typescript error if it occurs
const autoTableAny = autoTable as any;

const ComparisonPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    
    // EXTRACT DATA
    const { apiResponse } = location.state || {};
    const { comparison, company, scraped_sources, final_answer } = apiResponse || {};

    // --- STATE MANAGEMENT ---
    const [isEditMode, setIsEditMode] = useState(false);
    const [swotTable, setSwotTable] = useState<any[]>(comparison?.swot_table || []);
    const [openSources, setOpenSources] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    // --- DATA SAFETY CHECK ---
    if (!comparison) {
        return (
            <Container maxWidth="md" sx={{ mt: 10, textAlign: 'center' }}>
                <Typography variant="h5" color="error">No Comparison Data Found</Typography>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
                    Go Home
                </Button>
            </Container>
        );
    }

    // --- HANDLERS ---
    const handleSwotChange = (rowIndex: number, key: string, value: string) => {
        const newTable = [...swotTable];
        newTable[rowIndex] = { ...newTable[rowIndex], [key]: value };
        setSwotTable(newTable);
    };

    const handleDownload = (format: string) => {
        setAnchorEl(null);
        
        // 1. SWOT ONLY DOWNLOAD (Landscape)
        if (format === 'PDF') {
            const doc = new jsPDF('l'); 

            // Header
            doc.setFontSize(20);
            doc.setTextColor(0, 150, 136);
            doc.text(`Competitive SWOT Analysis: ${company}`, 14, 20);

            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 28);

            let yPos = 40;

            // SWOT Table
            if (swotTable.length > 0) {
                const headers = Object.keys(swotTable[0]).map(h => h.toUpperCase());
                const body = swotTable.map((row: any) => Object.values(row) as string[]);

                autoTableAny(doc, {
                    startY: yPos,
                    head: [headers],
                    body: body,
                    theme: 'grid',
                    headStyles: { fillColor: [0, 150, 136] },
                    styles: { cellWidth: 'auto', overflow: 'linebreak' },
                    margin: { left: 14 }
                });

                yPos = (doc as any).lastAutoTable.finalY + 15;
            }

            // Summary
            if (comparison.market_position_summary) {
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Market Position Summary", 14, yPos);
                yPos += 7;
                doc.setFontSize(11);
                doc.setTextColor(60);
                const lines = doc.splitTextToSize(comparison.market_position_summary, 270);
                doc.text(lines, 14, yPos);
            }

            doc.save(`${company}_SWOT_Comparison.pdf`);
        }
        // 2. FULL MERGED REPORT (Portrait)
        else if (format === 'MERGED') {
            const doc = new jsPDF('p'); 
            const pageWidth = doc.internal.pageSize.width;

            // --- PAGE 1: MARKET INTELLIGENCE ---
            doc.setFontSize(22);
            doc.setTextColor(0, 150, 136);
            doc.text(`Market Intelligence Report: ${company}`, 14, 20);

            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 28);

            let yPos = 40;

            // 1.1 Key Metrics
            const metrics: [string, string][] = [];
            const keyAnswer = final_answer?.extracted_data?.Key_Answer;
            
            if (keyAnswer) {
                if (typeof keyAnswer === 'string') {
                    metrics.push(["Key Finding", keyAnswer]);
                } else if (typeof keyAnswer === 'object' && !Array.isArray(keyAnswer)) {
                    Object.entries(keyAnswer).forEach(([k, v]) => {
                        if (v && (typeof v === 'string' || typeof v === 'number')) {
                            metrics.push([k.replace(/_/g, ' '), String(v)]);
                        }
                    });
                }
            }

            if (metrics.length > 0) {
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Key Statistics", 14, yPos);
                yPos += 5;

                autoTableAny(doc, {
                    startY: yPos,
                    head: [['Metric', 'Value']],
                    body: metrics,
                    theme: 'striped',
                    headStyles: { fillColor: [0, 150, 136] },
                    margin: { left: 14 }
                });
                yPos = (doc as any).lastAutoTable.finalY + 15;
            }

            // 1.2 Executive Summary
            const summary = final_answer?.summary;
            if (summary) {
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Executive Summary", 14, yPos);
                yPos += 7;
                doc.setFontSize(11);
                doc.setTextColor(60);
                const lines = doc.splitTextToSize(summary, pageWidth - 28);
                doc.text(lines, 14, yPos);
            }

            // --- PAGE 2: COMPETITIVE ANALYSIS ---
            doc.addPage();
            doc.setPage(2); 

            yPos = 20;
            doc.setFontSize(20);
            doc.setTextColor(0, 150, 136);
            doc.text(`Competitive SWOT Analysis`, 14, yPos);
            yPos += 20;

            // 2.1 SWOT Table
            if (swotTable.length > 0) {
                const headers = Object.keys(swotTable[0]).map(h => h.toUpperCase());
                const body = swotTable.map((row: any) => Object.values(row) as string[]);

                autoTableAny(doc, {
                    startY: yPos,
                    head: [headers],
                    body: body,
                    theme: 'grid',
                    headStyles: { fillColor: [0, 150, 136] },
                    styles: { cellWidth: 'auto', overflow: 'linebreak' },
                    margin: { left: 14 }
                });
                yPos = (doc as any).lastAutoTable.finalY + 15;
            }

            // 2.2 Market Position
            if (comparison.market_position_summary) {
                if (yPos > 250) { doc.addPage(); yPos = 20; }
                
                doc.setFontSize(14);
                doc.setTextColor(0);
                doc.text("Market Position Summary", 14, yPos);
                yPos += 7;
                doc.setFontSize(11);
                doc.setTextColor(60);
                const lines = doc.splitTextToSize(comparison.market_position_summary, pageWidth - 28);
                doc.text(lines, 14, yPos);
            }

            doc.save(`${company}_FULL_Report.pdf`);
        }
    };

    return (
        <Container maxWidth="xl" sx={{ pb: 8, mt: 4 }}>

            {/* TOP NAVIGATION */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, borderBottom: '1px solid #eee', pb: 2 }}>
                <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate('/')}
                    sx={{ textTransform: 'none', color: 'text.secondary', fontWeight: 600, mr: 2 }}
                >
                    Back
                </Button>

                <Box sx={{ display: 'flex', gap: 1, bgcolor: '#f4f6f8', p: 0.5, borderRadius: 2 }}>
                    <Button
                        variant="text"
                        onClick={() => navigate('/results', { state: { apiResponse } })}
                        sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            color: 'text.secondary',
                            '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' }
                        }}
                    >
                        Market Intelligence Report
                    </Button>

                    <Button
                        variant="contained"
                        sx={{
                            textTransform: 'none',
                            fontWeight: 700,
                            boxShadow: 'none',
                            bgcolor: 'white',
                            color: 'primary.main',
                            '&:hover': { bgcolor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }
                        }}
                    >
                        Competitive Report
                    </Button>
                </Box>
            </Box>

            {/* TITLE & AVATAR BAR */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1, mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    
                    {/* 🟢 AVATAR LOGO FIX */}
                    <Avatar 
                        sx={{ 
                            width: 64, 
                            height: 64, 
                            bgcolor: '#009688', 
                            fontSize: '1.8rem', 
                            fontWeight: 700,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)' 
                        }}
                    >
                        {company ? company.charAt(0).toUpperCase() : 'C'}
                    </Avatar>

                    <Box>
                        <Typography variant="h2" component="h1" sx={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: -1 }}>
                            {company}
                        </Typography>
                        <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 0, fontWeight: 500 }}>
                            Competitive SWOT Analysis
                        </Typography>
                    </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        startIcon={<ArticleIcon />}
                        variant="outlined"
                        color="inherit"
                        onClick={() => setOpenSources(true)}
                        sx={{ textTransform: 'none' }}
                    >
                        View Sources
                    </Button>

                    <Button
                        startIcon={isEditMode ? <CheckIcon /> : <EditIcon />}
                        variant={isEditMode ? "contained" : "outlined"}
                        onClick={() => setIsEditMode(!isEditMode)}
                        color={isEditMode ? "primary" : "inherit"}
                        sx={{ textTransform: 'none' }}
                    >
                        {isEditMode ? "Done Editing" : "Edit Table"}
                    </Button>

                    <Button
                        startIcon={<DownloadIcon />}
                        variant="contained"
                        onClick={(event) => setAnchorEl(event.currentTarget)}
                        color="primary"
                        sx={{ textTransform: 'none', fontWeight: 700 }}
                    >
                        Download Report
                    </Button>
                    <Menu
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl)}
                        onClose={() => setAnchorEl(null)}
                    >
                        <MenuItem onClick={() => handleDownload('PDF')}>
                            <ListItemIcon><PictureAsPdfIcon fontSize="small" /></ListItemIcon>
                            <ListItemText>Download SWOT PDF</ListItemText>
                        </MenuItem>
                        <MenuItem onClick={() => handleDownload('MERGED')}>
                            <ListItemIcon><PictureAsPdfIcon fontSize="small" color="secondary" /></ListItemIcon>
                            <ListItemText primary="Download Full Report" secondary="Market Analysis + SWOT" />
                        </MenuItem>
                    </Menu>
                </Box>
            </Box>

            {/* SWOT Table Section */}
            <Paper elevation={0} sx={{ p: 0, overflow: 'hidden', border: '1px solid #e0e0e0', borderRadius: 2, mb: 4 }}>
                <TableContainer>
                    <Table size="medium">
                        <TableHead>
                            <TableRow sx={{ bgcolor: '#009688' }}>
                                {swotTable.length > 0 && Object.keys(swotTable[0]).map((header) => (
                                    <TableCell key={header} sx={{ fontWeight: 700, textTransform: 'uppercase', color: 'white', borderRight: '1px solid rgba(255,255,255,0.2)' }}>
                                        {header}
                                    </TableCell>
                                ))}
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {swotTable.map((row: any, i: number) => (
                                <TableRow key={i} hover>
                                    {Object.entries(row).map(([key, val]: any, j: number) => (
                                        <TableCell key={j} sx={{ verticalAlign: 'top', borderRight: '1px solid #f0f0f0', width: j === 0 ? '150px' : 'auto', bgcolor: j === 0 ? '#f9fafb' : 'white', fontWeight: j === 0 ? 800 : 400 }}>
                                            {isEditMode && j !== 0 ? (
                                                <TextField
                                                    value={val}
                                                    onChange={(e) => handleSwotChange(i, key, e.target.value)}
                                                    multiline
                                                    minRows={3}
                                                    fullWidth
                                                    variant="outlined"
                                                    sx={{ bgcolor: 'white' }}
                                                />
                                            ) : (
                                                <Typography style={{ whiteSpace: 'pre-line' }}>{val}</Typography>
                                            )}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            {/* Market Position Summary */}
            {comparison?.market_position_summary && (
                <Paper sx={{ mt: 4, p: 3, bgcolor: '#e3f2fd', border: '1px solid #90caf9' }} elevation={0}>
                    <Typography variant="h6" color="primary.dark" gutterBottom fontWeight={600}>Market Position Summary</Typography>
                    <Typography variant="body1" color="text.primary">
                        {comparison.market_position_summary}
                    </Typography>
                </Paper>
            )}

            <Dialog open={openSources} onClose={() => setOpenSources(false)} maxWidth="md" fullWidth>
                <DialogTitle>Data Sources</DialogTitle>
                <DialogContent dividers>
                    {scraped_sources && scraped_sources.length > 0 ? (
                        <List>
                            {scraped_sources.map((source: any, i: number) => (
                                <ListItem key={i} component="a" href={source.url} target="_blank" sx={{ color: 'primary.main', textDecoration: 'none' }}>
                                    <ListItemIcon><LinkIcon /></ListItemIcon>
                                    <ListItemText primary={source.title || source.url} secondary={source.url} />
                                </ListItem>
                            ))}
                        </List>
                    ) : (
                        <Typography color="text.secondary">No direct sources available. Analysis generated by AI knowledge base.</Typography>
                    )}
                </DialogContent>
            </Dialog>

        </Container>
    );
};

export default ComparisonPage;