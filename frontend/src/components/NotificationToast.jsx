import React, { useState, useEffect } from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  IconButton,
  Button,
  Box,
  Typography,
} from '@mui/material';
import {
  Close as CloseIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const NotificationToast = ({ notification, onClose, onAction }) => {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (notification) {
      setOpen(true);
    }
  }, [notification]);

  const handleClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
    if (onClose) {
      onClose();
    }
  };

  const handleAction = (action) => {
    if (onAction) {
      onAction(action, notification);
    }
    handleClose();
  };

  if (!notification) {
    return null;
  }

  const getSeverity = () => {
    switch (notification.severity?.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      case 'success':
        return 'success';
      default:
        return 'info';
    }
  };

  const getAutoHideDuration = () => {
    switch (notification.severity?.toLowerCase()) {
      case 'critical':
        return null; // Don't auto-hide critical alerts
      case 'warning':
        return 10000; // 10 seconds
      case 'info':
        return 6000; // 6 seconds
      default:
        return 6000;
    }
  };

  return (
    <Snackbar
      open={open}
      autoHideDuration={getAutoHideDuration()}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      <Alert
        severity={getSeverity()}
        onClose={handleClose}
        sx={{
          width: '100%',
          minWidth: 300,
          maxWidth: 500,
        }}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {notification.actions?.map((action, idx) => (
              <Button
                key={idx}
                color="inherit"
                size="small"
                onClick={() => handleAction(action)}
              >
                {action.label}
              </Button>
            ))}
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={handleClose}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
        }
      >
        <AlertTitle>{notification.title || 'Notification'}</AlertTitle>
        <Typography variant="body2">{notification.message}</Typography>
        {notification.entity_id && (
          <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
            Entity: {notification.entity_id}
          </Typography>
        )}
        {notification.timestamp && (
          <Typography variant="caption" display="block" color="text.secondary">
            {new Date(notification.timestamp).toLocaleTimeString()}
          </Typography>
        )}
      </Alert>
    </Snackbar>
  );
};

// Toast Container Component
export const ToastContainer = () => {
  const [notifications, setNotifications] = useState([]);
  const [currentNotification, setCurrentNotification] = useState(null);

  useEffect(() => {
    // Listen for custom toast events
    const handleToast = (event) => {
      const notification = event.detail;
      setNotifications((prev) => [...prev, notification]);
    };

    window.addEventListener('showToast', handleToast);
    return () => window.removeEventListener('showToast', handleToast);
  }, []);

  useEffect(() => {
    if (notifications.length > 0 && !currentNotification) {
      setCurrentNotification(notifications[0]);
      setNotifications((prev) => prev.slice(1));
    }
  }, [notifications, currentNotification]);

  const handleClose = () => {
    setCurrentNotification(null);
  };

  const handleAction = (action, notification) => {
    if (action.handler) {
      action.handler(notification);
    }
  };

  return (
    <NotificationToast
      notification={currentNotification}
      onClose={handleClose}
      onAction={handleAction}
    />
  );
};

export default NotificationToast;

// Made with Bob