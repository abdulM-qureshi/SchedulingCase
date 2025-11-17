import sys
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from ..forms import LoginForm  # adjust import path if needed
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from schedularapp.forms import SignupForm, LoginForm, AdminLoginForm
from schedularapp.views.Kindergarten import Kindergarten
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
import json
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User



def login_view(request):
    """
    Debuggable login view.
    - Prints debug info to server console.
    - Authenticates and redirects to `next` or dashboard on success.
    """
    # DEBUG: print basic request info
    print("LOGIN_VIEW: method=", request.method, file=sys.stderr)

    next_url = request.GET.get("next") or request.POST.get("next") or None

    if request.method == "POST":
        print("LOGIN_VIEW: POST payload:", request.POST.dict(), file=sys.stderr)
        form = LoginForm(request.POST)
        print("LOGIN_VIEW: form.is_valid() ->", form.is_valid(), file=sys.stderr)
        if form.is_valid():
            user = form.authenticate_user(request)
            print("LOGIN_VIEW: authenticate returned:", repr(getattr(user, 'username', None)), file=sys.stderr)
            if user:
                if not user.is_active:
                    messages.error(request, "Account is inactive. Contact admin.")
                    print("LOGIN_VIEW: account inactive for:", user.username, file=sys.stderr)
                    return render(request, "login.html", {"form": form})

                login(request, user)
                remember = request.POST.get("rememberMe")
                if not remember:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

                # safe next redirect
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    print("LOGIN_VIEW: redirecting to next:", next_url, file=sys.stderr)
                    return HttpResponseRedirect(next_url)
                print("LOGIN_VIEW: redirecting to dashboard", file=sys.stderr)
                return HttpResponseRedirect("/dashboard/")
            else:
                messages.error(request, "Invalid email or password.")
                print("LOGIN_VIEW: authentication failed (invalid credentials)", file=sys.stderr)
        else:
            # form invalid
            print("LOGIN_VIEW: form.errors ->", form.errors.as_json(), file=sys.stderr)
            messages.error(request, "Please fix the errors and try again.")
    else:
        # Optional: force logout on GET if you want always fresh login
        # if request.user.is_authenticated:
        #     logout(request)
        form = LoginForm()

    context = {"form": form}
    if next_url:
        context["next"] = next_url
    return render(request, "login.html", context)

#Signup
def signup_view(request):
    # If already logged in, keep previous behavior (optional)
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(role="User")
            # Do NOT log the user in automatically.
            # Instead, show a success message and redirect to login.
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("login")
        # if invalid, falls through and re-renders form with errors
    else:
        form = SignupForm()
    return render(request, "signup.html", {"form": form})

# ---------- LOGOUT
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

# ---------- CUSTOM ADMIN LOGIN at /admin/login/

def admin_login_view(request):
    """
    Custom admin login:
    Accepts username or email + password via AdminLoginForm.
    Allows access if user.is_superuser OR user.profile.role == "Admin".
    Redirects to /admin/dashboard/ upon success.
    """

    # Already logged in and authorized → send directly to admin dashboard
    if request.user.is_authenticated:
        try:
            if request.user.is_superuser or getattr(request.user.profile, "role", None) == "Admin":
                return redirect("admin_dashboard")
        except Exception:
            if request.user.is_superuser:
                return redirect("admin_dashboard")

    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            user = form.authenticate_user(request)
            if not user:
                messages.error(request, "Invalid administrator credentials.")
                return render(request, "admin_login.html", {"form": form})

            # Check if admin
            is_admin_by_role = getattr(getattr(user, "profile", None), "role", None) == "Admin"
            if not (user.is_superuser or is_admin_by_role):
                messages.error(request, "Admin access required (user is not assigned Admin role).")
                return render(request, "admin_login.html", {"form": form})

            if not user.is_active:
                messages.error(request, "Account inactive. Contact system administrator.")
                return render(request, "admin_login.html", {"form": form})

            # Log in
            login(request, user)

            # Remember session duration
            remember = request.POST.get("rememberDevice")
            if not remember:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)

            # Redirect to Admin Dashboard
            messages.success(request, "Admin login successful — redirecting to admin panel...")
            return redirect("admin_dashboard")

        else:
            messages.error(request, "Please fix the errors below and try again.")
    else:
        form = AdminLoginForm()

    return render(request, "admin_login.html", {"form": form})


