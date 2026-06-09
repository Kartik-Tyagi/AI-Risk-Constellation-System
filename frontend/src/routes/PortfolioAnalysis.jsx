import React, { useState, useEffect } from 'react';
import {
  Box, Container, Typography, Grid, Card, CardContent, CardActionArea,
  CircularProgress, Chip, Divider, Paper,
} from '@mui/material';
import { portfolioApi } from '../services/api';

const riskColor = level => {
  switch (level?.toLowerCase()) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'error';
    case 'critical': return 'error';
    default: return 'default';
  }
};

const PortfolioAnalysis = () => {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [riskLoading, setRiskLoading] = useState(false);

  useEffect(() => {
    portfolioApi.getAll()
      .then(res => setPortfolios(res.data?.portfolios || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (portfolio) => {
    setSelected(portfolio);
    setRiskData(null);
    setRiskLoading(true);
    portfolioApi.getRiskMetrics(portfolio.portfolio_id)
      .then(res => setRiskData(res.data))
      .catch(() => {})
      .finally(() => setRiskLoading(false));
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Typography variant="h4" gutterBottom>Portfolio Analysis</Typography>

      <Grid container spacing={3}>
        {/* Portfolio List */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Portfolios</Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              portfolios.map(p => (
                <Card
                  key={p.portfolio_id}
                  sx={{ mb: 1, border: selected?.portfolio_id === p.portfolio_id ? 2 : 0, borderColor: 'primary.main' }}
                >
                  <CardActionArea onClick={() => handleSelect(p)} sx={{ p: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="subtitle2">{p.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          ${(p.total_value || 0).toLocaleString()}
                        </Typography>
                      </Box>
                      <Chip
                        label={p.metadata?.risk_level || 'N/A'}
                        color={riskColor(p.metadata?.risk_level)}
                        size="small"
                      />
                    </Box>
                  </CardActionArea>
                </Card>
              ))
            )}
          </Paper>
        </Grid>

        {/* Risk Details */}
        <Grid item xs={12} md={8}>
          {!selected ? (
            <Paper sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
              <Typography>Select a portfolio to view risk analysis</Typography>
            </Paper>
          ) : (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>{selected.name}</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {selected.description || selected.metadata?.portfolio_type}
              </Typography>
              <Divider sx={{ my: 2 }} />

              {riskLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : riskData ? (
                <Grid container spacing={2}>
                  {[
                    { label: 'Risk Score', value: riskData.risk_score?.toFixed(1), unit: '' },
                    { label: 'Risk Level', value: riskData.risk_level, unit: '' },
                    { label: 'VaR (95%)', value: `$${(riskData.risk_metrics?.var_95 || 0).toLocaleString()}`, unit: '' },
                    { label: 'VaR (99%)', value: `$${(riskData.risk_metrics?.var_99 || 0).toLocaleString()}`, unit: '' },
                    { label: 'Volatility', value: ((riskData.risk_metrics?.volatility || 0) * 100).toFixed(2), unit: '%' },
                    { label: 'Sharpe Ratio', value: riskData.risk_metrics?.sharpe_ratio?.toFixed(3), unit: '' },
                    { label: 'Max Drawdown', value: ((riskData.risk_metrics?.max_drawdown || 0) * 100).toFixed(2), unit: '%' },
                    { label: 'Beta', value: riskData.risk_metrics?.beta?.toFixed(3), unit: '' },
                  ].map(({ label, value, unit }) => (
                    <Grid item xs={6} sm={3} key={label}>
                      <Card sx={{ bgcolor: 'background.default' }}>
                        <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Typography variant="caption" color="text.secondary" display="block">{label}</Typography>
                          <Typography variant="h6">{value}{unit && <span style={{ fontSize: '0.75rem' }}>{unit}</span>}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}

                  {riskData.risk_dna && (
                    <>
                      <Grid item xs={12}>
                        <Typography variant="subtitle1" sx={{ mt: 1 }}>Risk DNA</Typography>
                      </Grid>
                      {Object.entries(riskData.risk_dna).map(([key, val]) => (
                        <Grid item xs={6} sm={3} key={key}>
                          <Card sx={{ bgcolor: 'background.default' }}>
                            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                              <Typography variant="caption" color="text.secondary" display="block">
                                {key.replace(/_/g, ' ')}
                              </Typography>
                              <Typography variant="h6">{(val * 100).toFixed(1)}%</Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </>
                  )}

                  {riskData.recommendations?.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" sx={{ mt: 1 }}>Recommendations</Typography>
                      {riskData.recommendations.map((rec, i) => (
                        <Typography key={i} variant="body2" sx={{ mt: 0.5 }}>• {rec}</Typography>
                      ))}
                    </Grid>
                  )}
                </Grid>
              ) : null}
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default PortfolioAnalysis;
