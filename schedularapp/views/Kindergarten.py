from sched import scheduler
from django.views.decorators.csrf import csrf_exempt
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

openai.api_key = os.getenv('OPENAI_API_KEY') # API is in file .env

@csrf_exempt
def Kindergarten(request):
    if request.method == 'POST':
        try:
            start_time = datetime.now()  # start timer her

            # Build context
            context, constraints = _collect_context_from_request(request)

            end_time = datetime.now()  # end timer here
            decimal_time = (end_time - start_time).total_seconds()
            process_time = f"{decimal_time} sec"
            
            schedule_text, tokens_details = _optimize_schedule(context, constraints)
            
            _report, report_ = _constraints_check(schedule_text, constraints)
            
            cost1 = tokens_details['cost'] if isinstance(tokens_details, dict) else tokens_details
            cost2 = report_['cost'] if isinstance(report_, dict) else report_
            
            try:
                cost1 = float(cost1) if cost1 is not None else 0.0
            except (ValueError, TypeError):
                cost1 = 0.0
                
            try:
                cost2 = float(cost2) if cost2 is not None else 0.0
            except (ValueError, TypeError):
                cost2 = 0.0

            #  - Total_cost      
            cost_ = cost1 + cost2
            
            return JsonResponse({
                'Gpt_provided_schedule': schedule_text,
                "cleaned_report_json":_report,
                'tokens_details': tokens_details,
                'Correction Time': process_time,
                "Total cost": cost_,
                "model":'o3'
            })

        except Exception as e:
            logger.error(f"Error in Kindergarten view: {e}", exc_info=True) # Log full traceback
            return JsonResponse({
                "error": str(e),
                "message": "Something went wrong while processing the schedule input."
            }, status=400)
    elif request.method == 'GET':
        return render(request, 'index.html')

