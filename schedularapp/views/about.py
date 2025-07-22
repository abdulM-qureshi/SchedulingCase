from sched import scheduler
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render

def about(request):
    if request.method == 'GET':
       return render(request,"about.html")