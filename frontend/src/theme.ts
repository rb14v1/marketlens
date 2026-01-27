import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: 'rgba(0, 197, 193, 1)', // Teal
      contrastText: '#ffffff',
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(2, 18, 23, 1)', // Dark
      secondary: 'rgba(2, 18, 23, 0.6)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      letterSpacing: '-0.02em',
      color: 'rgba(2, 18, 23, 1)',
    },
    h4: {
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
      letterSpacing: '0.01em',
    },
    body1: {
      lineHeight: 1.6,
    }
  },
  shape: {
    borderRadius: 8, // Standard professional radius
  },
  shadows: [
    'none',
    '0px 1px 2px rgba(2, 18, 23, 0.06), 0px 1px 3px rgba(2, 18, 23, 0.1)', // 1 (Subtle)
    '0px 2px 4px rgba(2, 18, 23, 0.06), 0px 4px 6px rgba(2, 18, 23, 0.1)', // 2
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 3 (Card)
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 4
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 5
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 6
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 7
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 8
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 9
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 10
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 11
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 12
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 13
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 14
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 15
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 16
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 17
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 18
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 19
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 20
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 21
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 22
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 23
    '0px 4px 8px rgba(2, 18, 23, 0.08), 0px 8px 16px rgba(2, 18, 23, 0.08)', // 24
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          boxShadow: 'none',
          padding: '10px 20px',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0, 197, 193, 0.2)',
          },
        },
        contained: {
          backgroundColor: 'rgba(0, 197, 193, 1)',
          '&:hover': {
            backgroundColor: 'rgba(0, 180, 176, 1)',
          }
        }
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 6,
            backgroundColor: '#ffffff',
            '& fieldset': {
              borderColor: 'rgba(2, 18, 23, 0.15)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(0, 197, 193, 0.5)',
            },
            '&.Mui-focused fieldset': {
              borderColor: 'rgba(0, 197, 193, 1)',
            }
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: 'rgba(2, 18, 23, 1)',
          boxShadow: '0px 1px 0px rgba(0, 0, 0, 0.05)',
        }
      }
    }
  },
});

export default theme;
