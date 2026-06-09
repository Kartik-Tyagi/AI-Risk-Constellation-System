import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const RiskConstellation = () => {
  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" gutterBottom>
          Risk Constellation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Interactive 2D/3D risk visualization will be displayed here.
        </Typography>
      </Box>
    </Container>
  );
};

export default RiskConstellation;

// Made with Bob