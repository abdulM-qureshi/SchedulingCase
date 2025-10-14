from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import render
from django.http import HttpResponse
from schedularapp.views import index
from schedularapp.views.index import index 
from schedularapp.views.brikilund import brikilund 
from schedularapp.views.Kindergarten import Kindergarten 
from schedularapp.views.validate import validate_schedule_only 
from schedularapp.views.about import about 
from schedularapp.views.home import home 
# from schedularapp.views.home import register_view, login_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path("index/", index, name="index"),
    path("brikilund/", brikilund, name="lillebo weekly scheduling system"),
    path("", Kindergarten, name="AI ( o3 reasoning model ) based Kindergarten Schedule Management System"),
    path("validate/", validate_schedule_only, name=" Editor schedule vlidtion "),
    path("about/", about, name="About page"),
    path("home/", home, name="landing page"),
    # path('register/', register_view, name='register'),
    # path('login/', login_view, name='login'),
]
