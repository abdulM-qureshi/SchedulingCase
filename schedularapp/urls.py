from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import render
from django.http import HttpResponse
from schedularapp.views.index import index
from schedularapp.views.brikilund import brikilund
from schedularapp.views.Kindergarten import Kindergarten
from schedularapp.views.validate import validate_schedule_only
from schedularapp.views.about import about
from schedularapp.views.home import home
from schedularapp.views.accounts import (
    login_view, signup_view, logout_view, admin_login_view,
    ForgotPasswordDoneView, ForgotPasswordView,
    ResetPasswordConfirmView, ResetPasswordCompleteView, dashboard, admin_dashboard_view,admin_users_api
)
from schedularapp.views.accounts import admin_users_api, admin_user_detail_api


urlpatterns = [
    path("dj-admin/", admin.site.urls),
    path("index/", index, name="index"),
    path("brikilund/", brikilund, name="brikilund"),
    path("admin/dashboard/tables/users/", admin_users_api, name="admin_users_api"),
    path("admin/dashboard/tables/users/<int:user_id>/", admin_user_detail_api, name="admin_user_detail_api"),
    #  Remove or comment this line:
    path("Kindergarten/", Kindergarten, name="AI ( o3 reasoning model ) based Kindergarten Schedule Management System"),

    path("validate/", validate_schedule_only, name="validate"),
    path("about/", about, name="about"),
    path("home/", home, name="home"),

    # Base URL should render login page
    path("", login_view, name="login"),

    # Public auth
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),

    # Admin auth
    path("admin/login/", admin_login_view, name="admin_login"),

    # Password reset
    path("forgot-password/", ForgotPasswordView.as_view(), name="password_reset"),
    path("forgot-password/done/", ForgotPasswordDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", ResetPasswordConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", ResetPasswordCompleteView.as_view(), name="password_reset_complete"),
    path("admin/dashboard/", admin_dashboard_view, name="admin_dashboard"),
    path("admin/dashboard/tables/users/", admin_users_api, name="admin_users_api"),

    # Protected dashboard
    path("dashboard/", dashboard, name="dashboard"),
]
