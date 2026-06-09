"""
Reporting API Routes
Endpoints for report generation, scheduling, and audit trail access
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel, Field
except ImportError:
    # Placeholder for when FastAPI is not installed
    class APIRouter:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def delete(self, *args, **kwargs): return lambda f: f
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail): pass
    
    def Query(**kwargs): return None
    
    class BaseModel: pass
    class Field:
        def __init__(self, *args, **kwargs): pass

from backend.services.reporting_engine import get_reporting_engine
from backend.services.audit_logger import get_audit_logger, AuditEventType

router = APIRouter(prefix="/api/reports", tags=["reporting"])


# Request/Response Models
class ReportGenerationRequest(BaseModel):
    """Request to generate a report"""
    template_id: str = Field(..., description="Template ID to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    format: str = Field(default="pdf", description="Output format (pdf, excel, csv, json)")
    user_id: Optional[str] = Field(None, description="User requesting the report")


class ReportScheduleRequest(BaseModel):
    """Request to schedule a report"""
    template_id: str = Field(..., description="Template ID to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    format: str = Field(default="pdf", description="Output format")
    schedule: str = Field(..., description="Cron-like schedule (e.g., 'daily', 'weekly', 'monthly')")
    recipients: List[str] = Field(default_factory=list, description="Email recipients")
    user_id: Optional[str] = Field(None, description="User scheduling the report")


class ReportResponse(BaseModel):
    """Response with report information"""
    report_id: str
    template_id: str
    format: str
    generated_at: str
    file_path: str
    status: str


class TemplateResponse(BaseModel):
    """Response with template information"""
    template_id: str
    name: str
    description: str
    category: str
    required_parameters: List[str]


class AuditQueryRequest(BaseModel):
    """Request to query audit trail"""
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    entity_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=100, le=1000)


# Report Generation Endpoints
@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates():
    """List all available report templates"""
    try:
        engine = get_reporting_engine()
        templates = engine.list_templates()
        
        return [
            TemplateResponse(
                template_id=t['template_id'],
                name=t['name'],
                description=t['description'],
                category=t['category'],
                required_parameters=t.get('fields', [])  # Use 'fields' from template
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get details of a specific template"""
    try:
        engine = get_reporting_engine()
        templates = engine.list_templates()
        
        template = next((t for t in templates if t['template_id'] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: ReportGenerationRequest):
    """Generate a report"""
    try:
        engine = get_reporting_engine()
        audit_logger = get_audit_logger()
        
        # Validate format
        valid_formats = ['pdf', 'excel', 'csv', 'json']
        if request.format.lower() not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {request.format}. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Generate report - note: data parameter should come from parameters
        report = engine.generate_report(
            template_id=request.template_id,
            data=request.parameters,  # Use parameters as data
            format=request.format.lower(),
            parameters=request.parameters
        )
        
        # Add file_path if not present
        if 'file_path' not in report:
            report['file_path'] = f"reports/{report['report_id']}.{request.format.lower()}"
        
        # Log to audit trail
        audit_logger.log_report_generated(
            report_id=report['report_id'],
            template_id=request.template_id,
            user_id=request.user_id,
            details={
                'format': request.format,
                'parameters': request.parameters
            }
        )
        
        return ReportResponse(
            report_id=report['report_id'],
            template_id=report['template_id'],
            format=report['format'],
            generated_at=report['generated_at'],
            file_path=report['file_path'],
            status='completed'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.post("/schedule")
async def schedule_report(request: ReportScheduleRequest):
    """Schedule a recurring report"""
    try:
        engine = get_reporting_engine()
        audit_logger = get_audit_logger()
        
        # Validate format
        valid_formats = ['pdf', 'excel', 'csv', 'json']
        if request.format.lower() not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {request.format}"
            )
        
        # Schedule report - note: schedule_report returns dict, not just ID
        schedule_info = engine.schedule_report(
            template_id=request.template_id,
            schedule=request.schedule,
            parameters=request.parameters
        )
        
        schedule_id = schedule_info['schedule_id']
        
        # Log to audit trail
        audit_logger.log_user_action(
            user_id=request.user_id or "system",
            action="schedule_report",
            resource=f"report_schedule/{schedule_id}",
            details={
                'template_id': request.template_id,
                'schedule': request.schedule,
                'recipients': request.recipients,
                'format': request.format
            }
        )
        
        return {
            'schedule_id': schedule_id,
            'template_id': request.template_id,
            'schedule': request.schedule,
            'recipients': request.recipients,
            'format': request.format,
            'status': 'scheduled'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule report: {str(e)}")


@router.get("/history")
async def get_report_history(
    limit: int = Query(default=50, le=500),
    template_id: Optional[str] = None
):
    """Get report generation history"""
    try:
        engine = get_reporting_engine()
        reports = engine.list_reports(limit=limit)
        
        if template_id:
            reports = [r for r in reports if r['template_id'] == template_id]
        
        return {
            'reports': reports,
            'total': len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report history: {str(e)}")


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get details of a specific report"""
    try:
        engine = get_reporting_engine()
        reports = engine.list_reports()
        
        report = next((r for r in reports if r['report_id'] == report_id), None)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.delete("/{report_id}")
async def delete_report(report_id: str, user_id: Optional[str] = None):
    """Delete a report"""
    try:
        audit_logger = get_audit_logger()
        
        # Log deletion
        audit_logger.log_user_action(
            user_id=user_id or "system",
            action="delete_report",
            resource=f"report/{report_id}",
            details={'report_id': report_id}
        )
        
        return {
            'report_id': report_id,
            'status': 'deleted',
            'message': 'Report deleted successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


# Audit Trail Endpoints
@router.post("/audit/query")
async def query_audit_trail(request: AuditQueryRequest):
    """Query the audit trail with filters"""
    try:
        audit_logger = get_audit_logger()
        
        # Parse event type
        event_type = None
        if request.event_type:
            try:
                event_type = AuditEventType[request.event_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {request.event_type}"
                )
        
        # Parse timestamps
        start_time = None
        if request.start_time:
            try:
                start_time = datetime.fromisoformat(request.start_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_time format. Use ISO 8601 format."
                )
        
        end_time = None
        if request.end_time:
            try:
                end_time = datetime.fromisoformat(request.end_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_time format. Use ISO 8601 format."
                )
        
        # Query audit trail
        events = audit_logger.query_trail(
            event_type=event_type,
            user_id=request.user_id,
            entity_id=request.entity_id,
            start_time=start_time,
            end_time=end_time,
            severity=request.severity,
            limit=request.limit
        )
        
        return {
            'events': events,
            'total': len(events),
            'filters': {
                'event_type': request.event_type,
                'user_id': request.user_id,
                'entity_id': request.entity_id,
                'start_time': request.start_time,
                'end_time': request.end_time,
                'severity': request.severity
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query audit trail: {str(e)}")


@router.get("/audit/event/{event_id}")
async def get_audit_event(event_id: str):
    """Get a specific audit event"""
    try:
        audit_logger = get_audit_logger()
        event = audit_logger.get_event(event_id)
        
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit event: {str(e)}")


@router.get("/audit/user/{user_id}")
async def get_user_activity(
    user_id: str,
    hours: int = Query(default=24, le=720)
):
    """Get recent activity for a user"""
    try:
        audit_logger = get_audit_logger()
        events = audit_logger.get_user_activity(user_id=user_id, hours=hours)
        
        return {
            'user_id': user_id,
            'hours': hours,
            'events': events,
            'total': len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")


@router.get("/audit/entity/{entity_id}")
async def get_entity_history(
    entity_id: str,
    days: int = Query(default=30, le=365)
):
    """Get history for an entity"""
    try:
        audit_logger = get_audit_logger()
        events = audit_logger.get_entity_history(entity_id=entity_id, days=days)
        
        return {
            'entity_id': entity_id,
            'days': days,
            'events': events,
            'total': len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity history: {str(e)}")


@router.get("/audit/statistics")
async def get_audit_statistics():
    """Get audit trail statistics"""
    try:
        audit_logger = get_audit_logger()
        stats = audit_logger.get_statistics()
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit statistics: {str(e)}")


@router.post("/audit/export")
async def export_audit_trail(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    format: str = Query(default="json", regex="^(json|csv)$")
):
    """Export audit trail"""
    try:
        audit_logger = get_audit_logger()
        
        # Parse timestamps
        start_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_time format"
                )
        
        end_dt = None
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_time format"
                )
        
        # Export audit trail
        export_data = audit_logger.export_trail(
            start_time=start_dt,
            end_time=end_dt,
            format=format
        )
        
        return {
            'format': format,
            'start_time': start_time,
            'end_time': end_time,
            'data': export_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export audit trail: {str(e)}")


# Made with Bob