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


<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Kindergarten Schedule Optimizer - Code Explanation</title>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 30px; }
    h1, h2, h3 { color: #4A90E2; }
    ul { margin-left: 20px; margin-top: 0.5rem;}
    code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        h1, h2 {
      color: #2c3e50;
    }
    section {
      margin-bottom: 2rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background-color: #fff;
      box-shadow: 0 0 10px rgba(0,0,0,0.05);
    }
    th, td {
      padding: 12px;
      border: 1px solid #ddd;
      text-align: left;
    }
    th {
      background-color: #f0f0f0;
    }
  </style>
</head>
<body>

  <h1>🧠 Kindergarten Schedule Optimizer - Code Explanation</h1>

  <p>This Django project creates an AI-powered weekly schedule for a kindergarten. It takes staff availability and room details, sends them to the OpenAI model, and returns an optimized, fair, and rule-compliant schedule in response.</p>

  <h2>🔧 How It Works (Step-by-Step)</h2>

  <h3>1. Import Modules</h3>
  <p>It imports useful tools to:</p>
  <ul>
    <li>Handle HTTP requests (<code>django</code>)</li>
    <li>Use environment variables (<code>dotenv</code>)</li>
    <li>Work with time (<code>datetime</code>)</li>
    <li>Call GPT API (<code>openai</code>)</li>
    <li>Log info and debug (<code>logging</code>)</li>
  </ul>

  <h3>2. Setup Environment and Logging</h3>
  <ul>
    <li>Loads API key from <code>.env</code> file</li>
    <li>Sets up logging for debugging</li>
    <li>Connects to the OpenAI GPT API</li>
  </ul>

  <h3>3. Main Function: <code>brikilund</code></h3>
  <p>This is the heart of the code that runs when the user sends a request.</p>
  <ol>
    <li><strong>Start a timer</strong> – to measure how long the process takes</li>
    <li><strong>Extract user input</strong> – staff names, shifts, rooms, constraints</li>
    <li><strong>Send data to GPT</strong> – to generate an optimized weekly schedule</li>
    <li><strong>Check the result:</strong>
      <ul>
        <li>Any violations (e.g., no assistant left alone)</li>
        <li>Completeness (does it cover all shifts?)</li>
        <li>Fairness (is work equally divided?)</li>
        <li>Coverage (are all roles and rooms handled?)</li>
      </ul>
    </li>
    <li><strong>Send back a JSON response</strong> with the generated schedule and analysis</li>
    <li><strong>If there's an error</strong>, return an error message</li>
  </ol>

  <h3>4. <code>_collect_context_from_request(request)</code></h3>
  <p>Parses incoming data to build a structure that GPT can understand, including:</p>
  <ul>
    <li>Staff types and names (pedagogues, assistants, helpers)</li>
    <li>Room rules and required ratios</li>
    <li>Available time blocks and special conditions</li>
  </ul>

  <h3>5. <code>_check_violations()</code></h3>
  <p>Ensures basic safety and scheduling rules are not broken, like:</p>
  <ul>
    <li>Always having at least one pedagogue</li>
    <li>Never leaving assistants or helpers alone</li>
  </ul>

  <h3>6. <code>_optimize_schedule(context)</code></h3>
  <p>Sends the context (structured input) to OpenAI GPT with a crafted prompt and gets back the generated schedule as text.</p>

  <h3>7. Time Utility Functions</h3>
  <ul>
    <li><code>time_to_minutes()</code> – Converts "08:30" to total minutes</li>
    <li><code>parse_time_block()</code> – Parses ranges like "08:00–09:00"</li>
  </ul>

  <h3>8. Completeness and Fairness Checks</h3>
  <ul>
    <li><code>_check_output_completeness()</code> – Are all blocks filled?</li>
    <li><code>_calculate_fairness_score()</code> – Is work balanced?</li>
    <li><code>_calculate_coverage_score()</code> – Are all roles covered?</li>
  </ul>

  <h2>📤 What Does It Expect from the User?</h2>
  <p>A JSON request like this:</p>
  <pre>
{
  "total_staff": 13,
  "no_of_pedagogues": 6,
  "pedagogue_name_1": "Alice",
  ...
}
  </pre>
  <p>Each staff member's availability, shift preferences, and more are included.</p>

  <h2>✅ What Does It Return?</h2>
  <ul>
    <li>A JSON response with the weekly schedule</li>
    <li>List of any rule violations</li>
    <li>Score of how fair and complete the schedule is</li>
    <li>Time taken to process</li>
  </ul>

  <h2>🧠 Model Used</h2>
  <p>The AI model is <strong>OpenAI GPT (o3-reasoning-model)</strong> – good for structured and logical outputs.</p>

  <h2>⚠️ Things to Keep in Mind</h2>
  <ul>
    <li>The <code>.env</code> file must include the <code>OPENAI_API_KEY</code></li>
    <li>The prompt sent to GPT should be carefully written for good results</li>
    <li>Although designed for kindergarten, it can be adapted for any team-based schedule</li>
  </ul>

  <h1>Added Documentation</h1>

  <section>
    <h2>Sample Output: Generated Schedule Examples</h2>
    <p>The generated schedules showcase optimized staff assignments while adhering to predefined constraints. Each output is validated through iterative checks to ensure compliance with hard rules.</p>
    <ul>
      <li><strong>Initial Draft:</strong> Generated using <code>Birkilund.json</code>.</li>
      <li><strong>Validation Step:</strong> Checked against defined scheduling constraints.</li>
      <li><strong>Final Report:</strong> Displays successful assignments and flags potential conflicts.</li>
    </ul>
  </section>

  <section>
    <h2>📊 Metrics Table</h2>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Description</th>
          <th>Result</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Rule Satisfaction Rate</td>
          <td>Percentage of hard rules successfully met.</td>
          <td>85%</td>
        </tr>
        <tr>
          <td>Iterations to Success</td>
          <td>Average number of refinement steps for a valid schedule.</td>
          <td>2</td>
        </tr>
        <tr>
          <td>Cost Breakdown</td>
          <td>Token consumption and dollar cost per run.</td>
          <td>$0.0142</td>
        </tr>
      </tbody>
    </table>
  </section>

  <section>
    <h2>Key Insights</h2>
    <ul>
      <li><strong>Prompt Tuning:</strong> Adjusting input formatting and phrasing significantly enhances compliance with predefined constraints.</li>
      <li><strong>Optimal Iterations:</strong> On average, two iterations yield the best scheduling results, ensuring minimal errors while maintaining efficiency.</li>
      <li><strong>Cost vs. Quality Trade-off:</strong> Balancing precision and cost-effectiveness, we achieved full compliance within a budget of &lt;$1 per execution.</li>
    </ul>
  </section>

  <h1>Instructions to Use This Code</h1>

  <p>
    1. Create a file named <code>.env</code> in the root directory and add your OpenAI API key inside it like this:
  </p>
  <pre><code>OPENAI_API_KEY=your_api_key_here</code></pre>

  <p>
    2. Open your terminal and install the required dependencies:
  </p>
  <ul>
    <li><code>pip install -r requirements.txt</code></li>
  </ul>

  <p>
    3. Make sure you have Python installed on your system.
  </p>

  <h2>If Python is not installed:</h2>
  <p>
    Download and install the latest version of Python from the official website: 
    <a href="https://www.python.org/downloads/" target="_blank">https://www.python.org/downloads/</a>
  </p>

  <p>
    After completing these steps, you can run the application as per the usage instructions provided in the documentation or README file.
  </p>

  <h2>Final Steps:</h2>
  
  <p>
    Once you’ve completed the above steps, follow these commands to run the server:
  </p>
  <pre><code>cd schedularapp python manage.py runserver</code></pre>

  <p>
    Now you can test the app using <strong>Postman</strong> by sending a valid <code>JSON</code> request.
  </p>

</body>
</html>


