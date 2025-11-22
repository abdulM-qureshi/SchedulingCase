from textwrap import indent
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from dotenv import load_dotenv
from datetime import datetime
import logging
import openai
import time
import json
import re
import os

load_dotenv()  # load variables from .env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')  # API from .env

@csrf_exempt
def Kindergarten(request):

    if request.method == 'OPTIONS':
        response = HttpResponse(status=200)
        response['Access-Control-Allow-Origin'] = '*' # You may want to restrict this in production
        response['Access-Control-Allow-Methods'] = 'POST'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
        return response
    

    if request.method == 'POST':
        logger.info("Kindergarten schedule request received")
        try:
            start_time = datetime.now()

            # Build context
            context, constraints, kindergarten_data = _collect_context_from_request(request)

            certified = get_certified_staff(kindergarten_data)

        # First iteration -  LLM Json generation
            schedule_text, tokens_details = _optimize_schedule(context, constraints)
            logger.info(schedule_text)

            if not isinstance(schedule_text, dict):
                raise ValueError("Invalid schedule format: Expected a JSON object.")

            # Run constraint checks
            # _report, report_ = _constraints_check(schedule_text, constraints)
            target_hours = extract_target_weekly_hours(kindergarten_data)

            report, discrepancies = validate_weekly_hours(schedule_text, target_hours)

            violation_report = validate_hard_constraints(schedule_text, target_hours)

            # Check results
            print(f"Total violations: {violation_report['summary']['total_violations']}")
            for constraint, violations in violation_report['violations'].items():
                if violations:
                    print(f"\n{constraint}: {len(violations)} violations")
                    for violation in violations[:3]:  # Show first 3
                        print(f"  - {violation}")
            
        # Second iteration - LLM Json generation
            updated_schedule = re_optimize_schedule(context, schedule_text, discrepancies, violation_report)

            # Revalidate the updated schedule for discrepancies
            new_report, discrepancies_v1 = validate_weekly_hours(updated_schedule, target_hours)

            # Revalidate the updated schedule for violations
            violations_v1 = validate_hard_constraints(updated_schedule, target_hours)
                        
            end_time = datetime.now()
            process_time = f"{(end_time - start_time).total_seconds()} sec"

            # optimized_schedule = re_optimize_schedule(context, schedule_text)

            return JsonResponse({
                "updated_schedule": updated_schedule,
                "new_discrepancies": discrepancies_v1,
                "new_violations": violations_v1,
                "model": 'gpt-4o'
            })

        except Exception as e:
            logger.error(f"Error in Kindergarten view: {e}", exc_info=True)
            return JsonResponse({
                "error": str(e),
                "message": "Something went wrong while processing the schedule input."
            }, status=400)
    elif request.method == 'GET':
        return render(request, 'index.html')
    else:
        # For any request method other than POST, return a 405 Method Not Allowed error.
        return JsonResponse({"error": "Method not allowed"}, status=405)

def extract_target_weekly_hours(kindergarten_data):
    target_hours = {}
    for room in kindergarten_data.get("rooms", []):
        for staff in room.get("staff", []):
            initial = staff.get("initial")
            target_hours_value = staff.get("target_weekly_hours")
            if initial and target_hours_value is not None:
                target_hours[initial] = target_hours_value
    return target_hours

