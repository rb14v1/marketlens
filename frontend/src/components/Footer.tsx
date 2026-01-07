import React from 'react';
import { Box, Container, Typography, Link } from '@mui/material';

const Footer: React.FC = () => {
    return (
        <Box
            component="footer"
            sx={{
                py: 2,
                px: 2,
                mt: 'auto',
                backgroundColor: 'background.paper',
                color: 'text.primary',
                borderTop: '1px solid',
                borderColor: 'divider',
            }}
        >
            <Container maxWidth="lg">
                <Typography variant="body1" align="center">
                    © {new Date().getFullYear()} MarketLens. All rights reserved.
                </Typography>
                <Typography variant="body2" align="center" sx={{ color: 'text.secondary' }}>
                    <Link color="inherit" href="#">
                        Privacy Policy
                    </Link>
                    {' | '}
                    <Link color="inherit" href="#">
                        Terms of Service
                    </Link>
                </Typography>
            </Container>
        </Box>
    );
};

export default Footer;
