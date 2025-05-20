from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import render
from django.http import HttpResponse
from schedularapp.views import index
from schedularapp.views.index import index 
from schedularapp.views.brikilund import brikilund 
# def index(request):
#     return render(request, 'index.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path("index/", index, name="index"),
    path("brikilund/", brikilund, name="lillebo weekly scheduling system"),
]
