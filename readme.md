<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Kindergarten Schedule Optimizer - Code Explanation</title>
</head>
<body>

  <h1> Kindergarten Schedule Optimizer - Code Explanation</h1>

  <p>This Django project creates an AI-powered weekly schedule for a kindergarten. It takes staff availability and room details, sends them to the OpenAI model, and returns an optimized, fair, and rule-compliant schedule in response.</p>

  <h2> How It Works (Step-by-Step)</h2>
 

  <h2>Final Steps:</h2>
  
  <p>
    Once you’ve completed the above steps, follow these commands to run the server:
  </p>
  <pre><code>cd schedularapp
python manage.py runserver</code></pre>

  <p>
    Now you can test the app using <strong>Postman</strong> by sending a valid <code>JSON</code> request.
  </p>

  <!-- ============================== -->
  <!-- NEWLY ADDED SECTION BELOW -->
  <!-- ============================== -->

  <h1>🧩 New Features Added</h1>

  <h2>1️⃣ User Authentication System</h2>
  <ul>
    <li><strong>Signup, Login, and Logout</strong> functionality built using Django’s authentication framework.</li>
    <li>Users can register with <code>email</code>, <code>password</code>, and <code>username</code>.</li>
    <li>Form validation, error messages, and success alerts are handled in templates.</li>
    <li>Sessions are securely managed — with “Remember Me” support for persistent login.</li>
  </ul>

  <h2>2️⃣ Role-Based Access Control</h2>
  <ul>
    <li>Introduced a <code>UserProfile</code> model with a <code>role</code> field (choices: <code>Admin</code>, <code>User</code>).</li>
    <li>Each user automatically gets a profile upon creation.</li>
    <li>Admins and Superusers have access to admin-only routes and dashboards.</li>
    <li>Regular users are redirected to their respective dashboards or denied admin access.</li>
  </ul>

  <h2>3️⃣ Admin Login</h2>
  <ul>
    <li>Custom admin login page (<code>/admin/login/</code>) separate from Django’s default admin panel.</li>
    <li>Allows authentication via <code>username</code> or <code>email</code>.</li>
    <li>Restricts access to users who are either:
      <ul>
        <li><strong>Superusers</strong> (created via <code>createsuperuser</code> command), or</li>
        <li>Users whose profile role = <code>Admin</code></li>
      </ul>
    </li>
    <li>Successful login redirects directly to the custom <code>Admin Dashboard</code>.</li>
  </ul>

  <h2>4️⃣ Admin Dashboard (Custom Interface)</h2>
  <p>A dedicated, fully responsive admin panel built using Bootstrap 5 and Font Awesome icons.</p>

  <h3>Features:</h3>
  <ul>
    <li> Displays all registered users with name and email.</li>
    <li> <strong>Create User</strong> – Add new users directly from the admin panel.</li>
    <li> <strong>Edit User</strong> – Update user details inline using modal forms.</li>
    <li> <strong>Delete User</strong> – Remove users safely with confirmation dialogs.</li>
    <li> Shows total user count dynamically.</li>
  </ul>

  <h3>Technical Notes:</h3>
  <ul>
    <li>All actions (create, update, delete) use AJAX via <code>fetch()</code> and Django JSON APIs.</li>
    <li>Endpoints:
      <ul>
        <li><code>/admin/dashboard/</code> → Admin home view</li>
        <li><code>/admin/dashboard/tables/users/</code> → User CRUD REST API</li>
      </ul>
    </li>
    <li>CSRF tokens handled automatically for secure requests.</li>
    <li>Modal popups are centered using flexbox and animated transitions.</li>
  </ul>

  <h2>5️⃣ Code Highlights</h2>
  <ul>
    <li><strong>Views:</strong> <code>admin_login_view()</code>, <code>admin_dashboard_view()</code>, and CRUD views for users.</li>
    <li><strong>Forms:</strong> <code>AdminLoginForm</code> for validating admin credentials.</li>
    <li><strong>Models:</strong> <code>UserProfile</code> linked to Django’s User model for role-based access.</li>
    <li><strong>Static Files:</strong>
      <ul>
        <li><code>admin_dashboard.css</code> – Full styling for dashboard, modals, and buttons.</li>
        <li><code>admin_dashboard.js</code> – Handles all AJAX operations, form submission, and UI rendering.</li>
      </ul>
    </li>
  </ul>

  <h2>6️⃣ Security Enhancements</h2>
  <ul>
    <li>All admin routes protected by authentication and role checks.</li>
    <li>CSRF protection enabled site-wide.</li>
    <li>Session expiry control implemented (“Remember this device”).</li>
  </ul>

  <h2>7️⃣ UI Enhancements</h2>
  <ul>
    <li>Centered modals with background blur.</li>
    <li>Responsive layout for mobile and desktop views.</li>
    <li>Consistent button spacing and shadow animations.</li>
  </ul>

  <hr />
  <p><em>✨ This update enhances both the user experience and system security by introducing a complete role-based admin management module integrated with Django authentication.</em></p>

</body>
</html>