def _collect_context_from_request(request):
    "Extracts the full scheduling input as a dict, now handling nested JSON."
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data in request body: {e}")
        
    # Assuming 'body' already contains the parsed JSON from the user's request
    # Example: body = request.json()
    # CONSTRAINTS/HARD RULES - UPDATED TO INCLUDE BREAK WINDOW
    constraints = {
        'hard_constraints': 
        """Hard Constraints (Rules that CANNOT be broken)
        1. Operating Hours: Monday-Friday, 07:30 to 17:00.
        2. scheduler Cycle: The schedule must cover a 4-week rotating period.
        3. Weekly Hours: Each staff member must be scheduled for their precise Target Weekly Hours.
        4. This is important But - You are missing this which you should not miss !!! - Friday Early Leave: Over the 4-week cycle, every staff member must have exactly one Friday where they leave at 12:00.
        5. Fixed Staff Schedules:
            ○ Mýran, Staff 'J': Must be scheduled 09:00-15:00, Monday-Friday.
            ○ Løkurin, Staff 'N': Must be scheduled 08:00-16:00, Monday-Thursday. He has Off day on Friday.
        6. Staffing Levels & Room Combining:
            ○ Morning (07:30 - 08:00): Exactly 3 kindergarten staff members are on duty in a shared common area.
            ○ Room Opening (08:00 - 08:30): At least 1 staff member must be present in each of the 5 rooms.
            ○ Main Day (08:30 onwards): At least 2 staff members must be present in Tjørnin, Mýran, Túgvan, and Spírar. Løkurin must have its second staff member by 09:00 or 09:30.
            ○ Afternoon Consolidation (16:00 - 16:30): There is exactly 1 staff member remaining in each of the 5 rooms.
            ○ Final Closing (16:30 - 17:00): All remaining children and staff are combined into a single designated closing room. There is exactly 1 staff member on duty for this period. The schedule must assign which room this is each day whith: **-**.""",
        
        'Soft Constraints': 
        """ Soft Constraints (Goals for a "Good" Schedule)
            These rules guide the AI to create a fair and practical schedule.
            1. Shift Rotation: Opening, middle, and closing shifts should rotate fairly among staff
            week-to-week.
            2. Possible Start Times: 07:30, 08:00, 08:30, 09:00, or 09:30.
            3. Possible End Times: 12:00-13:30 (for half-days), or 15:00, 16:00, 16:30, 17:00.
            4. No "Wasted Time": Avoid scheduling staff to leave between 13:30 and 15:00."""
    }

    kindergarten_data = {
        "rooms": body.get("rooms", []), # Expects a list of room dictionaries
        "constraints": constraints, # Expects a list of strings
    }

    # Now you can iterate through the received data
    for room in kindergarten_data["rooms"]:
        room_name = room.get("name")
        staff_members = room.get("staff", [])

        print(f"Processing Room: {room_name}")
        for staff in staff_members:
            staff_initial = staff.get("initial")
            contracted_hours = staff.get("contracted_hours_week")
            target_weekly_hours = staff.get("target_weekly_hours")
            specific_constraints = staff.get("constraints")
            open_room = bool(staff.get("open_room", False))
            closer = bool(staff.get("closer", False))
            # consolidates_room = bool(staff.get("consolidates_room", False))

            print(f"  Staff: {staff_initial}, Contracted: {contracted_hours}, Target: {target_weekly_hours}, Constraints: {specific_constraints}")

    # Example of accessing a specific fixed constraint from the document (not user input)
    # Note: These are constants in the problem description, not typically passed via 'body'
    operating_hours = "Monday-Friday, 07:30 to 17:00."
    schedule_cycle = "4-week rotating period."

    # You should validate if the received data from the form aligns with the rules in the document.
    # For instance, check if the "Target Weekly Hours" provided by the user is indeed
    # 30 minutes less than "Contracted Hours" for each staff member, as stated in the rule[cite: 8].
    # If not, you might correct it or return an error.

    for room in kindergarten_data["rooms"]:
        for staff in room.get("staff", []):
            contracted = staff.get("contracted_hours_week")
            target = staff.get("target_weekly_hours")
            open_room = bool(staff.get("open_room", False))
            closer = bool(staff.get("closer", False))
            # consolidates_room = bool(staff.get("consolidates_room", False))
            if contracted is not None and target is not None:
                expected_target = contracted - 0.5
                if target != expected_target:
                    print(f"Warning: Staff {staff.get('initial')} in {room.get('name')} has inconsistent Target Weekly Hours. Expected {expected_target}, got {target}. Adjusting.")
                    staff["target_weekly_hours"] = expected_target # Or raise an error
    
    # IMPORTANT: THIS IS THE NEW PROMPT TO ENSURE CONSISTENT JSON OUTPUT
    llm_instruction_prompt = (
        "This is strictly important - Generate the schedule for 4 weeks, with each week containing 5 days (Monday to Friday). "
        "The output MUST be a pure JSON object in the following structure. No other words, text, or markdown outside this JSON.\n\n"

        "This json will continue till the nth number of room and nth number of staff, so feel free to cover each room and each staff"
        """{
    "room_1": {
        "room_name": "room_1",
        "week_1": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_2": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_3": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_4": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        }
    },
    "room_2": {
        "room_name": "room_2",
        "week_1": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_2": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_3": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_4": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        }
    },
    "room_3": {
        "room_name": "room_3",
        "week_1": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_2": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_3": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_4": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        }
    },
    "room_4": {
        "room_name": "room_4",
        "week_1": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_2": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_3": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_4": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        }
    },
    "room_5": {
        "room_name": "room_5",
        "week_1": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_2": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_3": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        },
        "week_4": {
        "staff": [
            {
            "staff_id": "",
            "monday": {
                "time": "",
                "hours": 0
            },
            "tuesday": {
                "time": "",
                "hours": 0
            },
            "wednesday": {
                "time": "",
                "hours": 0
            },
            "thursday": {
                "time": "",
                "hours": 0
            },
            "friday": {
                "time": "",
                "hours": 0
            },
            "Total hour": {
                "hour": 0
            }
            }
        ]
        }
    }
    }"""
        "Ensure legal ratios are met, breaks are handled, special constraints are respected, and fairness is maintained. The schedule must be complete by Thursday noon with minimal edits needed. Ensure all names and details are correct based on the provided context."
    )
    # CONTEXT
    context = {
        'kindergarten_data':kindergarten_data,
        'contracted_hours':contracted_hours, 
        'operating_hour':operating_hours,
        'schedule_cycle':schedule_cycle,
        "frí": "Each staff member is entitled to any specific designated leave day per week information given by user, referred to as 'frí' (meaning 'free' in Faroese). Ensure that this day is consistently applied across the schedule, allowing for a single leave day per week for each staff member, specifically marked as 'Fri'. you will get this data in constraint of specific user in kindergarten_data",
        "target_weekly_hours": (
            f"MANDATORY: For each staff member, the TOTAL scheduled hours over the 4-week period MUST EQUAL their 'target_weekly_hours' multiplied by 4. "
            f"NO staff member may be scheduled for more or fewer hours than this total. "
            f"Do NOT round, estimate, or approximate—hours must match exactly. "
            f"If you cannot achieve this for any staff member, you MUST clearly list their name and the reason in a separate 'violations' field in the output. "
            f"Schedules that do not meet this requirement will be rejected. "
            f"Target Weekly Hours for each staff member: {target_weekly_hours}. "
            f"Double-check your calculations before submitting the schedule."
        ),
        "Rolling horizon": {
            "Cycle": " - Generate a schedule of 4 weeks - each week must have a different schedule than the previous one and after one schedule give a line.",
            "Operating Days": "Monday - Friday",
            "Core Hours": "07:30 - 17:15 (Extended 15 minutes)",
        },
        'constraints': f"Make sure that any hard constraint isn't violated. Here they are: {constraints}", 
        "success_criteria": {
            "legal_compliance": "No live-ratio breaches",
            "shift_quality": "≥85% of shifts pass on first run",
            "manager_effort": "Schedule editable/finalized in under 10 minutes",
            "fairness": "Even distribution of late shifts (max 1 difference over 4 weeks)"
        },
        'llm_instruction': f"""
            You are tasked with generating a JSON report based on the provided schedule data and constraints. 
            Please adhere strictly to the following instructions:

            1. **Output Format**: Your response must be a complete JSON object, following the exact structure provided in the example below. Do not include any additional text, comments, or formatting outside of the JSON structure.

            2. **JSON Structure**: Ensure that all keys and nested objects are present as specified. If any data is unavailable, use a placeholder value such as `null` or an empty string, but maintain the structure.

            3. **Error Handling**: If you encounter any issues while generating the JSON, ensure that the output is still a valid JSON object, even if some values are placeholders.

            4. **Example Structure**: {llm_instruction_prompt}

            5. **Completeness**: Double-check that the entire JSON object is included in your response. Partial responses are not acceptable.

            By following these guidelines, ensure that the JSON output is complete and correctly formatted.
            """
    }
    
    return context, constraints

