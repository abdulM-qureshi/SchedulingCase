from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()  # load variables from .env
import logging
import openai
import json
import time
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

@csrf_exempt
def brikilund(request):
    try:
        start_time = datetime.now()  # start timer here

        # Build context
        context , pedagogues, assistants, helpers  = _collect_context_from_request(request)

        end_time = datetime.now()  # end timer here
        decimal_time = (end_time - start_time).total_seconds()
        process_time = f"{decimal_time} sec"

        schedule_text = _optimize_schedule(context)

        # Existing violations
        violations = _check_violations(pedagogues, assistants, helpers)

        # NEW: Output completeness
        completeness_result = _check_output_completeness(schedule_text, context)

        # NEW: Fairness
        fairness_result = _calculate_fairness_score(schedule_text, context)

        # NEW: Coverage
        coverage_result = _calculate_coverage_score(schedule_text, context)

        return JsonResponse({
            'Gpt_provided_schedule': schedule_text,
            'Correction Time': process_time,
            'Hard Rule Violation Count': violations if violations else "0",
            'Output Completeness': completeness_result,
            'Fairness Score': fairness_result,
            'Coverage Score': coverage_result,
            "model":'o3-reasoning-model',
        })

    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "message": "Something went wrong while processing the schedule input."
        }, status=400)


def _collect_context_from_request(request):
    "Extracts the full scheduling input as a dict."
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except Exception as e:
            raise ValueError("Invalid JSON data") from e
        
    # STAFF
    staff_counts = {
        "total_staff": int(body.get("total_staff", 13)),
        "no_of_pedagogues": int(body.get("no_of_pedagogues", 6)),
        "no_of_assistants": int(body.get("no_of_assistants", 5)),
        "no_of_helpers": int(body.get("no_of_helpers", 2)),
    }

    pedagogues = []
    for i in range(1, staff_counts["no_of_pedagogues"] + 1):
        pedagogues.append({
            "name": body.get(f"pedagogue_name_{i}", f"Pedagogue {i}"),
            "age": body.get(f"pedagogue_age_{i}", "N/A"),
            "shift_time": body.get(f"pedagogue_shift_time_{i}", "N/A"),
        })

    assistants = []
    for i in range(1 , staff_counts["no_of_assistants"] + 1):
        assistants.append({
            "name": body.get(f"assistant_name_{i}", f"Assistant {i}"),
            "age": body.get(f"assistant_age_{i}", "N/A"),
            "shift_time": body.get(f"assistant_shift_time_{i}", "N/A"),
        })

    helpers = []
    for i in range(1, staff_counts["no_of_helpers"] + 1 ):
        helpers.append({
            "name": body.get(f"helper_name_{i}", f"Helper {i}"),
            "age": body.get(f"helper_age_{i}", "N/A"),
            "shift_time": body.get(f"helper_shift_time_{i}", "N/A"),
        })

    context = {
        "staff_counts": staff_counts,
        "pedagogues": pedagogues,
        "assistants": assistants,
        "helpers": helpers,
        
        # ROOMS
        "rooms": {
            "total_rooms": int(body.get("rooms", 4)),
            "V1_V2": "Infant rooms (10–30 months)",
            "B1_B2": "Preschool rooms (2 years 10 months – 5 years)",
            "required_ratio": {
                "infants": "1 adult per 3 children",
                "preschoolers": "1 adult per 6 children"
            },
            "pedagogue_required": True
        },
        "schedule_blocks": [
            {"time": "07:00–08:00", "activity": "Opening (rooms merged)", "notes": "3 adults total (≥2 Pedagogues)"},
            {"time": "08:00–09:00", "activity": "Free play, breakfast", "notes": "Rooms split; floaters help"},
            {"time": "09:00–11:00", "activity": "Planned activities", "notes": "Core staffing; outings possible"},
            {"time": "11:00–13:00", "activity": "Lunch + naps", "notes": "Breaks begin; floaters cover"},
            {"time": "13:00–15:30", "activity": "Outdoor play / excursions", "notes": "Assistants may swap"},
            {"time": "15:30–Close", "activity": "Pick-up + merge", "notes": "Reduced staffing allowed"},
            {"time": "Friday 16:15–16:30", "activity": "Clean-up", "notes": "Rotated among staff"}
        ],
        "schedule_time": [
            {"time": "07:00–08:00"},
            {"time": "08:00–09:00"},
            {"time": "09:00–11:00"},
            {"time": "11:00–13:00"},
            {"time": "13:00–15:30"},
            {"time": "15:30–Close"},
            {"time": "16:15–16:30"}
        ],
        # CONSTRAINTS
        "constraints": {
            "hard_constraints": [
                "No staff can work more than 6 hours continuously without a 30-minute break",
                "At least 1 Pedagogue must be present in every room",
                "Helpers cannot be alone",
                "Staff must meet their contract hours within ±0.25h"
            ],
            
            "soft_constraints": [
                "Avoid same staff opening and closing same day",
                "Max 3 opens or 3 closes per person weekly",
                "Distribute Friday clean-up shifts fairly",
                "Respect role/room preferences where possible"
            ],
            "individual_availability": [
                {"staff": "P1", "note": "Cannot open on Mondays"},
                {"staff": "P4", "note": "Not available on Fridays"},
                {"staff": "P6", "note": "Only works Mon–Wed, 07:00–13:00"},
                {"staff": "A1", "note": "School on Wednesdays, 07:00–10:00"},
                {"staff": "H2", "note": "Only works 09:00–13:00"},
            ]
        },
        "success_criteria": {
            "legal_compliance": "No live-ratio breaches",
            "shift_quality": "≥85% of shifts pass on first run",
            "manager_effort": "Schedule editable/finalized in under 10 minutes",
            "fairness": "Even distribution of late shifts (max 1 difference over 4 weeks)"
        },
        "llm_instruction": (
            "Using the staff details, room setup, constraints, and availability, generate a weekly schedule "
            "that assigns each staff member to appropriate shifts. Ensure legal ratios are met, breaks are handled, "
            "and special constraints are respected. Schedule must be complete by Thursday noon with minimal edits needed."
        )
    }
    
    return context, pedagogues, assistants, helpers

