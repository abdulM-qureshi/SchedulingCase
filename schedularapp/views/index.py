from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
import json

# Maximum iterations for refinement
MAX_ITERATIONS = 5
# Define any absolute caps
ABSOLUTE_MAX_HOURS_PER_WEEK = 35

@csrf_exempt
def index(request):
    if request.method != 'POST':
        status = 405
        msg = 'Only POST method is allowed.' if request.method != 'GET' else 'GET method is not allowed. Please use POST.'
        return JsonResponse({'message': msg}, status=status)

    # Parse incoming values for validation
    try:
        payload = json.loads(request.body.decode('utf-8'))
        raw_employees = payload.get('employees', [])
    except json.JSONDecodeError:
        raw_employees = []

    if not raw_employees:
        raw_employees = []
        # ---- How many Employees does the user want to Add 
        for i in range(1, 4):
            # Validate max_hours_per_week per employee
            max_hours = request.POST.get(f'emp{i}_max_hours_per_week')
            try:
                max_hours = int(max_hours)
            except (TypeError, ValueError):
                return JsonResponse({'error': f'Invalid max_hours_per_week for emp{i}.'}, status=400)
            if max_hours > ABSOLUTE_MAX_HOURS_PER_WEEK:
                return JsonResponse({
                    'error': f'Max hours per week for emp{i} cannot exceed {ABSOLUTE_MAX_HOURS_PER_WEEK}.'
                }, status=400)

            raw_employees.append({
                'id': request.POST.get(f'emp{i}_id'),
                'availability': request.POST.get(f'emp{i}_availability'),
                'preferred_shifts': request.POST.get(f'emp{i}_preferred_shifts'),
                'max_hours_per_week': max_hours,
                'max_consecutive_shifts': int(request.POST.get(f'emp{i}_max_consecutive_shifts') or 0),
                'max_shifts_per_day': int(request.POST.get(f'emp{i}_max_shifts_per_day') or 0),
            })

    # Collect soft constraints
    soft_constraints = {
        'preferred_shifts_respected': request.POST.get('preferred_shifts_respected') == 'on',
        'shift_preferences_respected': request.POST.get('shift_preferences_respected') == 'on',
        
    }
    rotation_policy = request.POST.get('rotation_policy')
    days = {day: request.POST.get(f'day_{day.lower()}') == 'on' for day in ['Monday','Tuesday','Wednesday','Thursday','Friday']}
    operating_hours = {f'{day.lower()}_shift_time': request.POST.get(f'{day.lower()}_shift_time') for day in days}

    context = {
        'employees': raw_employees,
        'soft_constraints': soft_constraints,
        'rotation_policy': rotation_policy,
        'days': days,
        'operating_hours': operating_hours,
    }

    best_schedule, best_score, iterations = _optimize_schedule(context)
    return JsonResponse({
        'schedule': best_schedule,
        'score': best_score,
        'iterations': iterations
    })

def _optimize_schedule(context):
    base_system = "You are a scheduling optimization assistant."
    prompt_history = []
    best_schedule = None
    best_score = -1

    for iteration in range(1, MAX_ITERATIONS + 1):
        user_msg = _build_user_message(context, best_schedule, iteration)
        prompt_history.append({'role': 'user', 'content': user_msg})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{'role': 'system', 'content': base_system}] + prompt_history
        )
        schedule_text = response.choices[0].message['content']

        # Skip any schedule violating hard constraints
        if _violates_hard_constraints(schedule_text, context):
            continue

        score = _evaluate_schedule(schedule_text, context)
        if score > best_score:
            best_score = score
            best_schedule = schedule_text
            context['last_schedule'] = best_schedule
            context['last_score'] = best_score
        else:
            break

    return best_schedule, best_score, iteration


def _build_user_message(context, last_schedule, iteration):
    # Only include soft constraints and essential context
    filtered = {
        'employees': context['employees'],
        'soft_constraints': context['soft_constraints'],
        'rotation_policy': context['rotation_policy'],
        'days': context['days'],
        'operating_hours': context['operating_hours'],
    }
    if iteration == 1:
        return json.dumps(filtered, indent=2)
    return (
        f"Revised context: {json.dumps(filtered, indent=2)}\n"
        f"Last Schedule: {last_schedule}\n"
        f"Current Score: {context['last_score']}\n"
        "Please produce an improved schedule."
    )


