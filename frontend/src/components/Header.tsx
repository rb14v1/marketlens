import React from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import logo from '../assets/logo.png';

export default function Header() {
    // REMOVED: All state and handlers for the user menu were deleted here.

    return (
        <AppBar position="static" elevation={1} sx={{ bgcolor: 'white', color: 'text.primary' }}>
            <Toolbar>
                {/* LEFT SIDE: Logo & Title */}
                <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                    <img src={logo} alt="Logo" style={{ height: '30px', marginRight: '10px' }} />
                    <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', color: '#009688' }}>
                        <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>MarketLens</Link>
                    </Typography>
                </Box>

                {/* REMOVED: The User Avatar Box was deleted from here. */}
            </Toolbar>
        </AppBar>
    );
}