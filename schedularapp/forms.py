from django import forms
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class SignupForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(email=cleaned.get("email")).exists():
            raise forms.ValidationError("Email already registered.")
        return cleaned

    def save(self, role="User"):
        name = self.cleaned_data["full_name"].strip()
        first_name, *rest = name.split(" ", 1)
        last_name = rest[0] if rest else ""
        user = User.objects.create_user(
            username=self.cleaned_data["email"],  # using email as username
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=first_name,
            last_name=last_name,
        )
        # If you have UserProfile auto-created by signals, set role:
        try:
            user.profile.role = role
            user.profile.save()
        except Exception:
            pass
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def authenticate_user(self, request):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]
        return authenticate(request, username=email, password=password)

class AdminLoginForm(forms.Form):
    """
    Accepts a username OR an email in the `username` field.
    No min_length on password so existing superuser passwords won't get rejected.
    """
    username = forms.CharField(max_length=150, label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)   # no min_length here

    def authenticate_user(self, request):
        username_or_email = self.cleaned_data.get("username", "").strip()
        password = self.cleaned_data.get("password")
        if not username_or_email or not password:
            return None

        # 1) Try direct authenticate with provided username
        user = authenticate(request, username=username_or_email, password=password)
        if user:
            return user

        # 2) Try lookup by email then authenticate with that username
        try:
            user_obj = User.objects.get(email__iexact=username_or_email)
            return authenticate(request, username=user_obj.get_username(), password=password)
        except User.DoesNotExist:
            return None