def _violates_hard_constraints(schedule_text, context):
    """
    Parse the schedule_text for violations of:
      - employee hours > max_hours_per_week
      - shifts outside availability
      - consecutive shifts > max_consecutive_shifts
      - shifts per day > max_shifts_per_day
    Return True if any violation is found.
    """
    # TODO: Implement parsing logic to extract assignments and compare against context
    return False  # stub until real logic is added


def _evaluate_schedule(schedule_text, context):
    # TODO: implement real parsing & scoring for soft constraints
    import random
    return random.uniform(0, 1)


# ----------------------------------

# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from dotenv import load_dotenv
# from datetime import datetime
# import logging
# import openai
# import json
# import time
# import os
# import re
# load_dotenv()  # load variables from .env

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# openai.api_key = os.getenv('OPENAI_API_KEY') # API is in file .env

# @csrf_exempt
# def brikilund(request):
#     try:
#         start_time = datetime.now()  # start timer here

#         # Build context
#         context , pedagogues, assistants, helpers, constraints  = _collect_context_from_request(request)

#         end_time = datetime.now()  # end timer here
#         decimal_time = (end_time - start_time).total_seconds()
#         process_time = f"{decimal_time} sec"
        
#         schedule_text, tokens_details = _optimize_schedule(context)
        
#         report_  = _constraints_check(schedule_text, constraints)
        
#         cost1 = tokens_details['cost'] if isinstance(tokens_details, dict) else tokens_details
#         cost2 = report_['cost'] if isinstance(report_, dict) else report_
        
#         try:
#             cost1 = float(cost1) if cost1 is not None else 0.0
#         except (ValueError, TypeError):
#             cost1 = 0.0
            
#         try:
#             cost2 = float(cost2) if cost2 is not None else 0.0
#         except (ValueError, TypeError):
#             cost2 = 0.0
                
#         cost_ = cost1 + cost2

#         # Existing violations
#         violations = _check_violations(pedagogues, assistants, helpers)

#         # NEW: Output completeness
#         # completeness_result = _check_output_completeness(schedule_text, context)

#         # NEW: Fairness
#         fairness_result = _calculate_fairness_score(schedule_text, context)

#         # NEW: Coverage
#         # coverage_result = _calculate_coverage_score(schedule_text, context)
        
#         return JsonResponse({
#             'Gpt_provided_schedule': schedule_text,
#             "model report":report_,
#             'Fairness Score': fairness_result,
#             'tokens_details': tokens_details,
#             'Hard Rule Violation Count': violations if violations else "- No rule has been violated so far.",
#             'Correction Time': process_time,
#             "Total cost": cost_,
#             "model":'o3'
#             # 'Coverage Score': coverage_result,
#             # 'Output Completeness': completeness_result,
#         })

#     except Exception as e:
#         return JsonResponse({
#             "error": str(e),
#             "message": "Something went wrong while processing the schedule input."
#         }, status=400)

# def _collect_context_from_request(request):
#     "Extracts the full scheduling input as a dict."
#     if request.method == 'POST':
#         try:
#             body = json.loads(request.body)
#         except Exception as e:
#             raise ValueError("Invalid JSON data") from e
        
#     week_date_time = {
#     'starting_date':body.get('starting_date'),
#     'ending_date':body.get('ending_date')
#     }     
        
#     # STAFF
#     staff_counts = {
#         "total_staff": int(body.get("total_staff", 13)),
#         "no_of_pedagogues": int(body.get("no_of_pedagogues", 6)),
#         "no_of_assistants": int(body.get("no_of_assistants", 5)),
#         "no_of_helpers": int(body.get("no_of_helpers", 2)),
#     }
#     # Pedagogues
#     pedagogues = []
#     for i in range(1, staff_counts["no_of_pedagogues"] + 1):
#         pedagogues.append({
#             "name": body.get(f"pedagogue_name_{i}", f"Pedagogue {i}"),
#             "age": body.get(f"pedagogue_age_{i}", "N/A"),
#             "shift_time": body.get(f"pedagogue_shift_time_{i}", "N/A"),
#         })
#     # Assistants
#     assistants = []
#     for i in range(1 , staff_counts["no_of_assistants"] + 1):
#         assistants.append({
#             "name": body.get(f"assistant_name_{i}", f"Assistant {i}"),
#             "age": body.get(f"assistant_age_{i}", "N/A"),
#             "shift_time": body.get(f"assistant_shift_time_{i}", "N/A"),
#         })
#     # Helpers
#     helpers = []
#     for i in range(1, staff_counts["no_of_helpers"] + 1 ):
#         helpers.append({
#             "name": body.get(f"helper_name_{i}", f"Helper {i}"),
#             "age": body.get(f"helper_age_{i}", "N/A"),
#             "shift_time": body.get(f"helper_shift_time_{i}", "N/A"),
#         })
#     # CONSTRAINTS/HARD RULES
#     constraints = {
#         # HARD CONSTRAINTS
#         'hard_constraints' : body.get("hard_constraints"),
#         # SOFT CONSTRAINTS
#         'soft_constraints' : body.get("soft_constraints")
#         }
    
