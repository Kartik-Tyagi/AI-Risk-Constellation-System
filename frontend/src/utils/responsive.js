/**
 * Responsive Design Utilities
 * Helper functions and constants for responsive layouts
 */

// Breakpoint values (matching Material-UI defaults)
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
};

/**
 * Get current breakpoint
 * @param {number} width - Window width
 * @returns {string} Current breakpoint name
 */
export const getCurrentBreakpoint = (width) => {
  if (width >= breakpoints.xl) return 'xl';
  if (width >= breakpoints.lg) return 'lg';
  if (width >= breakpoints.md) return 'md';
  if (width >= breakpoints.sm) return 'sm';
  return 'xs';
};

/**
 * Check if device is mobile
 * @param {number} width - Window width
 * @returns {boolean}
 */
export const isMobile = (width) => {
  return width < breakpoints.md;
};

/**
 * Check if device is tablet
 * @param {number} width - Window width
 * @returns {boolean}
 */
export const isTablet = (width) => {
  return width >= breakpoints.sm && width < breakpoints.lg;
};

/**
 * Check if device is desktop
 * @param {number} width - Window width
 * @returns {boolean}
 */
export const isDesktop = (width) => {
  return width >= breakpoints.lg;
};

/**
 * Get responsive value based on breakpoint
 * @param {Object} values - Values for each breakpoint
 * @param {number} width - Window width
 * @returns {*} Value for current breakpoint
 */
export const getResponsiveValue = (values, width) => {
  const breakpoint = getCurrentBreakpoint(width);
  
  // Return exact match or fallback to smaller breakpoints
  if (values[breakpoint] !== undefined) return values[breakpoint];
  if (breakpoint === 'xl' && values.lg !== undefined) return values.lg;
  if ((breakpoint === 'xl' || breakpoint === 'lg') && values.md !== undefined) return values.md;
  if (values.sm !== undefined) return values.sm;
  if (values.xs !== undefined) return values.xs;
  
  return values.default;
};

/**
 * Get responsive grid columns
 * @param {number} width - Window width
 * @returns {number} Number of columns
 */
export const getGridColumns = (width) => {
  return getResponsiveValue(
    {
      xs: 1,
      sm: 2,
      md: 3,
      lg: 4,
      xl: 4,
    },
    width
  );
};

/**
 * Get responsive font size
 * @param {string} variant - Typography variant
 * @param {number} width - Window width
 * @returns {string} Font size
 */
export const getResponsiveFontSize = (variant, width) => {
  const fontSizes = {
    h1: { xs: '2rem', sm: '2.5rem', md: '3rem', lg: '3.5rem' },
    h2: { xs: '1.75rem', sm: '2rem', md: '2.5rem', lg: '3rem' },
    h3: { xs: '1.5rem', sm: '1.75rem', md: '2rem', lg: '2.5rem' },
    h4: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem', lg: '2rem' },
    h5: { xs: '1.1rem', sm: '1.25rem', md: '1.5rem', lg: '1.5rem' },
    h6: { xs: '1rem', sm: '1.1rem', md: '1.25rem', lg: '1.25rem' },
    body1: { xs: '0.875rem', sm: '1rem', md: '1rem', lg: '1rem' },
    body2: { xs: '0.75rem', sm: '0.875rem', md: '0.875rem', lg: '0.875rem' },
  };

  return getResponsiveValue(fontSizes[variant] || fontSizes.body1, width);
};

/**
 * Get responsive spacing
 * @param {number} baseSpacing - Base spacing value
 * @param {number} width - Window width
 * @returns {number} Responsive spacing
 */
export const getResponsiveSpacing = (baseSpacing, width) => {
  const multiplier = getResponsiveValue(
    {
      xs: 0.75,
      sm: 0.875,
      md: 1,
      lg: 1,
      xl: 1,
    },
    width
  );

  return baseSpacing * multiplier;
};

/**
 * Get responsive chart dimensions
 * @param {number} width - Container width
 * @returns {Object} Chart dimensions
 */
export const getResponsiveChartDimensions = (width) => {
  if (width < breakpoints.sm) {
    return { width: width - 32, height: 250 };
  } else if (width < breakpoints.md) {
    return { width: width - 48, height: 300 };
  } else if (width < breakpoints.lg) {
    return { width: width - 64, height: 400 };
  } else {
    return { width: width - 80, height: 500 };
  }
};

/**
 * Get touch-friendly size
 * @param {number} baseSize - Base size
 * @param {boolean} isTouchDevice - Is touch device
 * @returns {number} Touch-friendly size
 */
export const getTouchFriendlySize = (baseSize, isTouchDevice) => {
  return isTouchDevice ? Math.max(baseSize, 44) : baseSize;
};

/**
 * Detect if device has touch support
 * @returns {boolean}
 */
export const isTouchDevice = () => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    navigator.msMaxTouchPoints > 0
  );
};

/**
 * Get responsive table pagination
 * @param {number} width - Window width
 * @returns {number} Rows per page
 */
export const getResponsiveRowsPerPage = (width) => {
  return getResponsiveValue(
    {
      xs: 5,
      sm: 10,
      md: 15,
      lg: 25,
      xl: 25,
    },
    width
  );
};

/**
 * Get responsive sidebar width
 * @param {number} width - Window width
 * @returns {number} Sidebar width
 */
export const getResponsiveSidebarWidth = (width) => {
  return getResponsiveValue(
    {
      xs: 0, // Hidden on mobile
      sm: 0, // Hidden on small tablets
      md: 240,
      lg: 280,
      xl: 320,
    },
    width
  );
};

/**
 * Should show mobile layout
 * @param {number} width - Window width
 * @returns {boolean}
 */
export const shouldShowMobileLayout = (width) => {
  return width < breakpoints.md;
};

/**
 * Get responsive dialog width
 * @param {string} size - Dialog size (sm, md, lg, xl)
 * @param {number} width - Window width
 * @returns {string|number} Dialog width
 */
export const getResponsiveDialogWidth = (size, width) => {
  if (width < breakpoints.sm) {
    return '100%';
  }

  const sizes = {
    sm: 400,
    md: 600,
    lg: 900,
    xl: 1200,
  };

  return Math.min(sizes[size] || sizes.md, width - 64);
};

// Made with Bob