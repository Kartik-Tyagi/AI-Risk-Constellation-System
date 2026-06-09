import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const Settings = () => {
  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          User preferences and application settings will be displayed here.
        </Typography>
      </Box>
    </Container>
  );
};

export default Settings;

// Made with Bob