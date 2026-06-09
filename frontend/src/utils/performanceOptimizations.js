/**
 * Frontend Performance Optimizations
 * Code splitting, lazy loading, memoization, virtual scrolling, and debouncing
 */

import React, { lazy, Suspense, memo, useMemo, useCallback, useRef, useEffect } from 'react';

// ============================================================================
// Code Splitting & Lazy Loading
// ============================================================================

/**
 * Lazy load component with error boundary
 * @param {Function} importFunc - Dynamic import function
 * @param {Object} fallback - Fallback component while loading
 * @returns {React.Component} Lazy loaded component
 */
export const lazyLoadComponent = (importFunc, fallback = null) => {
  const LazyComponent = lazy(importFunc);
  
  return (props) => (
    <Suspense fallback={fallback || <LoadingSpinner />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

/**
 * Loading spinner component
 */
const LoadingSpinner = () => (
  <div className="loading-spinner">
    <div className="spinner"></div>
    <p>Loading...</p>
  </div>
);

/**
 * Preload component for better UX
 * @param {Function} importFunc - Dynamic import function
 */
export const preloadComponent = (importFunc) => {
  importFunc();
};

// ============================================================================
// Memoization Utilities
// ============================================================================

/**
 * Memoize component with custom comparison
 * @param {React.Component} Component - Component to memoize
 * @param {Function} arePropsEqual - Custom props comparison function
 * @returns {React.Component} Memoized component
 */
export const memoizeComponent = (Component, arePropsEqual = null) => {
  return memo(Component, arePropsEqual);
};

/**
 * Deep comparison for props
 * @param {Object} prevProps - Previous props
 * @param {Object} nextProps - Next props
 * @returns {boolean} Whether props are equal
 */
export const deepPropsEqual = (prevProps, nextProps) => {
  return JSON.stringify(prevProps) === JSON.stringify(nextProps);
};

/**
 * Shallow comparison for props (default React.memo behavior)
 * @param {Object} prevProps - Previous props
 * @param {Object} nextProps - Next props
 * @returns {boolean} Whether props are equal
 */
export const shallowPropsEqual = (prevProps, nextProps) => {
  const prevKeys = Object.keys(prevProps);
  const nextKeys = Object.keys(nextProps);
  
  if (prevKeys.length !== nextKeys.length) return false;
  
  return prevKeys.every(key => prevProps[key] === nextProps[key]);
};

/**
 * Custom hook for memoized value
 * @param {Function} factory - Factory function to compute value
 * @param {Array} deps - Dependencies array
 * @returns {*} Memoized value
 */
export const useMemoizedValue = (factory, deps) => {
  return useMemo(factory, deps);
};

/**
 * Custom hook for memoized callback
 * @param {Function} callback - Callback function
 * @param {Array} deps - Dependencies array
 * @returns {Function} Memoized callback
 */
export const useMemoizedCallback = (callback, deps) => {
  return useCallback(callback, deps);
};

// ============================================================================
// Virtual Scrolling
// ============================================================================

/**
 * Virtual scrolling hook for large lists
 * @param {Array} items - All items
 * @param {number} itemHeight - Height of each item
 * @param {number} containerHeight - Height of container
 * @param {number} overscan - Number of items to render outside viewport
 * @returns {Object} Virtual scrolling state and handlers
 */
export const useVirtualScroll = (items, itemHeight, containerHeight, overscan = 3) => {
  const [scrollTop, setScrollTop] = React.useState(0);
  
  const totalHeight = items.length * itemHeight;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;
  
  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    startIndex,
    endIndex
  };
};

/**
 * Virtual List Component
 */
export const VirtualList = memo(({ 
  items, 
  itemHeight, 
  containerHeight, 
  renderItem,
  className = ''
}) => {
  const {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    startIndex
  } = useVirtualScroll(items, itemHeight, containerHeight);
  
  return (
    <div 
      className={`virtual-list ${className}`}
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div key={startIndex + index} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

// ============================================================================
// Debouncing & Throttling
// ============================================================================

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  
  return function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
};

/**
 * Throttle function
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  
  return function throttled(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Custom hook for debounced value
 * @param {*} value - Value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {*} Debounced value
 */
export const useDebouncedValue = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = React.useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
};

/**
 * Custom hook for debounced callback
 * @param {Function} callback - Callback to debounce
 * @param {number} delay - Delay in milliseconds
 * @param {Array} deps - Dependencies
 * @returns {Function} Debounced callback
 */
export const useDebouncedCallback = (callback, delay, deps) => {
  const timeoutRef = useRef(null);
  
  return useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay, ...deps]);
};

/**
 * Custom hook for throttled callback
 * @param {Function} callback - Callback to throttle
 * @param {number} limit - Time limit in milliseconds
 * @param {Array} deps - Dependencies
 * @returns {Function} Throttled callback
 */
export const useThrottledCallback = (callback, limit, deps) => {
  const inThrottleRef = useRef(false);
  
  return useCallback((...args) => {
    if (!inThrottleRef.current) {
      callback(...args);
      inThrottleRef.current = true;
      setTimeout(() => {
        inThrottleRef.current = false;
      }, limit);
    }
  }, [callback, limit, ...deps]);
};

// ============================================================================
// Request Batching
// ============================================================================

/**
 * Batch multiple requests together
 */
export class RequestBatcher {
  constructor(batchSize = 10, delay = 50) {
    this.batchSize = batchSize;
    this.delay = delay;
    this.queue = [];
    this.timeoutId = null;
  }
  
  add(request) {
    return new Promise((resolve, reject) => {
      this.queue.push({ request, resolve, reject });
      
      if (this.queue.length >= this.batchSize) {
        this.flush();
      } else if (!this.timeoutId) {
        this.timeoutId = setTimeout(() => this.flush(), this.delay);
      }
    });
  }
  
  async flush() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    
    if (this.queue.length === 0) return;
    
    const batch = this.queue.splice(0, this.batchSize);
    
    try {
      // Execute all requests in parallel
      const results = await Promise.all(
        batch.map(({ request }) => request())
      );
      
      // Resolve all promises
      batch.forEach(({ resolve }, index) => {
        resolve(results[index]);
      });
    } catch (error) {
      // Reject all promises
      batch.forEach(({ reject }) => {
        reject(error);
      });
    }
  }
}

