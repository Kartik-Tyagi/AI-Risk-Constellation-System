import { useState, useCallback } from 'react';
import { useApp } from '../context/AppContext';

/**
 * Custom hook for making API calls with loading and error handling
 * @param {Function} apiFunction - The API function to call
 * @param {Object} options - Configuration options
 * @returns {Object} - { data, loading, error, execute, reset }
 */
export const useApi = (apiFunction, options = {}) => {
  const { showError } = useApp();
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);

      try {
        const response = await apiFunction(...args);
        const result = response.data;
        setData(result);
        
        if (options.onSuccess) {
          options.onSuccess(result);
        }
        
        return result;
      } catch (err) {
        const errorMessage = err.message || 'An error occurred';
        setError(errorMessage);
        
        if (options.showErrorNotification !== false) {
          showError(errorMessage);
        }
        
        if (options.onError) {
          options.onError(err);
        }
        
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, options, showError]
  );

  const reset = useCallback(() => {
    setData(options.initialData || null);
    setError(null);
    setLoading(false);
  }, [options.initialData]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
};

/**
 * Hook for making API calls that execute immediately on mount
 * @param {Function} apiFunction - The API function to call
 * @param {Array} dependencies - Dependencies array for re-execution
 * @param {Object} options - Configuration options
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useApiEffect = (apiFunction, dependencies = [], options = {}) => {
  const { data, loading, error, execute } = useApi(apiFunction, options);

  // Execute on mount and when dependencies change
  useState(() => {
    if (options.skip !== true) {
      execute();
    }
  });

  const refetch = useCallback(() => {
    return execute();
  }, [execute]);

  return {
    data,
    loading,
    error,
    refetch,
  };
};

// Made with Bob