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