// ============================================================================
// Image Optimization
// ============================================================================

/**
 * Lazy load images
 * @param {string} src - Image source
 * @param {string} placeholder - Placeholder image
 * @returns {Object} Image loading state
 */
export const useLazyImage = (src, placeholder = null) => {
  const [imageSrc, setImageSrc] = React.useState(placeholder);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  useEffect(() => {
    const img = new Image();
    
    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
    };
    
    img.onerror = (err) => {
      setError(err);
      setIsLoading(false);
    };
    
    img.src = src;
  }, [src]);
  
  return { imageSrc, isLoading, error };
};

/**
 * Lazy Image Component
 */
export const LazyImage = memo(({ 
  src, 
  alt, 
  placeholder = '/placeholder.png',
  className = '',
  ...props 
}) => {
  const { imageSrc, isLoading } = useLazyImage(src, placeholder);
  
  return (
    <img 
      src={imageSrc} 
      alt={alt}
      className={`${className} ${isLoading ? 'loading' : 'loaded'}`}
      {...props}
    />
  );
});

// ============================================================================
// Performance Monitoring
// ============================================================================

/**
 * Measure component render time
 * @param {string} componentName - Name of component
 * @returns {Function} Cleanup function
 */
export const measureRenderTime = (componentName) => {
  const startTime = performance.now();
  
  return () => {
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    if (renderTime > 16) { // More than one frame (60fps)
      console.warn(`${componentName} render took ${renderTime.toFixed(2)}ms`);
    }
  };
};

/**
 * Custom hook to measure component render time
 * @param {string} componentName - Name of component
 */
export const useRenderTime = (componentName) => {
  useEffect(() => {
    const cleanup = measureRenderTime(componentName);
    return cleanup;
  });
};

/**
 * Performance observer for long tasks
 */
export const observeLongTasks = (callback) => {
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) { // Long task threshold
          callback({
            name: entry.name,
            duration: entry.duration,
            startTime: entry.startTime
          });
        }
      }
    });
    
    observer.observe({ entryTypes: ['longtask'] });
    
    return () => observer.disconnect();
  }
  
  return () => {};
};

// ============================================================================
// Cache Management
// ============================================================================

/**
 * Simple in-memory cache with TTL
 */
export class Cache {
  constructor(ttl = 300000) { // 5 minutes default
    this.cache = new Map();
    this.ttl = ttl;
  }
  
  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const item = this.cache.get(key);
    
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.value;
  }
  
  has(key) {
    return this.get(key) !== null;
  }
  
  delete(key) {
    this.cache.delete(key);
  }
  
  clear() {
    this.cache.clear();
  }
  
  size() {
    return this.cache.size;
  }
}

/**
 * Custom hook for cached data
 * @param {string} key - Cache key
 * @param {Function} fetcher - Data fetcher function
 * @param {number} ttl - Time to live in milliseconds
 * @returns {Object} Cached data and loading state
 */
export const useCachedData = (key, fetcher, ttl = 300000) => {
  const cacheRef = useRef(new Cache(ttl));
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  useEffect(() => {
    const loadData = async () => {
      // Check cache first
      const cached = cacheRef.current.get(key);
      if (cached) {
        setData(cached);
        setLoading(false);
        return;
      }
      
      // Fetch data
      try {
        setLoading(true);
        const result = await fetcher();
        cacheRef.current.set(key, result);
        setData(result);
        setError(null);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [key, fetcher, ttl]);
  
  return { data, loading, error };
};

// ============================================================================
// Export all utilities
// ============================================================================

export default {
  // Code splitting
  lazyLoadComponent,
  preloadComponent,
  
  // Memoization
  memoizeComponent,
  deepPropsEqual,
  shallowPropsEqual,
  useMemoizedValue,
  useMemoizedCallback,
  
  // Virtual scrolling
  useVirtualScroll,
  VirtualList,
  
  // Debouncing & throttling
  debounce,
  throttle,
  useDebouncedValue,
  useDebouncedCallback,
  useThrottledCallback,
  
  // Request batching
  RequestBatcher,
  
  // Image optimization
  useLazyImage,
  LazyImage,
  
  // Performance monitoring
  measureRenderTime,
  useRenderTime,
  observeLongTasks,
  
  // Cache management
  Cache,
  useCachedData
};

// Made with Bob
