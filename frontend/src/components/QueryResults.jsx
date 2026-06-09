import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Alert,
  Divider,
} from '@mui/material';
import {
  Download as DownloadIcon,
  TableChart as TableChartIcon,
  BarChart as BarChartIcon,
  Timeline as TimelineIcon,
  Share as ShareIcon,
} from '@mui/icons-material';
import RiskGraph2D from '../visualizations/RiskGraph2D';
import TimeSeriesChart from '../visualizations/TimeSeriesChart';
import RiskHeatmap from '../visualizations/RiskHeatmap';
import RiskDistribution from '../visualizations/RiskDistribution';
import nlQueryService from '../services/nlQueryService';

const QueryResults = ({ results, query, onExport }) => {
  const [viewMode, setViewMode] = useState('auto'); // 'auto', 'table', 'chart', 'graph'

  if (!results) {
    return null;
  }

  if (!results.success) {
    return (
      <Paper sx={{ p: 3, mt: 2 }}>
        <Alert severity="error">
          <Typography variant="h6">Query Failed</Typography>
          <Typography>{results.error || 'An error occurred while processing your query'}</Typography>
        </Alert>
      </Paper>
    );
  }

  const parsedResults = nlQueryService.parseResponse(results);

  const handleExport = (format) => {
    const blob = nlQueryService.exportResults(parsedResults, format);
    if (blob) {
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `query-results-${timestamp}.${format}`;
      nlQueryService.downloadResults(blob, filename);
    }
    if (onExport) onExport(format);
  };

  const renderHeader = () => (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
      <Box>
        <Typography variant="h5" gutterBottom>
          Query Results
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {query}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Tooltip title="Export as JSON">
          <IconButton onClick={() => handleExport('json')} size="small">
            <DownloadIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Export as CSV">
          <IconButton onClick={() => handleExport('csv')} size="small">
            <TableChartIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Share">
          <IconButton size="small">
            <ShareIcon />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );

  const renderMetadata = () => {
    if (!parsedResults.metadata || Object.keys(parsedResults.metadata).length === 0) {
      return null;
    }

    return (
      <Card sx={{ mb: 2, backgroundColor: 'background.default' }}>
        <CardContent>
          <Typography variant="subtitle2" gutterBottom>
            Query Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                Type
              </Typography>
              <Typography variant="body2">
                <Chip label={parsedResults.type} size="small" color="primary" />
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                Timestamp
              </Typography>
              <Typography variant="body2">
                {new Date(parsedResults.timestamp).toLocaleString()}
              </Typography>
            </Grid>
            {parsedResults.metadata.execution_time && (
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Execution Time
                </Typography>
                <Typography variant="body2">
                  {parsedResults.metadata.execution_time.toFixed(2)}ms
                </Typography>
              </Grid>
            )}
            {parsedResults.metadata.confidence && (
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Confidence
                </Typography>
                <Typography variant="body2">
                  {(parsedResults.metadata.confidence * 100).toFixed(1)}%
                </Typography>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const renderRiskAssessment = (data) => {
    const items = Array.isArray(data) ? data : [data];

    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Entity</TableCell>
              <TableCell>Risk Level</TableCell>
              <TableCell align="right">Risk Score</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Key Factors</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item, idx) => (
              <TableRow key={idx}>
                <TableCell>{item.entity}</TableCell>
                <TableCell>
                  <Chip
                    label={item.riskLevel}
                    color={
                      item.riskLevel === 'high'
                        ? 'error'
                        : item.riskLevel === 'medium'
                        ? 'warning'
                        : 'success'
                    }
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">{item.riskScore}</TableCell>
                <TableCell>{(item.confidence * 100).toFixed(0)}%</TableCell>
                <TableCell>
                  {item.factors.slice(0, 3).map((factor, fIdx) => (
                    <Chip key={fIdx} label={factor} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderCorrelation = (data) => {
    const items = Array.isArray(data) ? data : [data];

    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Entity 1</TableCell>
              <TableCell>Entity 2</TableCell>
              <TableCell align="right">Correlation</TableCell>
              <TableCell>Strength</TableCell>
              <TableCell>Type</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item, idx) => (
              <TableRow key={idx}>
                <TableCell>{item.entity1}</TableCell>
                <TableCell>{item.entity2}</TableCell>
                <TableCell align="right">{item.correlation}</TableCell>
                <TableCell>
                  <Chip label={item.strength} size="small" />
                </TableCell>
                <TableCell>
                  <Chip
                    label={item.type}
                    color={item.type === 'positive' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderPropagation = (data) => (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Source Entity
              </Typography>
              <Typography variant="h6">{data.source}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Affected Entities
              </Typography>
              <Typography variant="h6">{data.affectedEntities.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Total Impact
              </Typography>
              <Typography variant="h6">{data.totalImpact.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Cascade Depth
              </Typography>
              <Typography variant="h6">{data.cascadeDepth}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Affected Entities
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Entity</TableCell>
              <TableCell align="right">Impact</TableCell>
              <TableCell align="right">Depth</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.affectedEntities.map((entity, idx) => (
              <TableRow key={idx}>
                <TableCell>{entity.id}</TableCell>
                <TableCell align="right">{entity.impact.toFixed(2)}</TableCell>
                <TableCell align="right">{entity.depth}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderComparison = (data) => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Comparison Summary
      </Typography>
      <Typography variant="body1" paragraph>
        {data.summary}
      </Typography>

      {data.winner && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Winner: {data.winner}</Typography>
        </Alert>
      )}

      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
        Metrics Comparison
      </Typography>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Metric</TableCell>
              {data.entities.map((entity, idx) => (
                <TableCell key={idx} align="right">
                  {entity}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(data.metrics).map(([metric, values]) => (
              <TableRow key={metric}>
                <TableCell>{metric}</TableCell>
                {values.map((value, idx) => (
                  <TableCell key={idx} align="right">
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderTemporal = (data) => (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Entity
              </Typography>
              <Typography variant="h6">{data.entity}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Trend
              </Typography>
              <Typography variant="h6">
                <Chip
                  label={data.trend}
                  color={
                    data.trend === 'increasing'
                      ? 'error'
                      : data.trend === 'decreasing'
                      ? 'success'
                      : 'default'
                  }
                />
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Anomalies Detected
              </Typography>
              <Typography variant="h6">{data.anomalies.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {data.timeSeries && data.timeSeries.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Risk Over Time
          </Typography>
          <TimeSeriesChart
            data={data.timeSeries.map((point) => ({
              timestamp: point.timestamp,
              value: point.value,
              series: 'Risk Level',
            }))}
            width={800}
            height={300}
          />
        </Box>
      )}
    </Box>
  );

  const renderOptimization = (data) => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Optimization Results
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Expected Improvement
              </Typography>
              <Typography variant="h6" color="success.main">
                +{(data.expectedImprovement * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Risk Reduction
              </Typography>
              <Typography variant="h6" color="success.main">
                -{(data.riskReduction * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
        Recommendations
      </Typography>
      {data.recommendations.map((rec, idx) => (
        <Alert key={idx} severity="info" sx={{ mb: 1 }}>
          {rec}
        </Alert>
      ))}
    </Box>
  );

  const renderResults = () => {
    const { type, results: data } = parsedResults;

    switch (type) {
      case 'risk_assessment':
        return renderRiskAssessment(data);
      case 'correlation':
        return renderCorrelation(data);
      case 'propagation':
        return renderPropagation(data);
      case 'comparison':
        return renderComparison(data);
      case 'temporal':
        return renderTemporal(data);
      case 'optimization':
        return renderOptimization(data);
      default:
        return (
          <Box>
            <Typography variant="body1">
              {JSON.stringify(data, null, 2)}
            </Typography>
          </Box>
        );
    }
  };

  return (
    <Paper sx={{ p: 3, mt: 2 }}>
      {renderHeader()}
      <Divider sx={{ mb: 2 }} />
      {renderMetadata()}
      {renderResults()}
    </Paper>
  );
};

export default QueryResults;

// Made with Bob