#     # CONTEXT
#     context = {
#         'week_time':week_date_time,
#         "staff_counts": staff_counts,
#         "pedagogues": pedagogues,
#         "assistants": assistants,
#         "helpers": helpers,
#         'constraints':f" Make sure that any hard constraint dont be violated. Here they are: {constraints}",
        
#         # ROOMS
#         "rooms": {
#             "total_rooms": int(body.get("rooms", 4)),
#             "V1_V2": "Infant rooms (10–30 months)",
#             "B1_B2": "Preschool rooms (2 years 10 months – 5 years)",
#             "required_ratio": {
#                 "infants": "1 adult per 3 children",
#                 "preschoolers": "1 adult per 6 children"
#             },
#             # MAKING THE pADAGOGUES REQUIRED
#             "pedagogue_required": True
#         },
#         "schedule_blocks": [
#             {"time": "07:00–08:00", "activity": "Opening (rooms merged)", "notes": "3 adults total (≥2 Pedagogues)"},
#             {"time": "08:00–09:00", "activity": "Free play, breakfast", "notes": "Rooms split; floaters help"},
#             {"time": "09:00–11:00", "activity": "Planned activities", "notes": "Core staffing; outings possible"},
#             {"time": "11:00–13:00", "activity": "Lunch + naps", "notes": "Breaks begin; floaters cover"},
#             {"time": "13:00–15:30", "activity": "Outdoor play / excursions", "notes": "Assistants may swap"},
#             {"time": "15:30–Close", "activity": "Pick-up + merge", "notes": "Reduced staffing allowed"},
#             {"time": "Friday 16:15–16:30", "activity": "Clean-up", "notes": "Rotated among staff"}
#         ],
#         # Mentioning the time schedule in which the shifts are assigned. - Standered time schedule
#         "schedule_time": [
#             {"time": "07:00–08:00"},
#             {"time": "08:00–09:00"},
#             {"time": "09:00–11:00"},
#             {"time": "11:00–13:00"},
#             {"time": "13:00–15:30"},
#             {"time": "15:30–Close"},
#             {"time": "16:15–16:30"}
#         ],
#         # STAFF AVAILABILITY
#             "individual_availability": [
#                 {"staff": "P1", "note": "Cannot open on Mondays"},
#                 {"staff": "P4", "note": "Not available on Fridays"},
#                 {"staff": "P6", "note": "Only works Mon–Wed, 07:00–13:00"},
#                 {"staff": "A1", "note": "School on Wednesdays, 07:00–10:00"},
#                 {"staff": "H2", "note": "Only works 09:00–13:00"},
#             ],
#         # SUCCESS_CRITERIA
#         "success_criteria": {
#             "legal_compliance": "No live-ratio breaches",
#             "shift_quality": "≥85% of shifts pass on first run",
#             "manager_effort": "Schedule editable/finalized in under 10 minutes",
#             "fairness": "Even distribution of late shifts (max 1 difference over 4 weeks)"
#         },
#         # INSTRUCTIONS TO LLM - o3
#         "llm_instruction": (
#             "Using the staff details, room setup, constraints, and availability, generate a weekly schedule "
#             "that assigns each staff member to appropriate shifts. Ensure legal ratios are met, breaks are handled, "
#             "and special constraints are respected. Schedule must be complete by Thursday noon with minimal edits needed."
#             "Please return hour by hour schedule in the format:\n"
#             "please keep it in your response and return it as a break : 08:00–09:00"
#             "please write the response in a proper, clean way so I can understand it better and easily convert it into a table for the frontend"
#         ),
#     }
    
#     return context, pedagogues, assistants, helpers , constraints

