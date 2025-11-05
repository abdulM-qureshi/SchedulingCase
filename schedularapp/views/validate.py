from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
import logging

# Import the validation functions from your existing Kindergarten.py
from .Kindergarten import validate_weekly_hours, validate_hard_constraints, extract_target_weekly_hours

logger = logging.getLogger(__name__)

@csrf_exempt
def validate_schedule_only(request):
    """
    Endpoint specifically for validating an already-generated schedule.
    """
    if request.method == 'OPTIONS':
        response = HttpResponse(status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
        return response
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
             
            schedule_data = body.get('updated_schedule')
            
            if not schedule_data:
                return JsonResponse({"error": "No schedule data provided"}, status=400)
            
            # Extract target hours from the original request data if available
            # For validation-only endpoint, we need to get this from somewhere
            # You might need to pass this from the frontend or store it somewhere
            target_hours = body.get('target_hours', {})
            
            # If target_hours is not provided, we can't validate properly
            if not target_hours:
                logger.warning("No target_hours provided for validation")
                # You might want to return an error or use default values
                target_hours = {}
            
            # Use the imported validation functions
            report, discrepancies = validate_weekly_hours(schedule_data, target_hours)
            violations = validate_hard_constraints(schedule_data, target_hours)
            
            # Debug logging
            logger.info(f"Violations structure: {type(violations)}")
            logger.info(f"Violations keys: {violations.keys() if isinstance(violations, dict) else 'Not a dict'}")
            
            return JsonResponse({
                "discrepancies": discrepancies,
                "violations": violations,  # This should already have the correct structure
                "validation_only": True
            })
            
        except Exception as e:
            logger.error(f"Error in validation endpoint: {e}", exc_info=True)
            return JsonResponse({
                "error": str(e),
                "message": "Error validating schedule"
            }, status=400)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)