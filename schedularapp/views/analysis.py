from itertools import tee
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dotenv import load_dotenv
import logging
import openai
import json
import os

load_dotenv()  # load variables from .env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')
logger.info("OpenAI key loaded.")

def constraint():
    return {
        'hard_constraints': 
        """Hard Constraint (Rules that CANNOT be broken)
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
        """Soft Constraints (Goals for a "Good" Schedule)
        These rules guide the AI to create a fair and practical schedule.
        1. Shift Rotation: Opening, middle, and closing shifts should rotate fairly among staff week-to-week.
        2. Possible Start Times: 07:30, 08:00, 08:30, 09:00, or 09:30.
        3. Possible End Times: 12:00-13:30 (for half-days), or 15:00, 16:00, 16:30, 17:00.
        4. No "Wasted Time": Avoid scheduling staff to leave between 13:30 and 15:00."""
    }

@csrf_exempt
def analysis(request): 
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

    try:
        body = json.loads(request.body)
        origional_data = body.get("origional", [])
        updated_data = body.get('updated',{})
        constraints_dict = constraint()

        # SYSTEM PROMPT
        base_system = """
        You are a strict JSON compliance report generator.
        Your task is to evaluate the given schedule and user-inserted schedule information against the provided constraints and return a JSON object report.

        VERY IMPORTANT:
        - Return ONLY a raw JSON object.
        - DO NOT return markdown formatting (like ```json).
        - DO NOT include any explanation or text before/after the JSON.
        - The JSON must be valid and parsable with json.loads().
        - If your output contains anything other than JSON, your response will be rejected.
        - For comparing weekly hours - you can compare users inserted hours in `schedule_text` and others in `rooms` 

        REQUIRED JSON STRUCTURE:
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
          "FairnessScore": "PROMPT: Return the fairness score as a string in the format 'X/10', where X can be an integer or one decimal (e.g., '8/10' or '8.5/10')."
        }
        """

        # USER MESSAGE: lean, direct, no fluff
        user_msg = json.dumps({
            "Kindergarten text":origional_data,
            "schedule_text": updated_data,
            "constraints": constraints_dict
        }, indent=2)

        logger.info("Sending prompt to OpenAI...")
        response = openai.ChatCompletion.create(
            model="o3",
            messages=[
                {"role": "system", "content": base_system.strip()},
                {"role": "user", "content": user_msg}
            ]
        )

        if 'choices' in response and response['choices']:
            raw_reply = response['choices'][0]['message']['content'].strip()

            # Try to parse LLM output
            try:
                json_reply = json.loads(raw_reply)
                return JsonResponse(json_reply, safe=False)
            except json.JSONDecodeError:
                logger.error("OpenAI response is not valid JSON.")
                return JsonResponse({
                    "error": "OpenAI response was not valid JSON.",
                    "raw_output": raw_reply
                }, status=500)

        logger.error("Unexpected OpenAI response structure.")
        return JsonResponse({"error": "Unexpected response from OpenAI."}, status=500)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body", exc_info=True)
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except openai.error.OpenAIError as oe:
        logger.error(f"OpenAI API error: {str(oe)}", exc_info=True)
        return JsonResponse({'error': 'Error communicating with OpenAI API.'}, status=502)
    except KeyError as ke:
        logger.error(f"Missing key: {str(ke)}", exc_info=True)
        return JsonResponse({'error': f'Missing key: {str(ke)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)
