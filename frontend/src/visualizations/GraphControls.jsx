import React, { useState } from 'react';
import {
  Box,
  Paper,
  IconButton,
  Slider,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Tooltip,
  Divider,
  Typography,
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  FilterList,
  Search,
  Refresh,
  Settings,
} from '@mui/icons-material';

const GraphControls = ({
  onZoomIn,
  onZoomOut,
  onResetView,
  onRefresh,
  onFilterChange,
  onSearchChange,
  onColorSchemeChange,
  onSizeByChange,
  filters = {},
  colorScheme = 'risk',
  sizeBy = 'riskScore',
  showAdvanced = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskRange, setRiskRange] = useState([0, 100]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [expanded, setExpanded] = useState(false);

  const entityTypes = [
    'stock',
    'bond',
    'commodity',
    'currency',
    'derivative',
    'fund',
    'index',
    'sector',
    'company',
  ];

  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchTerm(value);
    if (onSearchChange) {
      onSearchChange(value);
    }
  };

  const handleRiskRangeChange = (event, newValue) => {
    setRiskRange(newValue);
    if (onFilterChange) {
      onFilterChange({
        ...filters,
        minRiskLevel: newValue[0],
        maxRiskLevel: newValue[1],
      });
    }
  };

  const handleTypeToggle = (type) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter((t) => t !== type)
      : [...selectedTypes, type];
    
    setSelectedTypes(newTypes);
    if (onFilterChange) {
      onFilterChange({
        ...filters,
        nodeTypes: newTypes.length > 0 ? newTypes : undefined,
      });
    }
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setRiskRange([0, 100]);
    setSelectedTypes([]);
    if (onFilterChange) {
      onFilterChange({});
    }
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        top: 16,
        right: 16,
        width: expanded ? 320 : 'auto',
        maxHeight: '80vh',
        overflow: 'auto',
        zIndex: 1000,
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Main Controls */}
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Tooltip title="Zoom In">
            <IconButton size="small" onClick={onZoomIn}>
              <ZoomIn />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Zoom Out">
            <IconButton size="small" onClick={onZoomOut}>
              <ZoomOut />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Reset View">
            <IconButton size="small" onClick={onResetView}>
              <CenterFocusStrong />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={onRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={expanded ? 'Hide Filters' : 'Show Filters'}>
            <IconButton size="small" onClick={() => setExpanded(!expanded)}>
              <FilterList />
            </IconButton>
          </Tooltip>
        </Stack>

        {expanded && (
          <>
            <Divider sx={{ my: 2 }} />

            {/* Search */}
            <TextField
              fullWidth
              size="small"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ mb: 2 }}
            />

            {/* Risk Level Filter */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Risk Level Range
              </Typography>
              <Slider
                value={riskRange}
                onChange={handleRiskRangeChange}
                valueLabelDisplay="auto"
                min={0}
                max={100}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 50, label: '50%' },
                  { value: 100, label: '100%' },
                ]}
              />
            </Box>

            {/* Entity Type Filter */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Entity Types
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {entityTypes.map((type) => (
                  <Chip
                    key={type}
                    label={type}
                    size="small"
                    onClick={() => handleTypeToggle(type)}
                    color={selectedTypes.includes(type) ? 'primary' : 'default'}
                    variant={selectedTypes.includes(type) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Box>

            {/* Color Scheme */}
            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
              <InputLabel>Color Scheme</InputLabel>
              <Select
                value={colorScheme}
                label="Color Scheme"
                onChange={(e) => onColorSchemeChange && onColorSchemeChange(e.target.value)}
              >
                <MenuItem value="risk">Risk Level</MenuItem>
                <MenuItem value="type">Entity Type</MenuItem>
                <MenuItem value="sector">Sector</MenuItem>
              </Select>
            </FormControl>

            {/* Size By */}
            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
              <InputLabel>Node Size</InputLabel>
              <Select
                value={sizeBy}
                label="Node Size"
                onChange={(e) => onSizeByChange && onSizeByChange(e.target.value)}
              >
                <MenuItem value="riskScore">Risk Score</MenuItem>
                <MenuItem value="value">Portfolio Value</MenuItem>
                <MenuItem value="connections">Connections</MenuItem>
              </Select>
            </FormControl>

            {/* Clear Filters */}
            {(searchTerm || selectedTypes.length > 0 || riskRange[0] > 0 || riskRange[1] < 100) && (
              <Box sx={{ textAlign: 'center' }}>
                <Chip
                  label="Clear All Filters"
                  size="small"
                  onDelete={handleClearFilters}
                  color="secondary"
                />
              </Box>
            )}

            {/* Advanced Settings */}
            {showAdvanced && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Advanced Settings
                </Typography>
                {/* Add more advanced controls here */}
              </>
            )}
          </>
        )}
      </Box>
    </Paper>
  );
};

export default GraphControls;

// Made with Bob