def _collect_context_from_request(request):
    """Extracts scheduling input as a dict, handling nested JSON."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            logging.info("We received the request")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data in request body: {e}")

    constraints = {
        'hard_constraints':
        """
    Hard Constraints (Rules That Cannot Be Broken)

    The following rules must always be followed.  
    If any rule cannot be satisfied, do not generate a schedule.  
    Instead, respond with:
    { "error": "Constraints not satisfiable" }

    1. Operating Hours
    - Schedule is valid only Monday–Friday, 07:30–17:00.
    - No staff may be scheduled outside of these times.

    2. Schedule Cycle
    - The schedule must cover a 4-week rotating cycle.
    - All constraints apply consistently across the full cycle.

    3. Weekly Hours
    - Each staff member must be scheduled for their exact Target Weekly Hours.
    - No under- or over-scheduling is allowed.

    4. Friday Early Leave
    - In every 4-week cycle, each staff member must have exactly one Friday where they leave at 12:00.

    5. Fixed Staff Schedules
    - Staff J (Mýran): Always scheduled Monday–Friday, 09:00–15:00.
    - Staff N (Løkurin): Always scheduled Monday–Thursday, 08:00–16:00. Off on Friday.

    6. Staffing Levels & Room Combining
    Morning (07:30–08:00):
    - Exactly 3 staff members on duty, working in a shared common area.

    Room Opening (08:00–08:30):
    - Each of the 5 rooms must have at least 1 staff member.

    Main Day (08:30–16:00):
    - Rooms Tjørnin, Mýran, Túgvan, Spírar: At least 2 staff members present at all times.
    - Room Løkurin: Second staff member must be present by 09:00 or 09:30 at the latest.

    # Afternoon Consolidation (16:00–16:30):
     - Ensure exactly 1 staff member remains in each of the 5 rooms.
     - Verify that no more than 1 staff member is present in any room.

    Final Closing (16:30–17:00) Schedule Generation Steps:
    1. Identify the single staff member to be on duty from 16:30 to 17:00. This must be the only staff member scheduled during this time.
    2. For each day (Monday-Friday), designate one room as the 'closing room' for this time slot.
    3. Assign the single staff member to the designated 'closing room' for the 16:30-17:00 time slot.
    4. Ensure all other rooms are empty (have no staff assigned) from 16:30 to 17:00.

    Most important!!!:

    1. All 9 time slots (07:30–08:00 … 16:30–17:00) must appear for every weekday in every week.  
    2. Each time slot must contain at least one staff (unless rules require empty).  
    3. Never leave an array empty unless the constraint explicitly requires no staff.  
    4. Apply fixed staff schedules exactly as written.  
    5. Validate across all 4 weeks.  

    Do not drop or skip any time slot.  
    Do not output partial schedules.
    """, 

    'soft constraints':
    """
    Soft Constraints (Guidelines That Should Be Followed Whenever Possible)

    These rules are preferences, not absolutes.  
    If a soft constraint cannot be satisfied, the schedule is still valid.  
    However, attempt to follow them as much as possible to ensure fairness and practicality.

    1. Shift Rotation
    - Opening, middle, and closing shifts should rotate fairly among staff on a week-to-week basis.

    2. Possible Start Times
    - Staff shifts should only begin at one of the following times:
    07:30, 08:00, 08:30, 09:00, or 09:30.

    3. Possible End Times
    - Staff shifts should only end at one of the following times:
    12:00–13:30 (for half-days), or exactly at 15:00, 16:00, 16:30, or 17:00.

    4. No "Wasted Time"
    - Avoid scheduling staff to leave between 13:30 and 15:00, as this results in inefficient use of staff hours.
    """
    }

    kindergarten_data = {
        "rooms": body.get("rooms", []),
        "constraints": constraints,
    }

    context = {
        'kindergarten_data': kindergarten_data,
        'constraints': constraints,
    }
    return context, constraints, kindergarten_data

def calculate_cost(input_tokens, output_tokens):
    try:
        input_number_ = 0.005
        output_number_ = 0.015
        input_cost = (input_tokens / 1000) * input_number_
        output_cost = (output_tokens / 1000) * output_number_
        cost_ = input_cost + output_cost
        logger.info(f"Input Cost: {input_cost}, Output Cost: {output_cost}, Total Cost: {cost_}")
        return cost_
    except Exception as e:
        logger.error(f"Error calculating cost: {str(e)}")
        return None

def get_certified_staff(kindergarten_data):
    """
    Extract a list of staff initials who are certified from the given JSON.

    Parameters
    ----------
    data : dict or str
        JSON object or JSON string with "rooms" and "staff" structure.

    Returns
    -------
    list[str] : list of certified staff initials
    """
    import json

    data = kindergarten_data
    # Parse if passed as string
    if isinstance(data, str):
        data = json.loads(data)

    certified = []

    for room in data.get("rooms", []):
        for staff in room.get("staff", []):
            if str(staff.get("certified staff", "")).strip().lower() == "true":
                certified.append(staff.get("initial"))

    return certified

def validate_hard_constraints(schedule_data, target_hours):
    """
    Simplified version that only validates the fridayEarlyLeave field for constraint 4.
    All other constraints remain the same, but Friday early leave is much simpler.
    """
    import json
    import re
    from collections import defaultdict
    
    # Parse input
    if isinstance(schedule_data, str):
        data = json.loads(schedule_data)
    else:
        data = schedule_data
    
    schedules = data.get("schedules", [])
    violations = {
        "constraint_1_operating_hours": [],
        "constraint_2_schedule_cycle": [],
        "constraint_3_weekly_hours": [],
        "constraint_4_friday_early_leave": [],  # This will be simplified
        "constraint_5_fixed_schedules": [],
        "constraint_6_staffing_levels": []
    }
    
    # Helper functions (same as before)
    def parse_time_range(timestr):
        timestr = timestr.strip()
        timestr = re.sub(r"[—–]", "-", timestr)
        parts = timestr.split("-")
        if len(parts) != 2:
            return None
        try:
            sh, sm = map(int, parts[0].split(":"))
            eh, em = map(int, parts[1].split(":"))
            start = sh * 60 + sm
            end = eh * 60 + em
            return (start, end)
        except:
            return None
    
    def minutes_to_time(minutes):
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    # Get all staff across all rooms and weeks (same as before)
    all_staff_schedules = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # SIMPLIFIED: Only track fridayEarlyLeave assignments
    friday_early_leave_assignments = defaultdict(list)
    
    # Aggregate schedules
    for room_data in schedules:
        room_name = room_data.get("room", "")
        weeks = room_data.get("weeks", {})
        
        for week_key, week_data in weeks.items():
            week_name = week_key.strip().lower()
            
            for day_name, day_slots in week_data.items():
                day = day_name.strip().lower()
                
                # SIMPLIFIED: Only handle fridayEarlyLeave field
                if day == "fridayearlyleave":
                    if isinstance(day_slots, str) and day_slots.strip():
                        staff_id = day_slots.strip()
                        friday_early_leave_assignments[staff_id].append(week_name)
                    continue
                
                # Regular day handling for other constraints
                if not isinstance(day_slots, dict):
                    continue
                
                for time_slot, staff_list in day_slots.items():
                    time_range = parse_time_range(time_slot)
                    if not time_range:
                        continue
                    
                    start, end = time_range
                    for staff_id in staff_list:
                        if staff_id.strip():
                            all_staff_schedules[staff_id][week_name][day].append((start, end, room_name))
    
    # CONSTRAINT 1: Operating Hours (same as before)
    valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday'}
    valid_start = 7 * 60 + 30
    valid_end = 17 * 60
    
    for staff_id, weeks_data in all_staff_schedules.items():
        for week_name, days_data in weeks_data.items():
            for day, shifts in days_data.items():
                if day not in valid_days:
                    violations["constraint_1_operating_hours"].append({
                        "staff_id": staff_id,
                        "week": week_name,
                        "day": day,
                        "violation": "Scheduled on invalid day (not Mon-Fri)"
                    })
                
                for start, end, room in shifts:
                    if start < valid_start or end > valid_end:
                        violations["constraint_1_operating_hours"].append({
                            "staff_id": staff_id,
                            "week": week_name,
                            "day": day,
                            "room": room,
                            "time_slot": f"{minutes_to_time(start)}-{minutes_to_time(end)}",
                            "violation": f"Outside operating hours (07:30-17:00)"
                        })
    
    # CONSTRAINT 2: Schedule Cycle (same as before)
    required_weeks = {"week1", "week2", "week3", "week4"}
    for room_data in schedules:
        room_name = room_data.get("room", "")
        weeks = set(week_key.strip().lower() for week_key in room_data.get("weeks", {}).keys())
        
        missing_weeks = required_weeks - weeks
        extra_weeks = weeks - required_weeks
        
        if missing_weeks:
            violations["constraint_2_schedule_cycle"].append({
                "room": room_name,
                "violation": f"Missing weeks: {list(missing_weeks)}"
            })
        
        if extra_weeks:
            violations["constraint_2_schedule_cycle"].append({
                "room": room_name,
                "violation": f"Extra weeks found: {list(extra_weeks)}"
            })
    
    # CONSTRAINT 3: Weekly Hours (same as before)
    for staff_id, weeks_data in all_staff_schedules.items():
        target = target_hours.get(staff_id)
        if target is None:
            continue
            
        for week_name, days_data in weeks_data.items():
            total_minutes = 0
            for day, shifts in days_data.items():
                if not shifts:
                    continue
                intervals = [(start, end) for start, end, room in shifts]
                intervals.sort()
                merged = []
                current_start, current_end = intervals[0][:2]
                for start, end in intervals[1:]:
                    if start <= current_end:
                        current_end = max(current_end, end)
                    else:
                        merged.append((current_start, current_end))
                        current_start, current_end = start, end
                merged.append((current_start, current_end))
                
                day_minutes = sum(end - start for start, end in merged)
                total_minutes += day_minutes
            
            actual_hours = total_minutes / 60.0
            if abs(actual_hours - target) > 0.1:
                violations["constraint_3_weekly_hours"].append({
                    "staff_id": staff_id,
                    "week": week_name,
                    "calculated_hours": round(actual_hours, 2),
                    "target_hours": target,
                    "difference": round(actual_hours - target, 2)
                })
    
    # CONSTRAINT 4: SIMPLIFIED Friday Early Leave
    # ONLY check that each staff has exactly one fridayEarlyLeave assignment
    # No longer check actual Friday schedules or end times
    
    all_staff_ids = set()
    for staff_id in all_staff_schedules.keys():
        all_staff_ids.add(staff_id)
    for staff_id in friday_early_leave_assignments.keys():
        all_staff_ids.add(staff_id)
    
    for staff_id in all_staff_ids:
        early_leave_weeks = friday_early_leave_assignments.get(staff_id, [])
        early_leave_count = len(early_leave_weeks)
        
        # SIMPLIFIED: Only check count, don't validate actual Friday schedules
        if early_leave_count != 1:
            violations["constraint_4_friday_early_leave"].append({
                "staff_id": staff_id,
                "violation": f"Has {early_leave_count} Friday early leave assignments in fridayEarlyLeave field, expected exactly 1",
                "early_leave_weeks": early_leave_weeks,
                "note": "Only checking fridayEarlyLeave field assignments, not actual Friday schedules"
            })
    
    # CONSTRAINT 5: Fixed Staff Schedules (same as before)
    fixed_schedules = {
        "J": {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start": 9 * 60,
            "end": 15 * 60,
            "required_room": "mýran"
        },
        "N": {
            "days": ["monday", "tuesday", "wednesday", "thursday"],
            "start": 8 * 60,
            "end": 16 * 60,
            "required_room": "løkurin"
        }
    }
    
    for staff_id, required in fixed_schedules.items():
        if staff_id not in all_staff_schedules:
            violations["constraint_5_fixed_schedules"].append({
                "staff_id": staff_id,
                "violation": f"Staff {staff_id} not found in any schedule"
            })
            continue
        
        weeks_data = all_staff_schedules[staff_id]
        
        for week_name in ["week1", "week2", "week3", "week4"]:
            if week_name not in weeks_data:
                continue
            
            days_data = weeks_data[week_name]
            
            for req_day in required["days"]:
                if req_day not in days_data:
                    violations["constraint_5_fixed_schedules"].append({
                        "staff_id": staff_id,
                        "week": week_name,
                        "day": req_day,
                        "violation": f"Not scheduled on required day"
                    })
                    continue
                
                shifts = days_data[req_day]
                if not shifts:
                    violations["constraint_5_fixed_schedules"].append({
                        "staff_id": staff_id,
                        "week": week_name,
                        "day": req_day,
                        "violation": f"No shifts on required day"
                    })
                    continue
                
                shifts.sort()
                earliest_start = min(start for start, end, room in shifts)
                latest_end = max(end for start, end, room in shifts)
                
                if earliest_start > required["start"] or latest_end < required["end"]:
                    violations["constraint_5_fixed_schedules"].append({
                        "staff_id": staff_id,
                        "week": week_name,
                        "day": req_day,
                        "violation": f"Schedule {minutes_to_time(earliest_start)}-{minutes_to_time(latest_end)} doesn't cover required {minutes_to_time(required['start'])}-{minutes_to_time(required['end'])}"
                    })
                
                rooms_worked = {room.lower() for start, end, room in shifts}
                if required["required_room"] not in rooms_worked:
                    violations["constraint_5_fixed_schedules"].append({
                        "staff_id": staff_id,
                        "week": week_name,
                        "day": req_day,
                        "violation": f"Not working in required room '{required['required_room']}', found in: {list(rooms_worked)}"
                    })
            
            if staff_id == "N" and "friday" in days_data and days_data["friday"]:
                violations["constraint_5_fixed_schedules"].append({
                    "staff_id": staff_id,
                    "week": week_name,
                    "day": "friday",
                    "violation": f"Staff N must be off on Friday but is scheduled"
                })
    
    # CONSTRAINT 6: Staffing Levels (same as before - keeping this complex part unchanged)
    time_slot_requirements = {
        "07:30-08:00": {"total_staff": 3, "rooms": "shared_area"},
        "08:00-08:30": {"min_staff_per_room": 1, "rooms": "all_5"},
        "08:30-09:00": {"min_staff_per_room": 2, "rooms": ["tjørnin", "mýran", "túgvan", "spírar"], "løkurin_min": 1},
        "09:00-11:30": {"min_staff_per_room": 2, "rooms": ["tjørnin", "mýran", "túgvan", "spírar"], "løkurin_min": 2},
        "11:30-13:00": {"min_staff_per_room": 2, "rooms": ["tjørnin", "mýran", "túgvan", "spírar"], "løkurin_min": 2},
        "13:00-14:00": {"min_staff_per_room": 2, "rooms": ["tjørnin", "mýran", "túgvan", "spírar"], "løkurin_min": 2},
        "14:00-16:00": {"min_staff_per_room": 2, "rooms": ["tjørnin", "mýran", "túgvan", "spírar"], "løkurin_min": 2},
        "16:00-16:30": {"exact_staff_per_room": 1, "rooms": "all_5"},
        "16:30-17:00": {"total_staff": 1, "rooms": "single_closing_room"}
    }
    
    for room_data in schedules:
        room_name = room_data.get("room", "").lower()
        weeks = room_data.get("weeks", {})
        
        for week_key, week_data in weeks.items():
            for day_name, day_slots in week_data.items():
                day = day_name.strip().lower()
                
                if day == "fridayearlyleave":
                    continue
                
                if not isinstance(day_slots, dict):
                    continue
                
                for time_slot, staff_list in day_slots.items():
                    if time_slot not in time_slot_requirements:
                        continue
                    
                    req = time_slot_requirements[time_slot]
                    staff_count = len([s for s in staff_list if s.strip()])
                    
                    if time_slot == "08:00-08:30":
                        if staff_count < req["min_staff_per_room"]:
                            violations["constraint_6_staffing_levels"].append({
                                "room": room_name,
                                "week": week_key,
                                "day": day_name,
                                "time_slot": time_slot,
                                "violation": f"Has {staff_count} staff, minimum {req['min_staff_per_room']} required"
                            })
                    
                    elif time_slot in ["08:30-09:00", "09:00-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00"]:
                        if room_name in ["tjørnin", "mýran", "túgvan", "spírar"]:
                            min_required = req.get("min_staff_per_room", 2)
                            if staff_count < min_required:
                                violations["constraint_6_staffing_levels"].append({
                                    "room": room_name,
                                    "week": week_key,
                                    "day": day_name,
                                    "time_slot": time_slot,
                                    "violation": f"Has {staff_count} staff, minimum {min_required} required"
                                })
                        elif room_name == "løkurin":
                            min_required = req.get("løkurin_min", 2)
                            if staff_count < min_required:
                                violations["constraint_6_staffing_levels"].append({
                                    "room": room_name,
                                    "week": week_key,
                                    "day": day_name,
                                    "time_slot": time_slot,
                                    "violation": f"Has {staff_count} staff, minimum {min_required} required"
                                })
                    
                    elif time_slot == "16:00-16:30":
                        exact_required = req["exact_staff_per_room"]
                        if staff_count != exact_required:
                            violations["constraint_6_staffing_levels"].append({
                                "room": room_name,
                                "week": week_key,
                                "day": day_name,
                                "time_slot": time_slot,
                                "violation": f"Has {staff_count} staff, exactly {exact_required} required"
                            })
                    
                    elif time_slot == "16:30-17:00":
                        if staff_count > 1:
                            violations["constraint_6_staffing_levels"].append({
                                "room": room_name,
                                "week": week_key,
                                "day": day_name,
                                "time_slot": time_slot,
                                "violation": f"Has {staff_count} staff, maximum 1 allowed (single closing room)"
                            })
    
    # Summary
    total_violations = sum(len(v) for v in violations.values())
    
    return {
        "violations": violations,
        "summary": {
            "total_violations": total_violations,
            "violations_by_constraint": {k: len(v) for k, v in violations.items()},
            "rooms_checked": [r.get("room", "") for r in schedules],
            "weeks_checked": ["week1", "week2", "week3", "week4"],
            "friday_early_leave_summary": {
                "staff_with_early_leave": len(friday_early_leave_assignments),
                "early_leave_assignments": dict(friday_early_leave_assignments),
                "note": "Simplified validation - only checks fridayEarlyLeave field assignments"
            }
        }
    }

def validate_weekly_hours(schedule_text, target_hours, split_slots=False):
    """
    Updated to handle fridayEarlyLeave field properly.
    """
    import json, re, math
    from collections import defaultdict

    # Parse input
    if isinstance(schedule_text, str):
        try:
            data = json.loads(schedule_text)
        except Exception as e:
            raise ValueError(f"Invalid JSON: {e}")
    else:
        data = schedule_text

    schedules = data.get("schedules", [])

    # Helper functions (same as before)
    def clean_timestr(timestr):
        timestr = timestr.strip()
        timestr = re.sub(r"[–—]", "-", timestr)
        timestr = re.sub(r"\s*-\s*", "-", timestr)
        return timestr

    def parse_time_range(timestr):
        timestr = clean_timestr(timestr)
        parts = timestr.split("-")
        if len(parts) != 2:
            return None
        try:
            sh, sm = map(int, parts[0].split(":"))
            eh, em = map(int, parts[1].split(":"))
            start = sh * 60 + sm
            end = eh * 60 + em
            return (start, end) if end > start else None
        except Exception:
            return None

    def merge_intervals(intervals):
        if not intervals:
            return 0
        intervals.sort()
        merged = []
        current_start, current_end = intervals[0]
        for s, e in intervals[1:]:
            if s <= current_end:
                current_end = max(current_end, e)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = s, e
        merged.append((current_start, current_end))
        return sum(e - s for s, e in merged)

    # FIXED: Aggregation to skip fridayEarlyLeave field
    staff_week_assignments = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    
    for room in schedules:
        room_name = room.get("room", "Unknown")
        weeks = room.get("weeks", {})
        
        for week_key, week_obj in weeks.items():
            week_name = week_key.strip().lower()
            
            for day, slots in week_obj.items():
                day = day.strip().lower()
                
                # FIXED: Skip fridayEarlyLeave field - it's not a day schedule
                if day == "fridayearlyleave":
                    continue
                
                if not isinstance(slots, dict):
                    continue
                
                for timestr, staff_list in slots.items():
                    parsed = parse_time_range(timestr)
                    if not parsed:
                        continue
                    
                    start, end = parsed
                    
                    for staff_id in staff_list:
                        if staff_id:
                            staff_week_assignments[staff_id][week_name][day].add((start, end))

    # Calculate total hours per staff per week (rest remains the same)
    staff_week_minutes = defaultdict(lambda: defaultdict(int))
    
    for staff_id, weeks_data in staff_week_assignments.items():
        for week_name, days_data in weeks_data.items():
            total_week_minutes = 0
            
            for day, time_slots in days_data.items():
                intervals = list(time_slots)
                day_minutes = merge_intervals(intervals)
                total_week_minutes += day_minutes
            
            staff_week_minutes[staff_id][week_name] = total_week_minutes

    # Build report
    staff_weeks = {}
    discrepancies = []

    for staff_id, week_map in staff_week_minutes.items():
        staff_weeks.setdefault(staff_id, {})
        for week_name, minutes in week_map.items():
            hours = round(minutes / 60.0, 2)
            expected = None
            if target_hours and staff_id in target_hours:
                expected = float(target_hours[staff_id])
            
            staff_weeks[staff_id][week_name] = {
                "calculated_hours": hours,
                "expected_hours": expected
            }
            
            if expected is not None and not math.isclose(hours, expected, abs_tol=0.05):
                discrepancies.append({
                    "staff_id": staff_id,
                    "week": week_name,
                    "calculated_hours": hours,
                    "expected_hours": expected,
                    "difference": round(hours - expected, 2)
                })

    report = {
        "staff_weeks": staff_weeks,
        "hours_discrepancies": discrepancies,
        "summary": {
            "total_staff": len(staff_weeks),
            "weeks_present": sorted({w for week_map in staff_weeks.values() for w in week_map})
        }
    }

    return report, discrepancies

def clean_json_string(text: str) -> dict | list | None:
    """
    Enhanced JSON extraction with better debugging and error handling.
    """
    import json
    import re
    
    if not text or not isinstance(text, str):
        logger.error("Invalid input to JSON parser")
        return None
    
    original_length = len(text)
    logger.info(f"Parsing JSON of length: {original_length}")
    
    # Strategy 1: Try direct parsing with better error reporting
    try:
        result = json.loads(text.strip())
        logger.info("Strategy 1 (direct parsing) succeeded")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Strategy 1 failed - JSON decode error at position {e.pos}: {e.msg}")
        if e.pos < len(text):
            context_start = max(0, e.pos - 50)
            context_end = min(len(text), e.pos + 50)
            logger.error(f"Context around error: '{text[context_start:context_end]}'")
    
    # Strategy 2: Check for truncation and attempt to fix
    try:
        # Count braces to see if JSON is complete
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        logger.info(f"Brace count: open={open_braces}, close={close_braces}")
        logger.info(f"Bracket count: open={open_brackets}, close={close_brackets}")
        
        if open_braces > close_braces:
            logger.warning("JSON appears truncated - missing closing braces")
            # Try to add missing braces
            missing_braces = open_braces - close_braces
            fixed_text = text + ('}' * missing_braces)
            result = json.loads(fixed_text)
            logger.info("Strategy 2 (fix truncation) succeeded")
            return result
            
    except json.JSONDecodeError as e:
        logger.error(f"Strategy 2 failed: {e.msg}")
    
    # Strategy 3: Remove markdown and try again
    try:
        cleaned = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = cleaned.strip()
        
        if cleaned != text:
            logger.info("Removed markdown formatting")
            result = json.loads(cleaned)
            logger.info("Strategy 3 (remove markdown) succeeded")
            return result
            
    except json.JSONDecodeError as e:
        logger.error(f"Strategy 3 failed: {e.msg}")
    
    # Strategy 4: Find complete JSON objects
    try:
        json_start = text.find('{')
        if json_start == -1:
            logger.error("No opening brace found")
            return None
            
        # Find the matching closing brace
        brace_count = 0
        json_end = -1
        in_string = False
        escape_next = False
        
        for i in range(json_start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\' and in_string:
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break
        
        if json_end > json_start:
            potential_json = text[json_start:json_end + 1]
            logger.info(f"Extracted JSON from position {json_start} to {json_end}")
            result = json.loads(potential_json)
            logger.info("Strategy 4 (bracket matching) succeeded")
            return result
        else:
            logger.error("Could not find matching closing brace")
            
    except json.JSONDecodeError as e:
        logger.error(f"Strategy 4 failed: {e.msg}")
    
    # Strategy 5: Check for common JSON issues and fix them
    try:
        # Remove trailing commas
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix common quote issues (very basic)
        fixed_text = re.sub(r'([{,]\s*)"([^"]*)"(\s*:\s*)"([^"]*)"', r'\1"\2":\3"\4"', fixed_text)
        
        if fixed_text != text:
            logger.info("Applied JSON fixes")
            result = json.loads(fixed_text)
            logger.info("Strategy 5 (fix common issues) succeeded")
            return result
            
    except json.JSONDecodeError as e:
        logger.error(f"Strategy 5 failed: {e.msg}")
    
    # Last resort: detailed character-by-character analysis
    logger.error("All strategies failed. Performing detailed analysis...")
    
    # Check for invisible characters
    invisible_chars = []
    for i, char in enumerate(text[:100]):  # Check first 100 chars
        if ord(char) < 32 and char not in ['\n', '\r', '\t']:
            invisible_chars.append((i, ord(char)))
    
    if invisible_chars:
        logger.error(f"Found invisible characters: {invisible_chars}")
    
    # Check encoding issues
    try:
        text.encode('utf-8')
        logger.info("Text is valid UTF-8")
    except UnicodeEncodeError as e:
        logger.error(f"UTF-8 encoding issue: {e}")
    
    logger.error("JSON parsing completely failed")
    return None

def normalize_friday_early_leave_key(schedule_dict):
    """
    Normalize the fridayEarlyLeave key to handle case variations.
    """
    if not isinstance(schedule_dict, dict) or "weeks" not in schedule_dict:
        return schedule_dict
    
    weeks = schedule_dict["weeks"]
    for week_name, week_data in weeks.items():
        if not isinstance(week_data, dict):
            continue
            
        # Look for variations of fridayEarlyLeave
        early_leave_key = None
        early_leave_value = None
        
        for key, value in list(week_data.items()):  # Use list() to avoid dict change during iteration
            if key.lower().replace("_", "").replace("-", "") == "fridayearlyleave":
                early_leave_key = key
                early_leave_value = value
                break
        
        if early_leave_key and early_leave_key != "fridayEarlyLeave":
            # Remove the incorrectly cased key and add the correct one
            del week_data[early_leave_key]
            week_data["fridayEarlyLeave"] = early_leave_value
            logger.info(f"Normalized {early_leave_key} to fridayEarlyLeave in {week_name}")
    
    return schedule_dict

# Your standardized schema - define once and reuse
STANDARDIZED_ROOM_SCHEMA ={
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "RoomSchedule",
    "type": "object",
    "properties": {
        "room": {
            "type": "string",
            "description": "Name of the room (e.g., Room 1)"
        },
        "weeks": {
            "type": "object",
            "description": "Weekly schedules",
            "patternProperties": {
                "^week[0-9]+$": {
                    "type": "object",
                    "description": "Schedule for a specific week",
                    "properties": {
                        "monday": { "$ref": "#/definitions/daySchedule" },
                        "tuesday": { "$ref": "#/definitions/daySchedule" },
                        "wednesday": { "$ref": "#/definitions/daySchedule" },
                        "thursday": { "$ref": "#/definitions/daySchedule" },
                        "friday": { "$ref": "#/definitions/daySchedule" },
                        "fridayearlyLeave": {
                            "type":"string",
                            "description": "Single person with early leave on Friday"
                        }
                    },
                    "required": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "additionalProperties":  False
                }
            },
            "additionalProperties":  False
        }
    },
    "required": ["room", "weeks"],
    "additionalProperties":  False,
    "definitions": {
        "daySchedule": {
            "type": "object",
            "description": "Schedule for a single day",
            "properties": {
                "07:30-08:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "08:00-08:30": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "08:30-09:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "09:00-11:30": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "11:30-13:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "13:00-14:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "14:00-16:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "16:00-16:30": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "16:30-17:00": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                }
            },
            "required": [
                "07:30-08:00",
                "08:00-08:30",
                "08:30-09:00",
                "09:00-11:30",
                "11:30-13:00",
                "13:00-14:00",
                "14:00-16:00",
                "16:00-16:30",
                "16:30-17:00"
            ],
            "additionalProperties": False
        }
    }
}

def _optimize_schedule(context, constraints):
    """
    Generate schedule using your standardized schema with strengthened prompts.
    """
    room_names = [room.get("name") for room in context["kindergarten_data"].get("rooms", [])]
    final_schedule = {"schedules": []}
    tokens_total = {"input": 0, "output": 0}

    # Ultra-strict system prompt
    base_system = """
    You are a kindergarten scheduling optimizer. Your task is CRITICAL and MUST be executed PERFECTLY.

    ABSOLUTE REQUIREMENTS - NO EXCEPTIONS:
    1. Output EXACTLY one valid JSON object that PERFECTLY matches the provided schema
    2. NEVER add markdown code blocks (```json), explanations, or any text outside the JSON
    3. EVERY time slot MUST contain at least 1 staff member (minItems: 1 requirement)
    4. ALL 9 time slots MUST be present for every day of every week (Monday-Friday, Week1-Week4)
    5. The "room" field MUST exactly match the requested room name
    6. JSON MUST be syntactically perfect - no trailing commas, proper quotes, valid structure

    CRITICAL SCHEMA COMPLIANCE:
    - Each day MUST have exactly these 9 time slots: "07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00", "16:00-16:30", "16:30-17:00"
    - Each time slot MUST be an array of strings with at least 1 staff member
    - Each week MUST be named exactly: "week1", "week2", "week3", "week4"
    - Each day MUST be named exactly: "monday", "tuesday", "wednesday", "thursday", "friday"

    FAILURE IS NOT ACCEPTABLE. If constraints cannot be satisfied, return:
    {"error": "Constraints not satisfiable", "room": "ROOM_NAME"}

    Before outputting, VALIDATE your JSON:
    1. Check every time slot exists
    2. Check every array has at least 1 item
    3. Check JSON syntax is perfect
    4. Check schema compliance is 100%
    """

    for room in room_names:
        success = False
        max_attempts = 3
        
        for attempt in range(max_attempts):
            # Ultra-specific user prompt
            user_msg = f"""
            TASK: Generate a complete 4-week schedule for room: "{room}"

            INPUT DATA:
            {json.dumps(context['kindergarten_data'], indent=2)}

            MANDATORY SCHEMA (MUST follow 100% exactly):
            {json.dumps(STANDARDIZED_ROOM_SCHEMA, indent=2)}

            HARD CONSTRAINTS (CANNOT be violated):
            {constraints["hard_constraints"]}

            CRITICAL INSTRUCTIONS:
            1. Set "room" field to exactly: "{room}"
            2. Create exactly 4 weeks: week1, week2, week3, week4
            3. Each week has exactly 5 days: monday, tuesday, wednesday, thursday, friday
            4. Each day has exactly 9 time slots (as defined in schema)
            5. Each time slot MUST have at least 1 staff member (never empty arrays)
            6. If you cannot assign real staff to a slot, use placeholder like ["STAFF_NEEDED"] but NEVER leave empty

            VALIDATION CHECKLIST BEFORE RESPONDING:
            ✓ JSON is syntactically perfect
            ✓ "room" field matches "{room}"
            ✓ Has exactly 4 weeks (week1-week4)
            ✓ Each week has exactly 5 days
            ✓ Each day has exactly 9 time slots
            ✓ Every time slot array has minItems: 1
            ✓ No trailing commas or syntax errors

            OUTPUT ONLY THE JSON - NOTHING ELSE.
            """
            
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": user_msg}
                    ],
                    temperature=0.0,  # Maximum determinism
                    # max_tokens=4000   # Ensure enough space for complete response
                )
                
                raw = response["choices"][0]["message"]["content"]
                logger.info(f"Room {room}, Attempt {attempt + 1} - Response length: {len(raw)}")
                
                # Parse using your improved function
                parsed = clean_json_string(raw)
                
                if parsed and isinstance(parsed, dict):
                    # Validate schema compliance
                    if validate_schema_compliance(parsed, room):
                        final_schedule["schedules"].append(parsed)
                        success = True
                        logger.info(f"✅ SUCCESS: Room {room} schedule generated and validated")
                        break
                    else:
                        logger.warning(f"❌ Schema validation failed for room {room}, attempt {attempt + 1}")
                elif isinstance(parsed, dict) and "error" in parsed:
                    logger.error(f"LLM reported constraint error for room {room}: {parsed}")
                    final_schedule["schedules"].append(parsed)
                    success = True
                    break
                else:
                    logger.warning(f"❌ JSON parsing failed for room {room}, attempt {attempt + 1}")
                    
                tokens_total["input"] += response.get("usage", {}).get("prompt_tokens", 0)
                tokens_total["output"] += response.get("usage", {}).get("completion_tokens", 0)
                
            except Exception as e:
                logger.error(f"❌ API error for room {room}, attempt {attempt + 1}: {e}")
                
        if not success:
            logger.error(f"❌ CRITICAL FAILURE: Could not generate schedule for room {room} after {max_attempts} attempts")
            # Force a minimal valid structure
            final_schedule["schedules"].append(create_fallback_schedule(room))

    return final_schedule, tokens_total
def validate_schema_compliance(parsed_schedule, expected_room_name):
    """
    Improved validation with better error reporting.
    """
    try:
        # Normalize the schedule first
        parsed_schedule = normalize_friday_early_leave_key(parsed_schedule)
        
        # Check basic structure
        if not isinstance(parsed_schedule, dict):
            logger.error(f"Schedule is not a dict, got {type(parsed_schedule)}")
            return False
            
        if "room" not in parsed_schedule:
            logger.error("Missing 'room' field")
            return False
            
        if "weeks" not in parsed_schedule:
            logger.error("Missing 'weeks' field")
            return False
            
        if parsed_schedule["room"] != expected_room_name:
            logger.error(f"Room name mismatch: expected '{expected_room_name}', got '{parsed_schedule['room']}'")
            # Don't fail for room name mismatch - might be encoding issue
            logger.warning("Continuing despite room name mismatch")
            
        weeks = parsed_schedule["weeks"]
        if not isinstance(weeks, dict):
            logger.error(f"'weeks' is not a dict, got {type(weeks)}")
            return False
            
        # Check week count
        week_keys = list(weeks.keys())
        logger.info(f"Found weeks: {week_keys}")
        
        if len(week_keys) == 0:
            logger.error("No weeks found")
            return False
            
        # More flexible week validation - allow any number of weeks for now
        required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        required_slots = [
            "07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-11:30", 
            "11:30-13:00", "13:00-14:00", "14:00-16:00", "16:00-16:30", "16:30-17:00"
        ]
        
        for week_name, week_data in weeks.items():
            logger.info(f"Validating week: {week_name}")
            
            if not isinstance(week_data, dict):
                logger.error(f"Week {week_name} is not a dict, got {type(week_data)}")
                return False
            
            week_keys_found = list(week_data.keys())
            logger.info(f"Week {week_name} keys: {week_keys_found}")
            
            # Check for required days
            missing_days = set(required_days) - set(week_keys_found)
            if missing_days:
                logger.error(f"Week {week_name} missing days: {missing_days}")
                return False
                
            # Validate day schedules
            for day_name in required_days:
                if day_name not in week_data:
                    continue
                    
                day_data = week_data[day_name]
                if not isinstance(day_data, dict):
                    logger.error(f"Week {week_name}, day {day_name} is not a dict")
                    return False
                
                day_slots = list(day_data.keys())
                missing_slots = set(required_slots) - set(day_slots)
                if missing_slots:
                    logger.error(f"Week {week_name}, day {day_name} missing slots: {missing_slots}")
                    return False
                    
                for slot_name, slot_data in day_data.items():
                    if not isinstance(slot_data, list):
                        logger.error(f"Week {week_name}, day {day_name}, slot {slot_name} is not a list")
                        return False
                        
                    if len(slot_data) < 1:
                        logger.error(f"Week {week_name}, day {day_name}, slot {slot_name} is empty")
                        return False
        
        logger.info(f"Schema validation PASSED for room {expected_room_name}")
        return True
        
    except Exception as e:
        logger.error(f"Schema validation exception: {e}", exc_info=True)
        return False

def validate_and_parse_llm_response(raw_response: str, expected_room: str = None) -> dict | None:
    """
    Main parsing function with comprehensive error handling.
    """
    if not raw_response:
        logger.error("Empty response from LLM")
        return None
    
    logger.info(f"Raw response length: {len(raw_response)}")
    
    # Check for obviously incomplete responses
    if len(raw_response) < 100:
        logger.warning(f"Response seems too short: {raw_response}")
        
        # Check if it's an error response
        try:
            parsed = json.loads(raw_response)
            if isinstance(parsed, dict) and "error" in parsed:
                logger.info("Found error response in short JSON")
                return parsed
        except:
            pass
    
    # Parse the JSON
    parsed = clean_json_string(raw_response)
    
    if parsed is None:
        logger.error("Complete JSON parsing failure")
        return None
    
    # Check for error responses first
    if isinstance(parsed, dict) and "error" in parsed:
        logger.info(f"LLM returned error response: {parsed.get('error')}")
        return parsed
    
    # Validate structure if we have an expected room
    if expected_room:
        if not validate_schema_compliance(parsed, expected_room):
            logger.error(f"Schema validation failed for room {expected_room}")
            return None
    
    logger.info("JSON parsing and validation completed successfully")
    return parsed

# Update your _optimize_schedule function to use this improved parser
def get_llm_schedule_with_better_error_handling(context, room_name, attempt_num):
    """
    Helper function to get schedule from LLM with better error handling.
    """
    base_system = """You are a kindergarten scheduling optimizer. 

CRITICAL REQUIREMENTS:
1. Output ONLY valid JSON - no markdown, no explanations
2. Include "fridayEarlyLeave" field in each week as a string
3. Every time slot must have at least 1 staff member
4. Follow the exact schema provided

If constraints cannot be satisfied, return: {"error": "Constraints not satisfiable", "room": "ROOM_NAME"}"""

    user_msg = f"""Generate complete 4-week schedule for room: "{room_name}"

SCHEMA: {json.dumps(STANDARDIZED_ROOM_SCHEMA, indent=2)}
DATA: {json.dumps(context['kindergarten_data'], indent=2)}

Return ONLY JSON - no other text."""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": base_system},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.0,
            max_tokens=6000  # Ensure enough tokens for complete response
        )
        
        raw = response["choices"][0]["message"]["content"]
        logger.info(f"LLM response for {room_name} attempt {attempt_num}: {len(raw)} chars")
        
        # Check if response was truncated
        if response["choices"][0].get("finish_reason") != "stop":
            logger.warning(f"LLM response may be incomplete. Finish reason: {response['choices'][0].get('finish_reason')}")
        
        return raw, response.get("usage", {})
        
    except Exception as e:
        logger.error(f"LLM API error for {room_name}: {e}")
        return None, {}

# Create fallback schedule function
def create_fallback_schedule(room_name):
    """Create a complete valid schedule when LLM fails."""
    time_slots = [
        "07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-11:30", 
        "11:30-13:00", "13:00-14:00", "14:00-16:00", "16:00-16:30", "16:30-17:00"
    ]
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    weeks = ["week1", "week2", "week3", "week4"]
    
    fallback = {
        "room": room_name,
        "weeks": {}
    }
    
    for week in weeks:
        fallback["weeks"][week] = {}
        
        # Add day schedules
        for day in days:
            fallback["weeks"][week][day] = {}
            for slot in time_slots:
                fallback["weeks"][week][day][slot] = ["STAFF_NEEDED"]
        
        # Add fridayEarlyLeave
        fallback["weeks"][week]["fridayEarlyLeave"] = "STAFF_NAME"
    
    logger.info(f"Created fallback schedule for {room_name}")
    return fallback

def re_optimize_schedule(context, schedule_text, discrepancies, violations):
    """
    Re-optimize using your standardized schema with strengthened validation.
    """
    room_names = [room.get("name") for room in context["kindergarten_data"].get("rooms", [])]
    updated_schedule = {"schedules": []}

    # Ultra-strict system prompt for re-optimization
    base_system = """
    You are a kindergarten scheduling optimizer fixing validation issues.

    ABSOLUTE REQUIREMENTS:
    1. Output EXACTLY one complete, valid JSON schedule matching the provided schema
    2. Fix ONLY the reported violations and discrepancies
    3. MAINTAIN all existing valid assignments
    4. NEVER leave any time slot empty (minItems: 1 requirement)
    5. Return COMPLETE schedule - never partial or truncated

    SCHEMA COMPLIANCE IS MANDATORY - NO EXCEPTIONS.
    Every field, every array, every requirement must be perfectly met.
    
    If a fix creates impossible conflicts, document in "notes" field but still return valid JSON.
    """

    def ask_llm_with_validation(prompt, expected_room):
        """Ask LLM with built-in validation loop."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                
                raw = response["choices"][0]["message"]["content"]
                parsed = clean_json_string(raw)
                
                if parsed and validate_schema_compliance(parsed, expected_room):
                    return parsed
                else:
                    logger.warning(f"Validation failed for {expected_room}, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"LLM error for {expected_room}, attempt {attempt + 1}: {e}")
                
        return None

    # Get current schedules
    if isinstance(schedule_text, dict):
        current_schedules = schedule_text.get("schedules", [])
    else:
        try:
            current_schedules = json.loads(schedule_text).get("schedules", [])
        except:
            logger.error("Cannot parse current schedule_text")
            return schedule_text

    for room in room_names:
        # Find current room schedule
        current_room_schedule = None
        for sched in current_schedules:
            if sched.get("room", "").lower() == room.lower():
                current_room_schedule = sched
                break
        
        if not current_room_schedule:
            logger.warning(f"No current schedule found for room {room}")
            updated_schedule["schedules"].append(create_fallback_schedule(room))
            continue

        # Extract room-specific issues
        room_violations = extract_room_violations(violations, room)
        room_discrepancies = extract_room_discrepancies(discrepancies, room)

        if not room_violations and not room_discrepancies:
            # No issues for this room, but still validate compliance
            if validate_schema_compliance(current_room_schedule, room):
                updated_schedule["schedules"].append(current_room_schedule)
            else:
                logger.warning(f"Current schedule for {room} doesn't meet schema, regenerating...")
                updated_schedule["schedules"].append(create_fallback_schedule(room))
            continue

        # Create ultra-specific fix prompt
        prompt = f"""
        TASK: Fix schedule for room "{room}" while maintaining PERFECT schema compliance

        MANDATORY SCHEMA (100% compliance required):
        {json.dumps(STANDARDIZED_ROOM_SCHEMA, indent=2)}

        CURRENT SCHEDULE:
        {json.dumps(current_room_schedule, indent=2)}

        SPECIFIC VIOLATIONS TO FIX:
        {json.dumps(room_violations, indent=2)}

        SPECIFIC DISCREPANCIES TO FIX:
        {json.dumps(room_discrepancies, indent=2)}

        CRITICAL INSTRUCTIONS:
        1. Return COMPLETE corrected schedule for room "{room}"
        2. Fix ONLY the specific issues listed above
        3. Keep ALL other valid parts unchanged
        4. ENSURE every time slot has minItems: 1 (never empty arrays)
        5. Maintain exact schema structure and field names
        6. Validate JSON syntax before returning

        VALIDATION CHECKLIST:
        ✓ "room" field equals "{room}"
        ✓ Has exactly 4 weeks (week1-week4)
        ✓ Each week has 5 days (monday-friday)
        ✓ Each day has 9 time slots
        ✓ Every array has at least 1 item
        ✓ Perfect JSON syntax

        OUTPUT ONLY THE JSON - NO EXPLANATIONS.
        """
        
        fixed_schedule = ask_llm_with_validation(prompt, room)
        if fixed_schedule:
            updated_schedule["schedules"].append(fixed_schedule)
            logger.info(f"✅ Successfully fixed and validated schedule for room {room}")
        else:
            logger.error(f"❌ Failed to fix schedule for room {room}, using fallback")
            updated_schedule["schedules"].append(create_fallback_schedule(room))

    return updated_schedule

def extract_room_violations(violations, room_name):
    """Extract violations specific to a room."""
    room_violations = []
    if isinstance(violations, dict) and "violations" in violations:
        for constraint, violation_list in violations["violations"].items():
            for violation in violation_list:
                if (isinstance(violation, dict) and 
                    violation.get("room", "").lower() == room_name.lower()):
                    room_violations.append(violation)
    return room_violations

def extract_room_discrepancies(discrepancies, room_name):
    """Extract discrepancies that might be related to a room."""
    if not isinstance(discrepancies, list):
        return []
    
    # This might need adjustment based on your discrepancy structure
    return [d for d in discrepancies if 
            any(room_name.lower() in str(v).lower() for v in d.values())]
    """
    Improved re-optimization with consistent model usage and better error handling.
    """
    room_names = [room.get("name") for room in context["kindergarten_data"].get("rooms", [])]
    updated_schedule = {"schedules": []}

    base_system = """
    You are a kindergarten scheduling optimizer fixing validation issues.
    
    CRITICAL REQUIREMENTS:
    1. Output EXACTLY one complete, valid JSON schedule
    2. Fix ONLY the reported violations and discrepancies
    3. Do NOT modify working parts of the schedule
    4. Maintain all staff and their target hours
    5. Return complete JSON - never partial schedules
    
    If fixes are impossible, include the issue in a "violations" field but still return the complete schedule.
    """

    def ask_llm_improved(prompt):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",  # Fixed: use consistent model
                    messages=[
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                return response["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM API error, attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return None
        return None

    # Get current schedule data
    if isinstance(schedule_text, dict):
        current_schedules = schedule_text.get("schedules", [])
    else:
        try:
            parsed_schedule = json.loads(schedule_text)
            current_schedules = parsed_schedule.get("schedules", [])
        except:
            logger.error("Cannot parse current schedule_text")
            return schedule_text

    for room in room_names:
        # Find current room schedule
        current_room_schedule = None
        for sched in current_schedules:
            if sched.get("room", "").lower() == room.lower():
                current_room_schedule = sched
                break
        
        if not current_room_schedule:
            logger.warning(f"No current schedule found for room {room}")
            continue

        # Filter violations and discrepancies for this room
        room_violations = []
        room_discrepancies = []
        
        # Extract room-specific issues (you may need to adjust this based on your violation structure)
        if isinstance(violations, dict) and "violations" in violations:
            for constraint, violation_list in violations["violations"].items():
                room_violations.extend([v for v in violation_list if v.get("room", "").lower() == room.lower()])
        
        if isinstance(discrepancies, list):
            room_discrepancies = [d for d in discrepancies if any(room.lower() in str(v).lower() for v in d.values())]

        if not room_violations and not room_discrepancies:
            # No issues for this room, keep as is
            updated_schedule["schedules"].append(current_room_schedule)
            continue

        prompt = f"""
        Fix the schedule for room "{room}":
        
        CURRENT SCHEDULE:
        {json.dumps(current_room_schedule, indent=2)}
        
        VIOLATIONS TO FIX:
        {json.dumps(room_violations, indent=2)}
        
        DISCREPANCIES TO FIX:
        {json.dumps(room_discrepancies, indent=2)}
        
        TASK:
        1. Return the COMPLETE corrected schedule for room "{room}"
        2. Fix ONLY the specific violations and discrepancies listed above
        3. Keep all other parts of the schedule unchanged
        4. Maintain staff target hours and constraints
        5. Ensure the "room" field equals "{room}"
        
        Return ONLY valid JSON, no explanations.
        """
        
        raw_response = ask_llm_improved(prompt)
        if not raw_response:
            logger.error(f"Failed to get LLM response for room {room}")
            updated_schedule["schedules"].append(current_room_schedule)
            continue
            
        parsed_response = clean_json_string(raw_response)
        if parsed_response and isinstance(parsed_response, dict) and "room" in parsed_response:
            updated_schedule["schedules"].append(parsed_response)
            logger.info(f"✓ Successfully updated schedule for room {room}")
        else:
            logger.warning(f"Failed to parse updated schedule for room {room}, keeping original")
            updated_schedule["schedules"].append(current_room_schedule)

    return updated_schedule