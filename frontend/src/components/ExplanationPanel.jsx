import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Info, TrendingUp, TrendingDown, AccountTree } from '@mui/icons-material';

/**
 * ExplanationPanel Component
 * Displays AI explainability information for risk predictions
 */
const ExplanationPanel = ({ entityId, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [explanationData, setExplanationData] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (entityId) {
      fetchExplanation();
    }
  }, [entityId]);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/explainability/explain/risk/${entityId}?include_narrative=true&include_attention=true`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch explanation');
      }
      
      const data = await response.json();
      setExplanationData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const renderNarrative = () => {
    if (!explanationData?.narrative) return null;

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          <Info sx={{ mr: 1, verticalAlign: 'middle' }} />
          Risk Explanation
        </Typography>
        <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
          <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
            {explanationData.narrative}
          </Typography>
        </Paper>
      </Box>
    );
  };

  const renderFeatureImportance = () => {
    if (!explanationData?.shap_explanation?.top_features) return null;

    const features = explanationData.shap_explanation.top_features;
    const chartData = features.map(f => ({
      name: f.feature,
      value: Math.abs(f.shap_value),
      impact: f.shap_value > 0 ? 'Increases Risk' : 'Decreases Risk',
      rawValue: f.shap_value
    }));

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Feature Importance
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          SHAP values showing how each feature contributes to the risk score
        </Typography>
        
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={120} />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <Paper sx={{ p: 1 }}>
                      <Typography variant="body2">
                        <strong>{data.name}</strong>
                      </Typography>
                      <Typography variant="body2" color={data.rawValue > 0 ? 'error' : 'success'}>
                        SHAP: {data.rawValue.toFixed(3)}
                      </Typography>
                      <Typography variant="caption">
                        {data.impact}
                      </Typography>
                    </Paper>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="value">
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.rawValue > 0 ? '#f44336' : '#4caf50'} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Feature Details
          </Typography>
          <List dense>
            {features.map((feature, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={feature.feature}
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        size="small"
                        label={`SHAP: ${feature.shap_value.toFixed(3)}`}
                        color={feature.shap_value > 0 ? 'error' : 'success'}
                        icon={feature.shap_value > 0 ? <TrendingUp /> : <TrendingDown />}
                      />
                      <Typography variant="caption">
                        {feature.shap_value > 0 ? 'Increases' : 'Decreases'} risk
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Box>
    );
  };

  const renderAttentionWeights = () => {
    if (!explanationData?.attention) return null;

    const attention = explanationData.attention;

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          <AccountTree sx={{ mr: 1, verticalAlign: 'middle' }} />
          Attention Weights
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Graph attention showing which entities influence this risk assessment
        </Typography>

        {attention.incoming_attention && attention.incoming_attention.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Incoming Influences
            </Typography>
            <Grid container spacing={1}>
              {attention.incoming_attention.map((item, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">
                        From: {item.source}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            bgcolor: 'grey.200',
                            borderRadius: 1,
                            overflow: 'hidden'
                          }}
                        >
                          <Box
                            sx={{
                              width: `${item.weight * 100}%`,
                              height: '100%',
                              bgcolor: 'primary.main'
                            }}
                          />
                        </Box>
                        <Typography variant="caption" sx={{ ml: 1, minWidth: 40 }}>
                          {(item.weight * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {attention.outgoing_attention && attention.outgoing_attention.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Outgoing Influences
            </Typography>
            <Grid container spacing={1}>
              {attention.outgoing_attention.map((item, idx) => (
                <Grid item xs={12} sm={6} key={idx}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">
                        To: {item.target}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            bgcolor: 'grey.200',
                            borderRadius: 1,
                            overflow: 'hidden'
                          }}
                        >
                          <Box
                            sx={{
                              width: `${item.weight * 100}%`,
                              height: '100%',
                              bgcolor: 'secondary.main'
                            }}
                          />
                        </Box>
                        <Typography variant="caption" sx={{ ml: 1, minWidth: 40 }}>
                          {(item.weight * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Box>
    );
  };

  const renderRiskData = () => {
    if (!explanationData?.risk_data) return null;

    const riskData = explanationData.risk_data;

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Risk Details
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">
                  Risk Score
                </Typography>
                <Typography variant="h4" color="error">
                  {riskData.risk_score.toFixed(1)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {riskData.trend && (
            <Grid item xs={12} sm={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Trend
                  </Typography>
                  <Typography variant="h6">
                    {riskData.trend}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {riskData.correlated_entities && riskData.correlated_entities.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Correlated Entities
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {riskData.correlated_entities.map((entity, idx) => (
                      <Chip key={idx} label={entity} size="small" />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}

          {riskData.recommendations && riskData.recommendations.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations
                  </Typography>
                  <List dense>
                    {riskData.recommendations.map((rec, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={rec} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!explanationData) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">No explanation data available</Alert>
      </Box>
    );
  }

  return (
    <Paper sx={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Feature Importance" />
          <Tab label="Attention Weights" />
          <Tab label="Details" />
        </Tabs>
      </Box>

      <Box sx={{ height: 'calc(100% - 48px)', overflow: 'auto' }}>
        {activeTab === 0 && renderNarrative()}
        {activeTab === 1 && renderFeatureImportance()}
        {activeTab === 2 && renderAttentionWeights()}
        {activeTab === 3 && renderRiskData()}
      </Box>
    </Paper>
  );
};

export default ExplanationPanel;

// Made with Bob