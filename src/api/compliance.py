"""
HIPAA Compliance API routes

Provides compliance checking endpoints for HIPAA-covered healthcare applications.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.config.hipaa_checker import run_hipaa_compliance_check
from src.api.security import verify_admin_token  # We'll need to create this

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/hipaa", response_model=Dict[str, Any])
async def run_hipaa_compliance_check_endpoint(
    detailed: Optional[bool] = Query(False, description="Include detailed check information"),
    current_user: Dict[str, Any] = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Run HIPAA compliance checks.
    
    **Admin role required**
    
    This endpoint runs comprehensive HIPAA compliance checks including:
    - PHI encryption at rest (database SSL, encryption keys)
    - PHI encryption in transit (HTTPS for API URLs)
    - Audit logging of API activity
    - Access controls (JWT authentication)
    - Session timeout policies
    - Role-based access restrictions
    
    Query Parameters:
    - detailed: Include full details for each check (default: false)
    
    Response (Scoring: 0-74 points):
    - score: "X/74" format
    - percentage: Compliance percentage (0-100%)
    - status: "compliant" (>=65 points) or "non_compliant" (<65 points)
    - passed: List of passed checks with details
    - failed: List of failed checks with recommendations
    - timestamp: ISO 8601 timestamp
    - summary: Overall statistics
    """
    try:
        logger.info(f"Running HIPAA compliance checks (initiated by user: {current_user.get('username')})")
        
        # Run compliance checks
        result = run_hipaa_compliance_check()
        
        # Optionally filter details
        if not detailed:
            # Keep only essential fields
            result['passed'] = [
                {'check': p['check'], 'points': p['points'], 'status': p['status']}
                for p in result.get('passed', [])
            ]
            result['failed'] = [
                {'check': f['check'], 'points': f['points'], 'status': f['status'], 'recommendation': f['recommendation']}
                for f in result.get('failed', [])
            ]
        
        logger.info(f"Compliance check completed: {result['score']} ({result['percentage']}%)")
        return result
        
    except Exception as e:
        logger.error(f"Error running compliance checks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run compliance checks: {str(e)}"
        )


@router.get("/hipaa/summary", response_model=Dict[str, Any])
async def get_hipaa_compliance_summary(
    current_user: Dict[str, Any] = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Get summary of HIPAA compliance status.
    
    **Admin role required**
    
    Returns quick compliance status without running full checks.
    Useful for dashboards and health checks.
    """
    try:
        # Run checks
        result = run_hipaa_compliance_check()
        
        # Extract only summary
        return {
            'score': result['score'],
            'percentage': result['percentage'],
            'status': result['status'],
            'timestamp': result['timestamp'],
            'summary': result['summary'],
            'checks_by_category': {
                'encryption': {
                    'at_rest': len([c for c in result['passed'] if 'Encryption' in c['check'] and 'Transit' not in c['check']]),
                    'in_transit': len([c for c in result['passed'] if 'HTTPS' in c['check']])
                },
                'audit': len([c for c in result['passed'] if 'Audit' in c['check']]),
                'access_control': len([c for c in result['passed'] if 'JWT' in c['check'] or 'Authentication' in c['check']]),
                'session': len([c for c in result['passed'] if 'Session' in c['check']]),
                'rbac': len([c for c in result['passed'] if 'Role' in c['check']])
            }
        }
    except Exception as e:
        logger.error(f"Error getting compliance summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compliance summary: {str(e)}"
        )


@router.get("/hipaa/export", response_model=Dict[str, Any])
async def export_hipaa_compliance_report(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: Dict[str, Any] = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Export HIPAA compliance report.
    
    **Admin role required**
    
    Export the compliance report in specified format (JSON or CSV).
    Useful for audit documentation and compliance submissions.
    """
    try:
        result = run_hipaa_compliance_check()
        
        if format.lower() == "csv":
            # Convert to CSV format
            csv_data = _convert_to_csv(result)
            return {
                'format': 'csv',
                'data': csv_data,
                'timestamp': result['timestamp']
            }
        else:
            # Return JSON (default)
            return {
                'format': 'json',
                'data': result,
                'timestamp': result['timestamp']
            }
    except Exception as e:
        logger.error(f"Error exporting compliance report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export compliance report: {str(e)}"
        )


def _convert_to_csv(result: Dict[str, Any]) -> str:
    """Convert compliance result to CSV format"""
    csv_lines = [
        "Check,Status,Points,Details/Reason",
        f"Report Generated,{result['timestamp']},,",
        f"Total Score,{result['score']},,",
        f"Percentage,{result['percentage']}%,,",
        f"Overall Status,{result['status']},,",
        ""
    ]
    
    # Add passed checks
    csv_lines.append("PASSED CHECKS:")
    for check in result.get('passed', []):
        csv_lines.append(f"{check['check']},PASSED,{check['points']},{check.get('details', '')}")
    
    csv_lines.append("")
    
    # Add failed checks
    csv_lines.append("FAILED CHECKS:")
    for check in result.get('failed', []):
        reason = check.get('reason', '').replace(',', ';')  # Escape commas
        csv_lines.append(f"{check['check']},FAILED,{check['points']},{reason}")
        if check.get('recommendation'):
            rec = check['recommendation'].replace(',', ';')
            csv_lines.append(f"  Recommendation,,,{rec}")
    
    return "\n".join(csv_lines)
