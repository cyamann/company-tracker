from django.http import HttpResponse
from .tasks import notify_admin_for_late_employee
from django.db.models import F
from .models import Notification

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
from datetime import date, datetime, time, timedelta
from .models import Attendance, AttendanceLog, EmployeeProfile
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

# Sabitler
START_TIME = time(8, 0)  # İş başlangıç saati: 08:00
END_TIME = time(18, 0)  # İş bitiş saati: 18:00
WEEKEND_DAYS = [5, 6]  # Cumartesi ve Pazar (5 = Cumartesi, 6 = Pazar)


def update_annual_leave(employee, new_leave_days):
    """
    Personelin yıllık iznini günceller.
    """
    profile = EmployeeProfile.objects.get(user=employee)
    profile.annual_leave_days = new_leave_days
    profile.save()  # Signal otomatik olarak tetiklenecek


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

START_TIME = time(8, 0)  

@login_required
def check_in(request):
    today = date.today()

    # Tatil günlerini kontrol et
    if today.weekday() >= 5:  # Cumartesi veya Pazar
        return redirect('employee_page')

    # Attendance kaydı al veya oluştur
    attendance, created = Attendance.objects.get_or_create(employee=request.user, date=today)

    # Check-in zamanını al
    check_in_time = now().time()
    AttendanceLog.objects.create(attendance=attendance, action='Check-In', timestamp=now())

    # Geç kalma kontrolü
    if check_in_time > START_TIME:
        late_minutes = (datetime.combine(today, check_in_time) - datetime.combine(today, START_TIME)).seconds // 60
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Geç Kalma Bildirimi",
                message=f"{request.user.username} adlı personel {late_minutes} dakika geç kalmıştır.",
            )
    return redirect('employee_page')



@login_required
def notification_list(request):
    """
    Admin kullanıcılar için tüm bildirimleri döner.
    """
    if not request.user.is_superuser:
        return redirect('login')  # Sadece admin kullanıcılar erişebilir

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/notification_list.html', {'notifications': notifications})

@login_required
def check_out(request):
    if request.user.is_authenticated:
        today = date.today()

        try:
            # Kullanıcıya ait Attendance kaydı al
            attendance = Attendance.objects.get(employee=request.user, date=today)

            # Check-out log kaydı oluştur
            check_out_time = now().time()
            AttendanceLog.objects.create(attendance=attendance, action='Check-Out', timestamp=now())

            # Erken çıkma kontrolü
            if check_out_time < END_TIME:
                early_minutes = (datetime.combine(today, END_TIME) - datetime.combine(today, check_out_time)).seconds / 60
                early_hours = early_minutes / 60
                print(f"Erken çıkma: {early_minutes} dakika")

                # Saat bazında izin kesintisi
                profile = EmployeeProfile.objects.get(user=request.user)
                hours_to_deduct = early_minutes / 60  # Saat olarak kesilecek izin
                profile.annual_leave_days -= hours_to_deduct / 8  # Günlük izin saat üzerinden gün hesaplanır
                profile.save()

                # Yetkiliye bildirim gönder
                print(f"{request.user.username} erken çıktı. {early_minutes} dakika.")
            else:
                print(f"{request.user.username} iş saatine uygun şekilde çıkış yaptı.")
        except Attendance.DoesNotExist:
            print("Bugün için check-in yapılmamış.")
        return redirect('employee_page')
    return redirect('login')


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('admin_dashboard')


def index(request):
    return render(request, 'dashboard/index.html')



@login_required
def employee(request):
    """
    Çalışanın izin taleplerini, yoklama kayıtlarını ve yıllık izin günlerini yönetir.
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

    # Kullanıcının yıllık izin günlerini formatla
    profile = EmployeeProfile.objects.get(user=request.user)
    formatted_leave_days = format_leave_days(profile.annual_leave_days)

    # Template'e gönderilecek veri
    context = {
        'form': form,  # İzin talep formu
        'leave_requests': leave_requests,  # İzin talepleri
        'attendance_logs': attendance_logs,  # Yoklama logları
        'formatted_leave_days': formatted_leave_days,  # Formatlanmış yıllık izin günleri
    }
    return render(request, 'dashboard/employee.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    leave_requests = LeaveRequest.objects.filter(status='Pending')  # Onay bekleyen izinler
    total_leave_requests = LeaveRequest.objects.all().count()  # Toplam izin talebi

    return render(request, 'dashboard/admin_dashboard.html', {
        'notifications': notifications,
        'leave_requests': leave_requests,
        'total_leave_requests': total_leave_requests,
    })


def admin(request):
    return render(request, 'dashboard/admin.html')

from django.contrib import messages

def manage_leaves(request):
    print("manage_leaves fonksiyonu çağrıldı.")

    leave_requests = LeaveRequest.objects.all().order_by('-start_date')  # Tüm izin taleplerini al
    employee_profiles = EmployeeProfile.objects.all()  # Tüm çalışan profillerini al

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave_request = LeaveRequest.objects.get(id=leave_id)

        if action == 'approve':
            leave_request.status = 'Approved'
            print(f"Leave duration: {leave_duration}, Remaining leave days: {employee_profile.annual_leave_days}")

            # İzin günlerinden düşme işlemi
            try:
                employee_profile = EmployeeProfile.objects.get(user=leave_request.employee)
                leave_duration = (leave_request.end_date - leave_request.start_date).days + 1

                # Negatif izin günlerini engelle
                if employee_profile.annual_leave_days >= leave_duration:
                    employee_profile.annual_leave_days -= leave_duration
                    employee_profile.save()
                    print(f"Leave duration: {leave_duration}, Remaining leave days: {employee_profile.annual_leave_days}")

                    # Kullanıcıya başarı mesajı gönder
                    messages.success(request, f"{leave_request.employee.username} için izin onaylandı. Kalan izin günleri: {employee_profile.annual_leave_days:.2f} gün.")
                else:
                    messages.error(request, "Yıllık izin yetersiz!")  # İzin yeterli değilse hata ver
            except EmployeeProfile.DoesNotExist:
                messages.error(request, "Employee profile bulunamadı!")  # Kullanıcı profili yoksa hata ver

        elif action == 'reject':
            leave_request.status = 'Rejected'
            messages.info(request, f"{leave_request.employee.username} için izin reddedildi.")

        leave_request.save()
        return redirect('manage_leaves')  # İşlem sonrası aynı sayfaya yönlendir

    # Şablona izin taleplerini ve çalışan profillerini gönder
    return render(request, 'dashboard/manage_leaves.html', {
        'leave_requests': leave_requests,
        'employee_profiles': employee_profiles
    })


def format_leave_days(leave_days):
    """
    Gün, saat ve dakika olarak yıllık izin günlerini formatlar.
    Negatif değerleri sıfır olarak gösterir.
    """
    if leave_days < 0:
        leave_days = 0  # Negatif değerleri sıfıra eşitle

    total_minutes = leave_days * 8 * 60  # Gün -> Saat -> Dakika
    days = total_minutes // (8 * 60)  # Gün sayısı
    hours = (total_minutes % (8 * 60)) // 60  # Saat sayısı
    minutes = total_minutes % 60  # Dakika sayısı
    return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"

