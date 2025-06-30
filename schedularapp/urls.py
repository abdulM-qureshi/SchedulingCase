from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import render
from django.http import HttpResponse
from schedularapp.views import index
from schedularapp.views.index import index 
from schedularapp.views.brikilund import brikilund 
from schedularapp.views.Kindergarten import Kindergarten 

urlpatterns = [
    path('admin/', admin.site.urls),
    path("index/", index, name="index"),
    path("brikilund/", brikilund, name="lillebo weekly scheduling system"),
    path("Kindergarten/", Kindergarten, name="AI ( o3 reasoning model ) based Kindergarten Schedule Management System"),
]
