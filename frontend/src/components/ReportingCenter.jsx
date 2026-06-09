import React, { useState, useEffect } from 'react';
import './ReportingCenter.css';

/**
 * ReportingCenter Component
 * UI for generating reports, scheduling, and viewing audit trail
 */
const ReportingCenter = () => {
  const [activeTab, setActiveTab] = useState('generate');
  const [templates, setTemplates] = useState([]);
  const [reports, setReports] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Report generation state
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [reportFormat, setReportFormat] = useState('pdf');
  const [reportParameters, setReportParameters] = useState({});
  
  // Schedule state
  const [scheduleFrequency, setScheduleFrequency] = useState('daily');
  const [scheduleRecipients, setScheduleRecipients] = useState('');
  
  // Audit filter state
  const [auditFilters, setAuditFilters] = useState({
    event_type: '',
    user_id: '',
    severity: '',
    limit: 100
  });

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
    loadReports();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/reports/templates');
      const data = await response.json();
      setTemplates(data);
      setError(null);
    } catch (err) {
      setError('Failed to load templates: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadReports = async () => {
    try {
      const response = await fetch('/api/reports/history?limit=50');
      const data = await response.json();
      setReports(data.reports || []);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  };

  const loadAuditTrail = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/reports/audit/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(auditFilters)
      });
      const data = await response.json();
      setAuditEvents(data.events || []);
      setError(null);
    } catch (err) {
      setError('Failed to load audit trail: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!selectedTemplate) {
      setError('Please select a template');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate.template_id,
          parameters: reportParameters,
          format: reportFormat,
          user_id: 'current_user' // Would come from auth context
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      const data = await response.json();
      setError(null);
      alert(`Report generated successfully: ${data.report_id}`);
      loadReports();
    } catch (err) {
      setError('Failed to generate report: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const scheduleReport = async () => {
    if (!selectedTemplate) {
      setError('Please select a template');
      return;
    }

    const recipients = scheduleRecipients.split(',').map(e => e.trim()).filter(e => e);

    try {
      setLoading(true);
      const response = await fetch('/api/reports/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate.template_id,
          parameters: reportParameters,
          format: reportFormat,
          schedule: scheduleFrequency,
          recipients: recipients,
          user_id: 'current_user'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to schedule report');
      }

      const data = await response.json();
      setError(null);
      alert(`Report scheduled successfully: ${data.schedule_id}`);
    } catch (err) {
      setError('Failed to schedule report: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (reportId) => {
    try {
      const response = await fetch(`/api/reports/${reportId}`);
      const data = await response.json();
      
      // In production, this would trigger actual file download
      alert(`Download report: ${reportId}\nFile: ${data.file_path}`);
    } catch (err) {
      setError('Failed to download report: ' + err.message);
    }
  };

  const renderGenerateTab = () => (
    <div className="generate-tab">
      <h3>Generate Report</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-section">
        <label>Select Template:</label>
        <select 
          value={selectedTemplate?.template_id || ''}
          onChange={(e) => {
            const template = templates.find(t => t.template_id === e.target.value);
            setSelectedTemplate(template);
            setReportParameters({});
          }}
          disabled={loading}
        >
          <option value="">-- Select Template --</option>
          {templates.map(template => (
            <option key={template.template_id} value={template.template_id}>
              {template.name} ({template.category})
            </option>
          ))}
        </select>
      </div>

      {selectedTemplate && (
        <>
          <div className="template-info">
            <h4>{selectedTemplate.name}</h4>
            <p>{selectedTemplate.description}</p>
            <p><strong>Category:</strong> {selectedTemplate.category}</p>
          </div>

          <div className="form-section">
            <label>Output Format:</label>
            <select 
              value={reportFormat}
              onChange={(e) => setReportFormat(e.target.value)}
              disabled={loading}
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>

          <div className="form-section">
            <label>Parameters:</label>
            <div className="parameters-grid">
              {selectedTemplate.fields?.map(field => (
                <div key={field} className="parameter-input">
                  <label>{field}:</label>
                  <input
                    type="text"
                    value={reportParameters[field] || ''}
                    onChange={(e) => setReportParameters({
                      ...reportParameters,
                      [field]: e.target.value
                    })}
                    placeholder={`Enter ${field}`}
                    disabled={loading}
                  />
                </div>
              ))}
            </div>
          </div>

          <button 
            className="btn-primary"
            onClick={generateReport}
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </>
      )}
    </div>
  );

  const renderScheduleTab = () => (
    <div className="schedule-tab">
      <h3>Schedule Report</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-section">
        <label>Select Template:</label>
        <select 
          value={selectedTemplate?.template_id || ''}
          onChange={(e) => {
            const template = templates.find(t => t.template_id === e.target.value);
            setSelectedTemplate(template);
          }}
          disabled={loading}
        >
          <option value="">-- Select Template --</option>
          {templates.map(template => (
            <option key={template.template_id} value={template.template_id}>
              {template.name}
            </option>
          ))}
        </select>
      </div>

      {selectedTemplate && (
        <>
          <div className="form-section">
            <label>Frequency:</label>
            <select 
              value={scheduleFrequency}
              onChange={(e) => setScheduleFrequency(e.target.value)}
              disabled={loading}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div className="form-section">
            <label>Output Format:</label>
            <select 
              value={reportFormat}
              onChange={(e) => setReportFormat(e.target.value)}
              disabled={loading}
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>

          <div className="form-section">
            <label>Recipients (comma-separated emails):</label>
            <input
              type="text"
              value={scheduleRecipients}
              onChange={(e) => setScheduleRecipients(e.target.value)}
              placeholder="user1@example.com, user2@example.com"
              disabled={loading}
            />
          </div>

          <button 
            className="btn-primary"
            onClick={scheduleReport}
            disabled={loading}
          >
            {loading ? 'Scheduling...' : 'Schedule Report'}
          </button>
        </>
      )}
    </div>
  );

  const renderHistoryTab = () => (
    <div className="history-tab">
      <h3>Report History</h3>
      
      <div className="reports-list">
        {reports.length === 0 ? (
          <p>No reports generated yet</p>
        ) : (
          <table className="reports-table">
            <thead>
              <tr>
                <th>Report ID</th>
                <th>Template</th>
                <th>Format</th>
                <th>Generated</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map(report => (
                <tr key={report.report_id}>
                  <td>{report.report_id}</td>
                  <td>{report.template_name}</td>
                  <td>{report.format.toUpperCase()}</td>
                  <td>{new Date(report.generated_at).toLocaleString()}</td>
                  <td>
                    <span className={`status-badge status-${report.status}`}>
                      {report.status}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="btn-small"
                      onClick={() => downloadReport(report.report_id)}
                    >
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );

  const renderAuditTab = () => (
    <div className="audit-tab">
      <h3>Audit Trail</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="audit-filters">
        <div className="filter-row">
          <div className="filter-input">
            <label>Event Type:</label>
            <select
              value={auditFilters.event_type}
              onChange={(e) => setAuditFilters({...auditFilters, event_type: e.target.value})}
            >
              <option value="">All</option>
              <option value="risk_calculation">Risk Calculation</option>
              <option value="user_action">User Action</option>
              <option value="system_event">System Event</option>
              <option value="alert_triggered">Alert Triggered</option>
              <option value="report_generated">Report Generated</option>
            </select>
          </div>

          <div className="filter-input">
            <label>Severity:</label>
            <select
              value={auditFilters.severity}
              onChange={(e) => setAuditFilters({...auditFilters, severity: e.target.value})}
            >
              <option value="">All</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div className="filter-input">
            <label>User ID:</label>
            <input
              type="text"
              value={auditFilters.user_id}
              onChange={(e) => setAuditFilters({...auditFilters, user_id: e.target.value})}
              placeholder="Filter by user"
            />
          </div>

          <button 
            className="btn-primary"
            onClick={loadAuditTrail}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Search'}
          </button>
        </div>
      </div>

      <div className="audit-events">
        {auditEvents.length === 0 ? (
          <p>No audit events found. Click Search to load events.</p>
        ) : (
          <table className="audit-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Type</th>
                <th>Action</th>
                <th>User</th>
                <th>Severity</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map(event => (
                <tr key={event.event_id}>
                  <td>{event.event_id}</td>
                  <td>{event.event_type}</td>
                  <td>{event.action}</td>
                  <td>{event.user_id || 'System'}</td>
                  <td>
                    <span className={`severity-badge severity-${event.severity}`}>
                      {event.severity}
                    </span>
                  </td>
                  <td>{new Date(event.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );

  return (
    <div className="reporting-center">
      <div className="reporting-header">
        <h2>Reporting & Compliance Center</h2>
        <p>Generate reports, schedule recurring reports, and view audit trail</p>
      </div>

      <div className="reporting-tabs">
        <button 
          className={`tab-button ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          Generate Report
        </button>
        <button 
          className={`tab-button ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
        >
          Schedule Report
        </button>
        <button 
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          Report History
        </button>
        <button 
          className={`tab-button ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          Audit Trail
        </button>
      </div>

      <div className="reporting-content">
        {activeTab === 'generate' && renderGenerateTab()}
        {activeTab === 'schedule' && renderScheduleTab()}
        {activeTab === 'history' && renderHistoryTab()}
        {activeTab === 'audit' && renderAuditTab()}
      </div>
    </div>
  );
};

export default ReportingCenter;

// Made with Bob