def clean_json_string(json_str):
    # Remove triple backticks and language hints
    cleaned = re.sub(r"^```json\s*", "", json_str.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())

    try:
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        print("❌ JSON parsing error:", e)
        return None

def _optimize_schedule(context, constraints):
    "Sends the scheduling context to GPT and returns optimized schedule."
    base_system = (
        """You are a scheduling optimization assistant. 
        Based on the provided kindergarten staff, rooms, and constraints, generate a legal and fair weekly schedule.
        Your final output MUST be only the JSON object as specified in the user's instructions, with no additional text, markdown, or conversation. {constraints}"""
        .format(constraints=constraints)
    )
    user_msg = f"Here is the schedule input data for optimization:\n{json.dumps(context, indent=2)}\n\n{context['llm_instruction']}"
    logger.info(f"Input Prompt: {user_msg}")
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": base_system},
            {"role": "user", "content": user_msg}
        ]
    )
    logger.info(f"OpenAI API Response: {response}")
    schedule_text = response['choices'][0]['message']['content']
    logger.info(f"Type of schedule_text: {type(schedule_text)}")
    logger.info(f"Output Summary: {schedule_text[:500]}...")
    tokens_used = response['usage']['total_tokens'] if 'usage' in response else 'N/A'
    input_tokens = response['usage']['prompt_tokens'] if 'usage' in response else 'N/A'
    output_tokens = response['usage']['completion_tokens'] if 'usage' in response else 'N/A'
    cost_ = calculate_cost(input_tokens, output_tokens)
    logger.info(f"Tokens Used: {tokens_used}, Cost: {cost_}")
    tokens_details = {
        "input_token":input_tokens, 
        "output_token":output_tokens,
        "cost":cost_, 
    }
    parsed_schedule = clean_json_string(schedule_text)
    return parsed_schedule, tokens_details

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