# def _check_violations(pedagogues, assistants, helpers):
#     violations = []

#     # Example check 1: Ensure at least one pedagogue exists
#     if len(pedagogues) == 0:
#         violations.append("At least one pedagogue must be scheduled.")

#     # Example check 2: Assistants cannot be alone
#     if len(assistants) == 0:
#         violations.append("Assistants cannot be scheduled alone.")

#     # Example check 3: Helpers cannot work alone (adjust as per your logic)
#     if len(helpers) == 0:
#         violations.append("Helpers cannot work alone.")
    
#     return violations
        
# def _optimize_schedule(context):
#     "Sends the scheduling context to GPT and returns optimized schedule."
#     base_system = (
#         "You are a scheduling optimization assistant. "
#         "Based on the provided kindergarten staff, rooms, and constraints, generate a legal and fair weekly schedule."
#     )

#     user_msg = f"Here is the schedule input data for optimization:\n{json.dumps(context, indent=2)}"
#     logger.info(f"Input Prompt: {user_msg}")

#     response = openai.ChatCompletion.create(
#         model="o3",
#         messages=[
#             {"role": "system", "content": base_system},
#             {"role": "user", "content": user_msg}
#         ]
#     )
    
#     # Log the response to check its structure
#     logger.info(f"OpenAI API Response: {response}")

#     # Extract the schedule text
#     schedule_text = response['choices'][0]['message']['content']

#     # Log the type of schedule_text
#     logger.info(f"Type of schedule_text: {type(schedule_text)}")
    
#     # Log output summary
#     logger.info(f"Output Summary: {schedule_text[:100]}...")  # Log first 100 characters as a summary

#     # Log tokens used and cost if available
#     tokens_used = response['usage']['total_tokens'] if 'usage' in response else 'N/A'
#     # Log input tokens used 
#     input_tokens = response['usage']['prompt_tokens'] if 'usage' in response else 'N/A'
#     # Log output tokens used
#     output_tokens = response['usage']['completion_tokens'] if 'usage' in response else 'N/A'
    
#     cost_ = calculate_cost(input_tokens,output_tokens)
    
#     # cost_ = f"${cost_}"
    
#     logger.info(f"Tokens Used: {tokens_used}, Cost: {cost_}")
        
#     tokens_details = {
#         "input_token":input_tokens, 
#         "output_token":output_tokens,
#         "cost":cost_, 
#     }

#     return schedule_text, tokens_details


# def calculate_cost(input_tokens, output_tokens):
#     try:
#         input_number_ = 0.0005  # Correct input cost per 1k tokens
#         output_number_ = 0.0015  # Correct output cost per 1k tokens
#         input_cost = (input_tokens / 1000) * input_number_
#         output_cost = (output_tokens / 1000) * output_number_
#         cost_ = input_cost + output_cost
#         logger.info(f"Input Cost: {input_cost}, Output Cost: {output_cost}, Total Cost: {cost_}")
#         return cost_
#     except Exception as e:
#         logger.error(f"Error calculating cost: {str(e)}")
#         return None

# # --> This function checks the schedule text against the hard constraints provided in the context.
# def _constraints_check(schedule_text, constraints):
#     try:
#         base_system = (
#             "You are a scheduled text testing agent. "
#             f"Based on the provided schedule_text, you need to check if it follows the rules in {constraints}, "
#             "more specifically, the hard constraints. Generate a report about the satisfaction and return it."
#         )

#         user_msg = f"Here is the optimized schedule text:\n{json.dumps(schedule_text, indent=2)}"
#         logger.info(f"Input Prompt: {user_msg}")

#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": base_system},
#                 {"role": "user", "content": user_msg}
#             ]
#         )
        
#         # Log tokens used and cost if available
#         tokens_used = response['usage']['total_tokens'] if 'usage' in response else 'N/A'
#         # Log input tokens used 
#         input_tokens = response['usage']['prompt_tokens'] if 'usage' in response else 'N/A'
#         # Log output tokens used
#         output_tokens = response['usage']['completion_tokens'] if 'usage' in response else 'N/A'
        
#         cost_ = calculate_cost(input_tokens, output_tokens)
        
#         # cost_ = f"${cost_}"
#         # cost_
        
#         logger.info(f"Tokens Used: {tokens_used}, Cost: {cost_}")
            

#         if 'choices' in response and response['choices']:
#             _report = response['choices'][0]['message']['content']
            
