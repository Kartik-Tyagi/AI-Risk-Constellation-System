import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const Dashboard = () => {
  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Portfolio overview and risk metrics will be displayed here.
        </Typography>
      </Box>
    </Container>
  );
};

export default Dashboard;

// Made with Bob