@login_required(login_url='admin_login')
def admin_dashboard_view(request):
    """
    Admin dashboard view
    - Only accessible to users with Admin role or is_staff=True
    - Renders templates/admin_dashboard.html
    """
    user = request.user
    role = getattr(getattr(user, "profile", None), "role", None)

    if not (user.is_staff or role == "Admin"):
        messages.error(request, "Unauthorized access. Admins only.")
        return redirect("admin_login")

    return render(request, "admin_dashboard.html")



# ---------- PASSWORD RESET (Django built-ins)
class ForgotPasswordView(PasswordResetView):
    template_name = "forgot_password.html"
    email_template_name = "password_reset_email.html"
    subject_template_name = "password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

class ForgotPasswordDoneView(PasswordResetDoneView):
    template_name = "password_reset_done.html"

class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = "reset_password.html"
    success_url = reverse_lazy("password_reset_complete")

class ResetPasswordCompleteView(PasswordResetCompleteView):
    template_name = "password_reset_complete.html"

# ---------- DASHBOARD: your existing view (rename route only)
from schedularapp.views import Kindergarten as _Kindergarten  # if this is how it’s defined; otherwise import correctly

@login_required
def dashboard(request):
    # Call/forward to your existing Kindergarten implementation/template
    return Kindergarten(request)


def _is_admin_user(user):
    """Helper: returns True if the user is allowed admin dashboard access."""
    try:
        return user.is_authenticated and (user.is_superuser or getattr(user.profile, "role", None) == "Admin")
    except Exception:
        return user.is_authenticated and user.is_superuser
    


# @login_required(login_url="admin_login")
# @require_http_methods(["GET", "POST"])
# def admin_users_api(request):
#     """
#     GET: return list of users as JSON
#     POST: create a new user from JSON payload { "fullName": "...", "email": "..." }
#     """
#     if not _is_admin_user(request.user):
#         return HttpResponseForbidden(json.dumps({"error": "Admin access required"}), content_type="application/json")

#     if request.method == "GET":
#         users = User.objects.order_by("-date_joined").values(
#             "id", "first_name", "last_name", "email", "is_active", "date_joined", "username"
#         )
#         # Map into a friendly list
#         data = [
#             {
#                 "id": u["id"],
#                 "full_name": f"{u['first_name']} {u['last_name']}".strip(),
#                 "email": u["email"],
#                 "is_active": u["is_active"],
#                 "username": u["username"],
#                 "date_joined": u["date_joined"].isoformat() if u["date_joined"] else None,
#             }
#             for u in users
#         ]
#         return JsonResponse({"users": data})

#     # POST: create new user
#     try:
#         payload = json.loads(request.body.decode("utf-8"))
#     except Exception:
#         return HttpResponseBadRequest(json.dumps({"error": "Invalid JSON"}), content_type="application/json")

#     full_name = (payload.get("fullName") or "").strip()
#     email = (payload.get("email") or "").strip()
#     # optional: allow password in payload or generate one
#     password = payload.get("password")  # optional

#     if not full_name or not email:
#         return HttpResponseBadRequest(json.dumps({"error": "fullName and email are required"}), content_type="application/json")

#     if User.objects.filter(email__iexact=email).exists():
#         return HttpResponseBadRequest(json.dumps({"error": "Email already registered"}), content_type="application/json")

#     # Build username from email (or use part before '@')
#     username = email.split("@")[0]
#     # ensure username unique
#     base = username
#     i = 1
#     while User.objects.filter(username=username).exists():
#         username = f"{base}{i}"
#         i += 1

#     # split full name into first/last
#     parts = full_name.split(" ", 1)
#     first_name = parts[0]
#     last_name = parts[1] if len(parts) > 1 else ""

#     # If no password supplied, create a random one and (optionally) email later
#     if not password:
#         # keep a simple temporary password (you can replace with better generator)
#         import secrets, string
#         password = secrets.token_urlsafe(8)

