from django.http import HttpResponse
from .tasks import notify_admin_for_late_employee
from django.db.models import F
from .models import Notification,Attendance, AttendanceLog,LeaveRequest,EmployeeProfile

from django.shortcuts import render, redirect
from django.utils.timezone import now
from datetime import date, datetime, time, timedelta
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from .forms import LeaveRequestForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

START_TIME = time(8, 0)  
END_TIME = time(18, 0) 
WEEKEND_DAYS = [5, 6] 


def update_annual_leave(employee, new_leave_days):

    profile = EmployeeProfile.objects.get(user=employee)
    profile.annual_leave_days = new_leave_days
    profile.save()


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect('admin_page')
            else:
                return redirect('employee_page')
        else:
            return HttpResponse("Invalid username or password.")
    return render(request, 'dashboard/login.html') 

def logout_view(request):
    logout(request)
    return redirect('login') 

START_TIME = time(8, 0)  

@login_required
def check_in(request):
    today = date.today()

    if today.weekday() >= 5: 
        return redirect('employee_page')

    attendance, created = Attendance.objects.get_or_create(employee=request.user, date=today)

    check_in_time = now().time()
    AttendanceLog.objects.create(attendance=attendance, action='Check-In', timestamp=now())

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

    if not request.user.is_superuser:
        return redirect('login')  

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/notification_list.html', {'notifications': notifications})

@login_required
def check_out(request):
    if request.user.is_authenticated:
        today = date.today()

        try:
            attendance = Attendance.objects.get(employee=request.user, date=today)

            check_out_time = now().time()
            AttendanceLog.objects.create(attendance=attendance, action='Check-Out', timestamp=now())

            if check_out_time < END_TIME:
                early_minutes = (datetime.combine(today, END_TIME) - datetime.combine(today, check_out_time)).seconds / 60
                early_hours = early_minutes / 60
                print(f"Erken çıkma: {early_minutes} dakika")

                profile = EmployeeProfile.objects.get(user=request.user)
                hours_to_deduct = early_minutes / 60 
                profile.annual_leave_days -= hours_to_deduct / 8
                profile.save()

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

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user 
            leave_request.save()
            return redirect('employee_page') 
    else:
        form = LeaveRequestForm()

    leave_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-start_date')
    attendance_logs = AttendanceLog.objects.filter(attendance__employee=request.user).order_by('-timestamp')

    profile = EmployeeProfile.objects.get(user=request.user)
    formatted_leave_days = format_leave_days(profile.annual_leave_days)

    context = {
        'form': form,  
        'leave_requests': leave_requests,  
        'attendance_logs': attendance_logs,  
        'formatted_leave_days': formatted_leave_days, 
    }
    return render(request, 'dashboard/employee.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    leave_requests = LeaveRequest.objects.filter(status='Pending') 
    total_leave_requests = LeaveRequest.objects.all().count()  

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

    leave_requests = LeaveRequest.objects.all().order_by('-start_date')  
    employee_profiles = EmployeeProfile.objects.all() 

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave_request = LeaveRequest.objects.get(id=leave_id)

        if action == 'approve':
            leave_request.status = 'Approved'
            print(f"Leave duration: {leave_duration}, Remaining leave days: {employee_profile.annual_leave_days}")

            try:
                employee_profile = EmployeeProfile.objects.get(user=leave_request.employee)
                leave_duration = (leave_request.end_date - leave_request.start_date).days + 1

                if employee_profile.annual_leave_days >= leave_duration:
                    employee_profile.annual_leave_days -= leave_duration
                    employee_profile.save()
                    print(f"Leave duration: {leave_duration}, Remaining leave days: {employee_profile.annual_leave_days}")

                    messages.success(request, f"{leave_request.employee.username} için izin onaylandı. Kalan izin günleri: {employee_profile.annual_leave_days:.2f} gün.")
                else:
                    messages.error(request, "Yıllık izin yetersiz!") 
            except EmployeeProfile.DoesNotExist:
                messages.error(request, "Employee profile bulunamadı!")

        elif action == 'reject':
            leave_request.status = 'Rejected'
            messages.info(request, f"{leave_request.employee.username} için izin reddedildi.")

        leave_request.save()
        return redirect('manage_leaves')  

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
        leave_days = 0

    total_minutes = leave_days * 8 * 60 
    days = total_minutes // (8 * 60) 
    hours = (total_minutes % (8 * 60)) // 60  
    minutes = total_minutes % 60  
    return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"