def _check_violations(pedagogues, assistants, helpers):
    violations = []

    # Example check 1: Ensure at least one pedagogue exists
    if len(pedagogues) == 0:
        violations.append("At least one pedagogue must be scheduled.")

    # Example check 2: Assistants cannot be alone
    # For demo, just check if assistants list is empty or not - adjust per your logic
    if len(assistants) == 0:
        violations.append("Assistants cannot be scheduled alone.")

    # Example check 3: Helpers cannot work alone (adjust as per your logic)
    if len(helpers) == 0:
        violations.append("Helpers cannot work alone.")
    
    return violations
        
def _optimize_schedule(context):
    
        "Sends the scheduling context to GPT and returns optimized schedule."
        base_system = (
            "You are a scheduling optimization assistant. "
            "Based on the provided kindergarten staff, rooms, and constraints, generate a legal and fair weekly schedule."
        )

        user_msg = f"Here is the schedule input data for optimization:\n{json.dumps(context, indent=2)}"
        logger.info(f"{user_msg}")

        response = openai.ChatCompletion.create(
            model="o3",
            messages=[
                {"role": "system", "content": base_system},
                {"role": "user", "content": user_msg}
            ]
        )
        logger.info(f"- Response : {context}, Trying to refine it.")
        

        return response['choices'][0]['message']['content']


def time_to_minutes(t):
    # Convert 'HH:MM' or 'HH:MM–HH:MM' string parts to minutes since midnight
    h, m = map(int, t.split(':'))
    return h * 60 + m

def parse_time_block(block_str):
    # Parse time range like '07:00–08:00' or '15:30–Close' (handle Close as 24:00)
    start_str, end_str = block_str.split('–')
    start = time_to_minutes(start_str)
    if end_str.lower() == 'close':
        end = 24 * 60
    else:
        end = time_to_minutes(end_str)
    return (start, end)

def _check_output_completeness(schedule_text, context):
    try:
        schedule_lower = schedule_text.lower()

        # Check for missing staff names (keep your existing logic)
        staff_names = [p["name"] for p in context["pedagogues"]] + \
                    [a["name"] for a in context["assistants"]] + \
                    [h["name"] for h in context["helpers"]]
        missing_staff = [name for name in staff_names if name.lower() not in schedule_lower]

        # Extract all time ranges from schedule_text (output)
        # Matches times like '07:00-08:00', '07:00–08:00' (dash or en dash)
        time_blocks_in_output = re.findall(r'(\d{2}:\d{2})\s*[–-]\s*(\d{2}:\d{2}|close)', schedule_lower)

        output_intervals = []
        for start_str, end_str in time_blocks_in_output:
            start = time_to_minutes(start_str)
            end = 24 * 60 if end_str == 'close' else time_to_minutes(end_str)
            output_intervals.append((start, end))

        def is_block_covered(block_start, block_end, intervals):
            # Check if this block is fully inside any output interval
            for (start, end) in intervals:
                if block_start >= start and block_end <= end:
                    return True
            return False

        # Check each defined schedule block if it is covered
        missing_blocks = []
        for block in context["schedule_time"]:
            block_start, block_end = parse_time_block(block["time"].lower())
            if not is_block_covered(block_start, block_end, output_intervals):
                missing_blocks.append(block["time"])

        return {
            "status": "Complete" if not missing_staff and not missing_blocks else "Incomplete",
            "missing_staff": missing_staff,
            "missing_blocks": missing_blocks
        }

    except Exception as e:
        return {
            "status": "Error",
            "error": str(e)
        }

def _calculate_fairness_score(schedule_text, context):
    schedule_lower = schedule_text.lower()
    staff_names = [p["name"] for p in context["pedagogues"]] + \
                [a["name"] for a in context["assistants"]] + \
                [h["name"] for h in context["helpers"]]
    
    shift_counts = {name: schedule_lower.count(name.lower()) for name in staff_names}
    shifts = list(shift_counts.values())
    
    if not shifts:
        return {"score": 0, "message": "No staff found in schedule"}

    fairness_score = 1 - (max(shifts) - min(shifts)) / max(1, sum(shifts))
    return {"score": round(fairness_score * 100, 2), "details": shift_counts}


def _calculate_coverage_score(schedule_text, context):
    schedule_lower = schedule_text.lower()
    blocks = [block["time"] for block in context["schedule_blocks"]]
    
    covered_blocks = [b for b in blocks if b.lower() in schedule_lower]
    score = len(covered_blocks) / len(blocks) * 100

    return {
        "score": round(score, 2),
        "covered_blocks": covered_blocks,
        "total_blocks": len(blocks)
    }
    
# What is the details object?
# The "details" object shows:
# How many times each staff member is scheduled throughout the week. Think of it like a workload count or number of assignments per person.
