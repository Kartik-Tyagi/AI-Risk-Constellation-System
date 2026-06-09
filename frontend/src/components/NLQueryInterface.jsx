import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Chip,
  Typography,
  CircularProgress,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  History as HistoryIcon,
  Clear as ClearIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';

const NLQueryInterface = ({ onQuerySubmit, loading = false }) => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  // Query templates/suggestions
  const queryTemplates = [
    {
      category: 'Risk Assessment',
      queries: [
        'What is the risk level of portfolio {name}?',
        'Show me the highest risk entities',
        'What are the risk factors for {entity}?',
        'Calculate the overall portfolio risk',
      ],
    },
    {
      category: 'Correlation Analysis',
      queries: [
        'Show me entities with high correlation to {entity}',
        'What entities are most correlated?',
        'Find entities with negative correlation to {entity}',
        'Show correlation matrix for top 10 entities',
      ],
    },
    {
      category: 'Risk Propagation',
      queries: [
        'Predict risk cascade from {entity}',
        'What happens if {entity} fails?',
        'Show risk propagation paths from {entity}',
        'Which entities would be affected by {entity}?',
      ],
    },
    {
      category: 'Comparison',
      queries: [
        'Compare risk profiles of {entity1} and {entity2}',
        'Which has higher risk: {entity1} or {entity2}?',
        'Show differences between {portfolio1} and {portfolio2}',
        'Compare risk DNA of {entity1} and {entity2}',
      ],
    },
    {
      category: 'Temporal Analysis',
      queries: [
        'How has risk changed for {entity} over time?',
        'Show risk trends for the past {period}',
        'When did {entity} have the highest risk?',
        'Predict future risk for {entity}',
      ],
    },
    {
      category: 'Optimization',
      queries: [
        'Optimize portfolio to minimize risk',
        'Suggest portfolio rebalancing',
        'What is the optimal allocation for {portfolio}?',
        'Find the best risk-return trade-off',
      ],
    },
  ];

  // Load query history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('queryHistory');
    if (savedHistory) {
      setQueryHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      // Add to history
      const newHistory = [query, ...queryHistory.filter((q) => q !== query)].slice(0, 20);
      setQueryHistory(newHistory);
      localStorage.setItem('queryHistory', JSON.stringify(newHistory));

      // Submit query
      onQuerySubmit(query);
      setShowSuggestions(false);
      setShowHistory(false);
    }
  };

  const handleTemplateClick = (template) => {
    setQuery(template);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery);
    setShowHistory(false);
    inputRef.current?.focus();
  };

  const handleVoiceInput = () => {
    if (recognitionRef.current) {
      if (isListening) {
        recognitionRef.current.stop();
      } else {
        recognitionRef.current.start();
        setIsListening(true);
      }
    }
  };

  const clearQuery = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  const clearHistory = () => {
    setQueryHistory([]);
    localStorage.removeItem('queryHistory');
    setShowHistory(false);
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 1200, mx: 'auto' }}>
      {/* Query Input */}
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          backgroundColor: 'background.paper',
          borderRadius: 2,
          boxShadow: 3,
        }}
      >
        <TextField
          ref={inputRef}
          fullWidth
          variant="outlined"
          placeholder="Ask a question about risk... (e.g., 'What is the risk of portfolio ABC?')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          disabled={loading}
          InputProps={{
            sx: { fontSize: '1.1rem' },
          }}
        />

        {query && (
          <IconButton onClick={clearQuery} disabled={loading}>
            <ClearIcon />
          </IconButton>
        )}

        <Tooltip title="Voice Input">
          <IconButton
            onClick={handleVoiceInput}
            disabled={loading || !recognitionRef.current}
            color={isListening ? 'error' : 'default'}
          >
            <MicIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Query History">
          <IconButton onClick={() => setShowHistory(!showHistory)} disabled={loading}>
            <HistoryIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Suggestions">
          <IconButton onClick={() => setShowSuggestions(!showSuggestions)} disabled={loading}>
            <AutoAwesomeIcon />
          </IconButton>
        </Tooltip>

        <IconButton type="submit" color="primary" disabled={!query.trim() || loading}>
          {loading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Paper>

      {/* Query Suggestions */}
      {showSuggestions && !showHistory && (
        <Paper
          sx={{
            mt: 2,
            p: 2,
            maxHeight: 500,
            overflow: 'auto',
            backgroundColor: 'background.paper',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Query Templates
          </Typography>
          {queryTemplates.map((category, idx) => (
            <Box key={idx} sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                {category.category}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {category.queries.map((template, qIdx) => (
                  <Chip
                    key={qIdx}
                    label={template}
                    onClick={() => handleTemplateClick(template)}
                    sx={{ cursor: 'pointer' }}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          ))}
        </Paper>
      )}

      {/* Query History */}
      {showHistory && !showSuggestions && (
        <Paper
          sx={{
            mt: 2,
            p: 2,
            maxHeight: 400,
            overflow: 'auto',
            backgroundColor: 'background.paper',
            borderRadius: 2,
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Query History</Typography>
            {queryHistory.length > 0 && (
              <IconButton size="small" onClick={clearHistory}>
                <ClearIcon />
              </IconButton>
            )}
          </Box>
          {queryHistory.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No query history yet
            </Typography>
          ) : (
            <List>
              {queryHistory.map((historyQuery, idx) => (
                <React.Fragment key={idx}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => handleHistoryClick(historyQuery)}>
                      <ListItemText primary={historyQuery} />
                    </ListItemButton>
                  </ListItem>
                  {idx < queryHistory.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* Voice Input Indicator */}
      {isListening && (
        <Paper
          sx={{
            mt: 2,
            p: 2,
            backgroundColor: 'error.dark',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <CircularProgress size={24} color="inherit" />
          <Typography>Listening... Speak now</Typography>
        </Paper>
      )}
    </Box>
  );
};

export default NLQueryInterface;

// Made with Bob