def _constraints_check(schedule_text, constraints):
    try:
        # Stronger prompt
        base_system = """
You are a strict JSON compliance report generator. 
Your task is to evaluate the given schedule against the provided constraints and return a JSON object report.

🛑 VERY IMPORTANT:
- Return ONLY a raw JSON object.
- DO NOT return markdown formatting (like ```json).
- DO NOT include any explanation or text before/after the JSON.
- The JSON must be valid and parsable with json.loads().

✅ REQUIRED JSON STRUCTURE:
 // All fields with "PROMPT" are explicit instructions for the LLM to follow.
        {
          "AdherenceReport": {
            "HardConstraints": {
              "OperatingHours": "string",
              "SchedulerCycle": "string",
              "WeeklyHours": "string",
              "FridayEarlyLeave": "string",
            },
            "SoftConstraints": {
              "PossibleStartTimes": "string",
              "PossibleEndTimes": "string",
              "NoWastedTime": "string"
            },
            "DetailedIssues": {
              "WeeklyHours": {
                "Staff Name": "string",
                "Other staff": "string"
              },
              "Missing Staff": {"key": "value"},
              "Room Assignments": "string",
            }
          },
            - PROMPT: This is a most important thing - which you need to focus and return this | meaning you need to calculate this and return this . 
          "FairnessScore": "PROMPT: Return the fairness score as a string in the format 'X/10', where X can be an integer or one decimal (e.g., '8/10' or '8.5/10')."
        }
"""

        user_msg = f"Here is the optimized schedule text:\n{json.dumps(schedule_text, indent=2)}\n\nConstraints:\n{constraints}"

        logger.info(f"Input Prompt to constraints checker: {user_msg[:500]}...")

        response = openai.ChatCompletion.create(
            model="o3",
            messages=[
                {"role": "system", "content": base_system},
                {"role": "user", "content": user_msg}
            ]
        )

        # Token usage
        tokens_used = response['usage']['total_tokens'] if 'usage' in response else 'N/A'
        input_tokens = response['usage']['prompt_tokens'] if 'usage' in response else 'N/A'
        output_tokens = response['usage']['completion_tokens'] if 'usage' in response else 'N/A'
        cost_ = calculate_cost(input_tokens, output_tokens)
        report_ = {
            "input_token": input_tokens,
            "output_token": output_tokens,
            "cost": cost_
        }

        if 'choices' in response and response['choices']:
            _report_text = response['choices'][0]['message']['content'].strip()

            try:
                parsed_report = json.loads(_report_text)
                logger.info("Parsed JSON successfully from response.")
                return parsed_report, report_

            except json.JSONDecodeError as parse_err:
                logger.warning(f"JSON parsing failed: {parse_err}")
                logger.debug("Raw response that failed to parse:", _report_text)
                return {"error": "Failed to parse JSON response.", "raw_response": _report_text}, report_

        else:
            logger.error("Unexpected API response structure.")
            return {"error": "Unexpected response structure."}, {
                "input_token": 0, "output_token": 0, "cost": 0.0
            }

    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error during constraints check: {str(e)}")
        return {"error": f"OpenAI API Error: {str(e)}"}, {
            "input_token": 0, "output_token": 0, "cost": 0.0
        }

    except Exception as e:
        logger.error(f"Unexpected error in _constraints_check: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}, {
            "input_token": 0, "output_token": 0, "cost": 0.0
        }
   
def time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

def parse_time_block(block_str):
    start_str, end_str = block_str.split('–')
    start = time_to_minutes(start_str)
    if end_str.lower() == 'close':
        end = 24 * 60
    else:
        end = time_to_minutes(end_str)
    return (start, end)

