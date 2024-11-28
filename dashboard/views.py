from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'dashboard/index.html')

def employee(request):
    return render(request,'employee.html')
def admin(request):
    return render(request,'admin.html')