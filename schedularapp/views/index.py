from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
import json

# Set your OpenAI API key in environment or settings
openai.api_key = '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'

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