#     user = User.objects.create_user(
#         username=username,
#         email=email,
#         password=password,
#         first_name=first_name,
#         last_name=last_name,
#     )

#     # If you have a UserProfile signal, it should auto-create profile. Otherwise set default:
#     try:
#         # set role to "User" by default if profile exists
#         profile = getattr(user, "profile", None)
#         if profile:
#             profile.role = "User"
#             profile.save()
#     except Exception:
#         pass

#     # Return created user info (do NOT return password)
#     created = {
#         "id": user.id,
#         "full_name": f"{user.first_name} {user.last_name}".strip(),
#         "email": user.email,
#         "username": user.username,
#     }
#     return JsonResponse({"user": created}, status=201)

# GET list and POST create
@login_required(login_url="admin_login")
@require_http_methods(["GET", "POST"])
def admin_users_api(request):
    if not _is_admin_user(request.user):
        return HttpResponseForbidden(json.dumps({"error": "Admin access required"}), content_type="application/json")

    if request.method == "GET":
        users = User.objects.order_by("-date_joined").values(
            "id", "first_name", "last_name", "email", "is_active", "username", "date_joined"
        )
        data = [
            {
                "id": u["id"],
                "full_name": f"{u['first_name']} {u['last_name']}".strip(),
                "email": u["email"],
                "is_active": u["is_active"],
                "username": u["username"],
                "date_joined": u["date_joined"].isoformat() if u["date_joined"] else None,
            }
            for u in users
        ]
        return JsonResponse({"users": data})

    # POST -> create user
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest(json.dumps({"error": "Invalid JSON"}), content_type="application/json")

    full_name = (payload.get("fullName") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password")  # optional

    if not full_name or not email:
        return HttpResponseBadRequest(json.dumps({"error": "fullName and email are required"}), content_type="application/json")

    if User.objects.filter(email__iexact=email).exists():
        return HttpResponseBadRequest(json.dumps({"error": "Email already registered"}), content_type="application/json")

    username = email.split("@")[0]
    base = username
    i = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{i}"
        i += 1

    parts = full_name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    if not password:
        import secrets
        password = secrets.token_urlsafe(8)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    # try to set profile.role if profile exists (signals may have created it)
    try:
        profile = getattr(user, "profile", None)
        if profile:
            profile.role = "User"
            profile.save()
    except Exception:
        pass

    created = {
        "id": user.id,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "username": user.username,
    }
    return JsonResponse({"user": created}, status=201)


# PUT & DELETE on a specific user
@login_required(login_url="admin_login")
@require_http_methods(["PUT", "DELETE"])
def admin_user_detail_api(request, user_id):
    if not _is_admin_user(request.user):
        return HttpResponseForbidden(json.dumps({"error": "Admin access required"}), content_type="application/json")

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Http404("User not found")

    if request.method == "DELETE":
        # Prevent admin delete of themselves (optional)
        if user == request.user:
            return HttpResponseBadRequest(json.dumps({"error": "Cannot delete yourself"}), content_type="application/json")
        user.delete()
        return JsonResponse({"deleted": True})

    # PUT -> update user
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest(json.dumps({"error": "Invalid JSON"}), content_type="application/json")

    # Allowed updates: fullName, email, is_active, password (optional)
    full_name = payload.get("fullName")
    email = payload.get("email")
    is_active = payload.get("isActive")
    new_password = payload.get("password")

    if email:
        # If email is already used by different user, reject
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            return HttpResponseBadRequest(json.dumps({"error": "Email already in use"}), content_type="application/json")
        user.email = email
        # optionally update username to email prefix? we leave username untouched

    if full_name is not None:
        parts = full_name.strip().split(" ", 1)
        user.first_name = parts[0] if parts else ""
        user.last_name = parts[1] if len(parts) > 1 else ""

    if is_active is not None:
        # ensure boolean
        user.is_active = bool(is_active)

    if new_password:
        user.set_password(new_password)

    user.save()

    # update profile role if provided (optional)
    role = payload.get("role")
    if role:
        try:
            profile = getattr(user, "profile", None)
            if profile:
                profile.role = role
                profile.save()
        except Exception:
            pass

    updated = {
        "id": user.id,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
    }
    return JsonResponse({"user": updated})

