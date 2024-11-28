from django.http import HttpResponse

from django.shortcuts import render, redirect
from .models import Attendance
from django.utils.timezone import now
from datetime import date
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import render, redirect
from .forms import LeaveRequestForm
from .models import LeaveRequest
def login(request):
    if request.method == 'POST':
        # Formdan gelen verileri al
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Kullanıcıyı doğrula
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  # Kullanıcıyı oturum başlat
            # Kullanıcı rolüne göre yönlendirme yap
            if user.is_superuser:
                return redirect('admin_page')
            else:
                return redirect('employee_page')
        else:
            return HttpResponse("Invalid username or password.")  # Hatalı giriş
    return render(request, 'dashboard/login.html')  # Login template

def logout_view(request):
    logout(request)
    return redirect('login')  # Çıkış yaptıktan sonra login sayfasına yönlendir


def check_in(request):
    if request.user.is_authenticated:  # Kullanıcının giriş yapıp yapmadığını kontrol et
        today = date.today()
        attendance, created = Attendance.objects.get_or_create(employee=request.user, date=today)
        if not attendance.check_in_time:  # Eğer daha önce check-in yapılmadıysa
            attendance.check_in_time = now().time()
            attendance.save()
            print("Check-in başarıyla kaydedildi.")  # Hata ayıklama için log
        else:
            print("Zaten check-in yapılmış.")
        return redirect('employee_page')  # İşlem sonrası employee sayfasına yönlendir
    else:
        return redirect('login')  # Kullanıcı giriş yapmadıysa login sayfasına yönlendir
def check_out(request):
    if request.user.is_authenticated:  # Kullanıcının giriş yaptığını kontrol et
        today = date.today()
        try:
            attendance = Attendance.objects.get(employee=request.user, date=today)
            if not attendance.check_out_time:
                attendance.check_out_time = now().time()
                attendance.save()
        except Attendance.DoesNotExist:
            pass
        return redirect('employee_page')  # Employee sayfasına yönlendirme
    return redirect('login')  # Giriş yapılmadıysa login sayfasına yönlendir


def employee(request):

    return render(request, 'dashboard/employee.html') 

def index(request):
    return render(request, 'dashboard/index.html')



def employee(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user  # Giriş yapmış kullanıcıyı ata
            leave_request.save()
            return redirect('employee_page')  # İzin talebi sonrası sayfaya dön
    else:
        form = LeaveRequestForm()

    leave_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-start_date')  # Kullanıcıya ait talepler
    return render(request, 'dashboard/employee.html', {'form': form, 'leave_requests': leave_requests})
def admin(request):
    return render(request, 'dashboard/admin.html')
def manage_leaves(request):
    leave_requests = LeaveRequest.objects.all().order_by('-start_date')  # Tüm talepleri al

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave_request = LeaveRequest.objects.get(id=leave_id)
        if action == 'approve':
            leave_request.status = 'Approved'
        elif action == 'reject':
            leave_request.status = 'Rejected'
        leave_request.save()
        return redirect('manage_leaves')  # İşlem sonrası sayfayı yenile

    return render(request, 'dashboard/manage_leaves.html', {'leave_requests': leave_requests})