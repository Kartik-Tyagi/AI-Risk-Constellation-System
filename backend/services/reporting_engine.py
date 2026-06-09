"""
Reporting Engine
Generate compliance reports and regulatory documents
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportTemplate:
    """Represents a report template"""
    
    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        category: str,
        fields: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize report template
        
        Args:
            template_id: Unique template identifier
            name: Template name
            description: Template description
            category: Report category
            fields: Required data fields
            metadata: Additional metadata
        """
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category
        self.fields = fields
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()


class ReportingEngine:
    """Main reporting engine for generating compliance reports"""
    
    def __init__(self):
        """Initialize reporting engine"""
        self.templates: Dict[str, ReportTemplate] = {}
        self.generated_reports: List[Dict[str, Any]] = []
        self.report_counter = 0
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize default report templates"""
        
        # Risk Summary Report
        self.add_template(ReportTemplate(
            template_id='risk_summary',
            name='Risk Summary Report',
            description='Comprehensive risk overview across all entities',
            category='risk_management',
            fields=['entities', 'risk_scores', 'risk_distribution', 'top_risks', 'trends'],
            metadata={'frequency': 'daily', 'format': ['pdf', 'excel']}
        ))
        
        # Portfolio Risk Report
        self.add_template(ReportTemplate(
            template_id='portfolio_risk',
            name='Portfolio Risk Report',
            description='Detailed portfolio risk analysis',
            category='portfolio_management',
            fields=['portfolio_id', 'holdings', 'risk_metrics', 'var', 'stress_tests'],
            metadata={'frequency': 'weekly', 'format': ['pdf', 'excel']}
        ))
        
        # Counterparty Exposure Report
        self.add_template(ReportTemplate(
            template_id='counterparty_exposure',
            name='Counterparty Exposure Report',
            description='Counterparty credit exposure analysis',
            category='credit_risk',
            fields=['counterparties', 'exposures', 'credit_ratings', 'limits', 'breaches'],
            metadata={'frequency': 'daily', 'format': ['pdf', 'excel']}
        ))
        
        # Regulatory Compliance Report
        self.add_template(ReportTemplate(
            template_id='regulatory_compliance',
            name='Regulatory Compliance Report',
            description='Regulatory compliance status and metrics',
            category='compliance',
            fields=['regulations', 'compliance_status', 'violations', 'remediation'],
            metadata={'frequency': 'monthly', 'format': ['pdf']}
        ))
        
        # Audit Trail Report
        self.add_template(ReportTemplate(
            template_id='audit_trail',
            name='Audit Trail Report',
            description='System audit trail and activity log',
            category='audit',
            fields=['events', 'users', 'actions', 'timestamps', 'changes'],
            metadata={'frequency': 'on_demand', 'format': ['pdf', 'excel', 'csv']}
        ))
        
        # Market Risk Report
        self.add_template(ReportTemplate(
            template_id='market_risk',
            name='Market Risk Report',
            description='Market risk exposure and sensitivity analysis',
            category='market_risk',
            fields=['positions', 'market_data', 'sensitivities', 'scenarios'],
            metadata={'frequency': 'daily', 'format': ['pdf', 'excel']}
        ))
        
        # Concentration Risk Report
        self.add_template(ReportTemplate(
            template_id='concentration_risk',
            name='Concentration Risk Report',
            description='Risk concentration analysis by sector, geography, counterparty',
            category='risk_management',
            fields=['concentrations', 'limits', 'breaches', 'diversification'],
            metadata={'frequency': 'weekly', 'format': ['pdf', 'excel']}
        ))
    
    def add_template(self, template: ReportTemplate) -> bool:
        """
        Add a report template
        
        Args:
            template: ReportTemplate instance
            
        Returns:
            True if successful
        """
        self.templates[template.template_id] = template
        logger.info(f"Added template: {template.name}")
        return True
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available templates
        
        Args:
            category: Filter by category
            
        Returns:
            List of template information
        """
        templates = self.templates.values()
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return [
            {
                'template_id': t.template_id,
                'name': t.name,
                'description': t.description,
                'category': t.category,
                'fields': t.fields,
                'metadata': t.metadata
            }
            for t in templates
        ]
    
    def generate_report(
        self,
        template_id: str,
        data: Dict[str, Any],
        format: str = 'json',
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a report from template
        
        Args:
            template_id: Template identifier
            data: Data for report generation
            format: Output format (json, pdf, excel, csv)
            parameters: Additional parameters
            
        Returns:
            Generated report information
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Validate required fields
        missing_fields = [f for f in template.fields if f not in data]
        if missing_fields:
            logger.warning(f"Missing fields for report: {missing_fields}")
        
        # Generate report ID
        self.report_counter += 1
        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-{self.report_counter:04d}"
        
        # Aggregate data
        aggregated_data = self._aggregate_data(template, data)
        
        # Generate report content
        report_content = self._generate_content(template, aggregated_data, format)
        
        # Create report record
        report = {
            'report_id': report_id,
            'template_id': template_id,
            'template_name': template.name,
            'category': template.category,
            'format': format,
            'generated_at': datetime.utcnow().isoformat(),
            'parameters': parameters or {},
            'data_summary': self._create_summary(aggregated_data),
            'content': report_content,
            'status': 'completed'
        }
        
        self.generated_reports.append(report)
        logger.info(f"Generated report: {report_id}")
        
        return report
    
    def _aggregate_data(
        self,
        template: ReportTemplate,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate data for report"""
        aggregated = {}
        
        for field in template.fields:
            if field in data:
                aggregated[field] = data[field]
            else:
                aggregated[field] = None
        
        # Add metadata
        aggregated['_metadata'] = {
            'template': template.name,
            'generated_at': datetime.utcnow().isoformat(),
            'data_points': len(data)
        }
        
        return aggregated
    
    def _generate_content(
        self,
        template: ReportTemplate,
        data: Dict[str, Any],
        format: str
    ) -> Any:
        """Generate report content in specified format"""
        
        if format == 'json':
            return data
        
        elif format == 'pdf':
            # In production, use reportlab or similar
            return {
                'type': 'pdf',
                'placeholder': 'PDF generation would happen here',
                'data': data
            }
        
        elif format == 'excel':
            # In production, use openpyxl or pandas
            return {
                'type': 'excel',
                'placeholder': 'Excel generation would happen here',
                'data': data
            }
        
        elif format == 'csv':
            # In production, use csv module or pandas
            return {
                'type': 'csv',
                'placeholder': 'CSV generation would happen here',
                'data': data
            }
        
        else:
            return data
    
    def _create_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create data summary for report"""
        summary = {
            'total_fields': len(data),
            'populated_fields': sum(1 for v in data.values() if v is not None),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add specific summaries based on data
        if 'risk_scores' in data and data['risk_scores']:
            import numpy as np
            scores = list(data['risk_scores'].values()) if isinstance(data['risk_scores'], dict) else data['risk_scores']
            summary['risk_summary'] = {
                'count': len(scores),
                'mean': float(np.mean(scores)),
                'max': float(np.max(scores)),
                'min': float(np.min(scores))
            }
        
        return summary
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a generated report by ID"""
        for report in self.generated_reports:
            if report['report_id'] == report_id:
                return report
        return None
    
    def list_reports(
        self,
        category: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List generated reports
        
        Args:
            category: Filter by category
            days: Number of days of history
            limit: Maximum number of reports
            
        Returns:
            List of reports
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        reports = [
            r for r in self.generated_reports
            if datetime.fromisoformat(r['generated_at']) > cutoff
        ]
        
        if category:
            reports = [r for r in reports if r['category'] == category]
        
        # Sort by generation time (newest first)
        reports.sort(key=lambda x: x['generated_at'], reverse=True)
        
        return reports[:limit]
    
    def schedule_report(
        self,
        template_id: str,
        schedule: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a recurring report
        
        Args:
            template_id: Template identifier
            schedule: Schedule specification (cron-like)
            parameters: Report parameters
            
        Returns:
            Schedule information
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        schedule_id = f"SCH-{len(self.generated_reports) + 1}"
        
        schedule_info = {
            'schedule_id': schedule_id,
            'template_id': template_id,
            'template_name': template.name,
            'schedule': schedule,
            'parameters': parameters or {},
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active',
            'next_run': self._calculate_next_run(schedule)
        }
        
        logger.info(f"Scheduled report: {schedule_id}")
        return schedule_info
    
    def _calculate_next_run(self, schedule: str) -> str:
        """Calculate next run time from schedule"""
        # Simple implementation - in production use croniter or similar
        if schedule == 'daily':
            next_run = datetime.utcnow() + timedelta(days=1)
        elif schedule == 'weekly':
            next_run = datetime.utcnow() + timedelta(weeks=1)
        elif schedule == 'monthly':
            next_run = datetime.utcnow() + timedelta(days=30)
        else:
            next_run = datetime.utcnow() + timedelta(days=1)
        
        return next_run.isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reporting engine statistics"""
        return {
            'total_templates': len(self.templates),
            'total_reports': len(self.generated_reports),
            'reports_by_category': self._count_by_category(),
            'recent_reports': len([
                r for r in self.generated_reports
                if datetime.fromisoformat(r['generated_at']) > 
                   datetime.utcnow() - timedelta(days=7)
            ])
        }
    
    def _count_by_category(self) -> Dict[str, int]:
        """Count reports by category"""
        counts = {}
        for report in self.generated_reports:
            category = report['category']
            counts[category] = counts.get(category, 0) + 1
        return counts


# Global reporting engine instance
_reporting_engine = None


def get_reporting_engine() -> ReportingEngine:
    """Get or create global reporting engine instance"""
    global _reporting_engine
    if _reporting_engine is None:
        _reporting_engine = ReportingEngine()
    return _reporting_engine


# Made with Bob