 Gunnleygur Clementsen requirements for Milestone 1:

 📦 Milestone 1: Data Ingestion & Validation

 ✅ 1. Ingestion Approach

The project begins with ingesting and validating master data — including staff, rooms, and rules — into a clean, structured JSON schema. This schema standardizes the inputs required by the LLM for generating weekly schedules and ensures the data can be easily extended, validated, and reused.

 Staff data includes role (Pedagogue, Assistant, Helper), availability, max hours, and constraints.
 Room data includes room type, child age group, required ratios, and pedagogue requirements.
 Rules data distinguishes between hard constraints (e.g., legal ratios, max shift lengths) and soft preferences (e.g., fairness in shift distribution).

All data is validated using conditional checks before submission to the LLM. Any missing or invalid entries are flagged for correction to avoid corrupt scheduling prompts.


 🧠 2. Prompting Structure

To guide the LLM in generating compliant schedules, we combine structured JSON input with a clear, descriptive instruction prompt. The basic format looks like:


You are a scheduling assistant. Based on the following staff, room details, and rules, generate a weekly schedule ensuring full legal compliance and fair distribution:

<data in JSON format>

Ensure all constraints are followed, breaks are included, and room coverage meets legal ratios.


The prompt will evolve as needed, but this structure keeps the instructions consistent while providing the full context for the model.


 📏 3. Measurement Definitions

Each rule is categorized as a hard or soft constraint:

 Hard Constraints (must-pass):

   No shift exceeds 6 hours without a break
   At least 1 pedagogue per room
   Legal child\:adult ratios met per room type
   Staff not assigned during unavailable times
   Helpers never left alone

 Soft Constraints (preferences):

   No staff opens and closes on the same day
   Max 3 opens or closes per staff per week
   Balanced distribution of Friday cleanup
   Respect for preferred roles/rooms

Each hard constraint will be programmatically evaluated on the LLM-generated output to ensure 100% compliance before acceptance.


 📊 4. Evaluation Plan

After each schedule is generated, the output will be parsed and assessed using the following metrics:

 Violation Count (hard rules): Number of detected rule breaks (should be 0)
 Fairness Score: Variation in number of opens/closes/undesirable shifts across staff
 Coverage Score: Whether all rooms were staffed during open hours
 Correction Time (optional): Time needed by the manager to fix output (target: under 10 mins)

These metrics will be logged per run to track model performance over time and drive iteration in prompt tuning or logic refinement.


<H1> Code Explaination </H1>


 🧠 Kindergarten Schedule Optimizer (AI-Powered)

This Django-based API endpoint receives staff and room scheduling data for a kindergarten, processes constraints and availability, and uses OpenAI's GPT model to generate an optimized weekly schedule. It further evaluates the generated schedule for rule violations, completeness, fairness, and coverage.



 📂 File Overview

Main File: `views.py`
Frameworks/Libraries: Django, OpenAI API, dotenv, datetime, logging, JSON



 🔧 Step-by-Step Code Breakdown

 1. Import Dependencies

python
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dotenv import load_dotenv
from datetime import datetime


 These modules handle HTTP requests, environment variables, and time tracking for the API.

python
import logging, openai, json, time, os, re


 Required for logging, interfacing with OpenAI API, JSON parsing, file/environment access, and regular expressions.



 2. Environment Setup and Logging

python
load_dotenv()   Load API keys and other environment variables
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')


 Loads `.env` file.
 Initializes logging for debugging.
 Retrieves OpenAI API key from environment variables.



 3. Main View: `brikilund`

python
@csrf_exempt
def brikilund(request):


 Disables CSRF validation (for API endpoint).
 Begins the main schedule generation logic.

 a. Start Processing Timer

python
start_time = datetime.now()


 Records the start time for performance measurement.

 b. Extract Input Context

python
context , pedagogues, assistants, helpers  = _collect_context_from_request(request)


 Parses input JSON and structures staff, room, and constraints data.

 c. Call Optimization Function

python
schedule_text = _optimize_schedule(context)


 Sends structured data to GPT for generating a weekly schedule.

 d. Evaluate the Output

python
violations = _check_violations(pedagogues, assistants, helpers)
completeness_result = _check_output_completeness(schedule_text, context)
fairness_result = _calculate_fairness_score(schedule_text, context)
coverage_result = _calculate_coverage_score(schedule_text, context)


 Runs rule checks, evaluates completeness of the output, and calculates fairness and coverage.

 e. Respond to Client

python
return JsonResponse({...})


 Returns the optimized schedule and metadata like violations, timing, and scores as JSON.

 f. Error Handling

python
except Exception as e:
    return JsonResponse({"error": str(e), ...}, status=400)


 Returns a proper error message in case of failure.



 4. \_collect\_context\_from\_request(request)

 Parses JSON POST  to extract:

   Total staff and breakdowns (pedagogues, assistants, helpers)
   Staff details (name, age, shift time)
   Room details and ratios
   Schedule blocks and time ranges
   Hard/soft constraints
   Individual staff availability
   Desired outcomes and LLM instruction

 Returns:

   `context` for GPT input
   `pedagogues`, `assistants`, `helpers` list for further validation



 5. \_check\_violations(...)

 Checks basic hard constraints:

   At least one pedagogue is scheduled.
   Assistants and helpers are not left alone.
 Returns a list of violations (if any).



 6. \_optimize\_schedule(context)

 Composes a prompt with system and user roles for GPT.
 Sends request to OpenAI's `o3` model to generate a weekly schedule.
 Extracts and returns only the GPT-generated message content.



 7. Time Utility Functions

python
def time_to_minutes(t)
def parse_time_block(block_str)


 Convert time strings like `07:00` to total minutes since midnight.
 Parse ranges like `07:00–08:00` or `15:30–Close`.



 8. \_check\_output\_completeness(schedule\_text, context)

 Validates whether the schedule contains entries for each required time block and role.
 Placeholder in code (`...`) suggests further implementation is pending or cut off.



 ✅ Planned / Additional Functions (Assumed)

python
_calculate_fairness_score(schedule_text, context)
_calculate_coverage_score(schedule_text, context)


 Likely compute:

   Distribution of shifts to ensure fairness
   Room and role coverage across the schedule



 🧪 Sample Request (JSON POST)

json
{
  "total_staff": 13,
  "no_of_pedagogues": 6,
  "pedagogue_name_1": "Alice",
  ...
}


 Include individual staff availability and shift preferences as keys.
 API responds with JSON containing the generated schedule and analysis.



 🧠 Model Used

json
"model": "o3-reasoning-model"


 Indicates the GPT model selected for optimized, structured reasoning.



 ⚠️ Notes

 Make sure `.env` file contains `OPENAI_API_KEY`
 Schedule generation assumes prompt engineering for reliability
 Designed for kindergarten use cases but adaptable to other scheduling systems


