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
from .models import Attendance, AttendanceLog

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
        # Kullanıcı ve bugünkü tarih için yoklama kaydını al veya oluştur
        attendance, created = Attendance.objects.get_or_create(employee=request.user, date=today)
        # Yeni bir check-in log kaydı oluştur
        AttendanceLog.objects.create(attendance=attendance, action='Check-In')
        print("Check-in başarıyla kaydedildi.")  # Log
        return redirect('employee_page')  # Employee sayfasına yönlendir
    else:
        return redirect('login')  # Kullanıcı giriş yapmadıysa login sayfasına yönlendir

def check_out(request):
    if request.user.is_authenticated:  # Kullanıcının giriş yaptığını kontrol et
        today = date.today()
        try:
            # Kullanıcı ve bugünkü tarih için yoklama kaydını getir
            attendance = Attendance.objects.get(employee=request.user, date=today)
            # Yeni bir check-out log kaydı oluştur
            AttendanceLog.objects.create(attendance=attendance, action='Check-Out')
            print("Check-out başarıyla kaydedildi.")  # Log
        except Attendance.DoesNotExist:
            print("Bugün için check-in yapılmamış.")  # Log
        return redirect('employee_page')  # Employee sayfasına yönlendir
    return redirect('login')  #



def index(request):
    return render(request, 'dashboard/index.html')



from django.shortcuts import render, redirect
from .forms import LeaveRequestForm
from .models import LeaveRequest, Attendance
from django.contrib.auth.decorators import login_required
from datetime import date

from django.shortcuts import render, redirect
from .forms import LeaveRequestForm
from .models import LeaveRequest, Attendance, AttendanceLog
from django.contrib.auth.decorators import login_required

@login_required
def employee(request):
    """
    Çalışanın izin taleplerini ve yoklama kayıtlarını yönetir.
    """
    # Kullanıcı izin talebi gönderdiğinde
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user  # Kullanıcıyı ilişkilendir
            leave_request.save()
            return redirect('employee_page')  # Başarıyla kaydedildikten sonra sayfayı yenile
    else:
        form = LeaveRequestForm()

    # Kullanıcıya ait izin taleplerini ve yoklama kayıtlarını getir
    leave_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-start_date')
    attendance_logs = AttendanceLog.objects.filter(attendance__employee=request.user).order_by('-timestamp')

    # Template'e gönderilecek veri
    context = {
        'form': form,  # İzin talep formu
        'leave_requests': leave_requests,  # İzin talepleri
        'attendance_logs': attendance_logs,  # Yoklama logları
    }
    return render(request, 'dashboard/employee.html', context)





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