#             report_ = {
#                 "tokens_used": _report,
#                 "input_token":input_tokens, 
#                 "output_token":output_tokens,
#                 "cost": cost_,
                
#             }

#             return report_ 
#         else:
#             logger.error("Unexpected API response structure")
#             return "Error in constraints check, unexpected API response structure."

#     except openai.error.OpenAIError as e:
#         logger.error(f"OpenAI API error: {str(e)}")
#         return "Error in constraints check, please try again later."
#     except Exception as e:
#         logger.error(f"Error in constraints check: {str(e)}")
#         return "Error in constraints check, please try again later."
    
# def time_to_minutes(t):
#     # Convert 'HH:MM' or 'HH:MM–HH:MM' string parts to minutes since midnight
#     h, m = map(int, t.split(':'))
#     return h * 60 + m

# def parse_time_block(block_str):
#     # Parse time range like '07:00–08:00' or '15:30–Close' (handle Close as 24:00)
#     start_str, end_str = block_str.split('–')
#     start = time_to_minutes(start_str)
#     if end_str.lower() == 'close':
#         end = 24 * 60
#     else:
#         end = time_to_minutes(end_str)
#     return (start, end)

# # def _check_output_completeness(schedule_text, context):
# #     try:
# #         schedule_lower = schedule_text.lower()

# #         # Check for missing staff names (keep your existing logic)
# #         staff_names = [p["name"] for p in context["pedagogues"]] + \
# #                     [a["name"] for a in context["assistants"]] + \
# #                     [h["name"] for h in context["helpers"]]
# #         missing_staff = [name for name in staff_names if name.lower() not in schedule_lower]

# #         # Extract all time ranges from schedule_text (output)
# #         # Matches times like '07:00-08:00', '07:00–08:00' (dash or en dash)
# #         time_blocks_in_output = re.findall(r'(\d{2}:\d{2})\s*[–-]\s*(\d{2}:\d{2}|close)', schedule_lower)

# #         output_intervals = []
# #         for start_str, end_str in time_blocks_in_output:
# #             start = time_to_minutes(start_str)
# #             end = 24 * 60 if end_str == 'close' else time_to_minutes(end_str)
# #             output_intervals.append((start, end))

# #         def is_block_covered(block_start, block_end, intervals):
# #             # Check if this block is fully inside any output interval
# #             for (start, end) in intervals:
# #                 if block_start >= start and block_end <= end:
# #                     return True
# #             return False

# #         # Check each defined schedule block if it is covered
# #         missing_blocks = []
# #         for block in context["schedule_time"]:
# #             block_start, block_end = parse_time_block(block["time"].lower())
# #             if not is_block_covered(block_start, block_end, output_intervals):
# #                 missing_blocks.append(block["time"])

# #         return {
# #             "status": "Complete" if not missing_staff and not missing_blocks else "Incomplete",
# #             "missing_staff": missing_staff,
# #             "missing_blocks": missing_blocks
# #         }

# #     except Exception as e:
# #         return {
# #             "status": "Error",
# #             "error": str(e)
# #         }

# def _calculate_fairness_score(schedule_text, context):
#     schedule_lower = schedule_text.lower()
#     staff_names = [p["name"] for p in context["pedagogues"]] + \
#                 [a["name"] for a in context["assistants"]] + \
#                 [h["name"] for h in context["helpers"]]
    
#     shift_counts = {name: schedule_lower.count(name.lower()) for name in staff_names}
#     shifts = list(shift_counts.values())
    
#     if not shifts:
#         return {"score": 0, "message": "No staff found in schedule"}

#     fairness_score = 1 - (max(shifts) - min(shifts)) / max(1, sum(shifts))
#     return {"score": round(fairness_score * 100, 2)}


# # def _calculate_coverage_score(schedule_text, context):
# #     schedule_lower = schedule_text.lower()
# #     blocks = [block["time"] for block in context["schedule_blocks"]]
    
# #     covered_blocks = [b for b in blocks if b.lower() in schedule_lower]
# #     score = len(covered_blocks) / len(blocks) * 100

# #     return {
# #         "score": round(score, 2),
# #         "covered_blocks": covered_blocks,
# #         "total_blocks": len(blocks)
# #     }
    
# # What is the details object?
# # The "details" object shows:
# # How many times each staff member is scheduled throughout the week. Think of it like a workload count or number of assignments per person.
