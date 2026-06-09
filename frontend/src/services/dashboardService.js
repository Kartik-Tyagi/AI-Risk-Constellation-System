/**
 * Dashboard Service
 * Handles dashboard layout persistence and management
 */

class DashboardService {
  constructor() {
    this.storageKey = 'risk-dashboard-layouts';
  }

  /**
   * Save dashboard layout
   * @param {string} dashboardId - Dashboard identifier
   * @param {Object} dashboard - Dashboard configuration
   */
  async saveDashboard(dashboardId, dashboard) {
    try {
      const dashboards = this.getAllDashboards();
      dashboards[dashboardId] = {
        ...dashboard,
        lastModified: new Date().toISOString(),
      };
      
      localStorage.setItem(this.storageKey, JSON.stringify(dashboards));
      
      return { success: true };
    } catch (error) {
      console.error('Error saving dashboard:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Load dashboard layout
   * @param {string} dashboardId - Dashboard identifier
   * @returns {Object|null} Dashboard configuration
   */
  async loadDashboard(dashboardId) {
    try {
      const dashboards = this.getAllDashboards();
      return dashboards[dashboardId] || null;
    } catch (error) {
      console.error('Error loading dashboard:', error);
      return null;
    }
  }

  /**
   * Get all saved dashboards
   * @returns {Object} All dashboards
   */
  getAllDashboards() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('Error getting dashboards:', error);
      return {};
    }
  }

  /**
   * Delete dashboard
   * @param {string} dashboardId - Dashboard identifier
   */
  async deleteDashboard(dashboardId) {
    try {
      const dashboards = this.getAllDashboards();
      delete dashboards[dashboardId];
      localStorage.setItem(this.storageKey, JSON.stringify(dashboards));
      return { success: true };
    } catch (error) {
      console.error('Error deleting dashboard:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Duplicate dashboard
   * @param {string} sourceDashboardId - Source dashboard ID
   * @param {string} newDashboardId - New dashboard ID
   */
  async duplicateDashboard(sourceDashboardId, newDashboardId) {
    try {
      const sourceDashboard = await this.loadDashboard(sourceDashboardId);
      if (!sourceDashboard) {
        throw new Error('Source dashboard not found');
      }

      return await this.saveDashboard(newDashboardId, {
        ...sourceDashboard,
        name: `${sourceDashboard.name || 'Dashboard'} (Copy)`,
      });
    } catch (error) {
      console.error('Error duplicating dashboard:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Export dashboard configuration
   * @param {string} dashboardId - Dashboard identifier
   * @returns {Blob} Dashboard configuration as JSON blob
   */
  async exportDashboard(dashboardId) {
    try {
      const dashboard = await this.loadDashboard(dashboardId);
      if (!dashboard) {
        throw new Error('Dashboard not found');
      }

      const json = JSON.stringify(dashboard, null, 2);
      return new Blob([json], { type: 'application/json' });
    } catch (error) {
      console.error('Error exporting dashboard:', error);
      return null;
    }
  }

  /**
   * Import dashboard configuration
   * @param {string} dashboardId - Dashboard identifier
   * @param {File} file - JSON file containing dashboard configuration
   */
  async importDashboard(dashboardId, file) {
    try {
      const text = await file.text();
      const dashboard = JSON.parse(text);
      
      return await this.saveDashboard(dashboardId, dashboard);
    } catch (error) {
      console.error('Error importing dashboard:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Share dashboard (generate shareable link)
   * @param {string} dashboardId - Dashboard identifier
   * @returns {string} Shareable link
   */
  async shareDashboard(dashboardId) {
    try {
      const dashboard = await this.loadDashboard(dashboardId);
      if (!dashboard) {
        throw new Error('Dashboard not found');
      }

      // In a real implementation, this would upload to a server
      // For now, we'll encode the dashboard in the URL
      const encoded = btoa(JSON.stringify(dashboard));
      const baseUrl = window.location.origin;
      return `${baseUrl}/dashboard/shared/${encoded}`;
    } catch (error) {
      console.error('Error sharing dashboard:', error);
      return null;
    }
  }

  /**
   * Load shared dashboard from URL
   * @param {string} encoded - Encoded dashboard configuration
   * @returns {Object|null} Dashboard configuration
   */
  async loadSharedDashboard(encoded) {
    try {
      const json = atob(encoded);
      return JSON.parse(json);
    } catch (error) {
      console.error('Error loading shared dashboard:', error);
      return null;
    }
  }

  /**
   * Get dashboard list
   * @returns {Array} List of dashboard summaries
   */
  getDashboardList() {
    const dashboards = this.getAllDashboards();
    return Object.entries(dashboards).map(([id, dashboard]) => ({
      id,
      name: dashboard.name || id,
      lastModified: dashboard.lastModified,
      widgetCount: dashboard.widgets?.length || 0,
    }));
  }

  /**
   * Reset dashboard to default
   * @param {string} dashboardId - Dashboard identifier
   */
  async resetDashboard(dashboardId) {
    try {
      return await this.deleteDashboard(dashboardId);
    } catch (error) {
      console.error('Error resetting dashboard:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Download dashboard configuration
   * @param {string} dashboardId - Dashboard identifier
   * @param {string} filename - Download filename
   */
  async downloadDashboard(dashboardId, filename = 'dashboard.json') {
    try {
      const blob = await this.exportDashboard(dashboardId);
      if (!blob) {
        throw new Error('Failed to export dashboard');
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      return { success: true };
    } catch (error) {
      console.error('Error downloading dashboard:', error);
      return { success: false, error: error.message };
    }
  }
}

export default new DashboardService();

// Made with Bob