from django.contrib import admin
from .models import Attendance, LeaveRequest, EmployeeProfile, Notification

admin.site.register(Attendance)

admin.site.register(EmployeeProfile)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')  # Doğru alan ismi için düzeltme

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status')

    def save_model(self, request, obj, form, change):
        if obj.status == 'Approved':
            try:
                employee_profile = EmployeeProfile.objects.get(user=obj.employee)
                leave_duration = (obj.end_date - obj.start_date).days + 1

                if employee_profile.annual_leave_days >= leave_duration:
                    employee_profile.annual_leave_days -= leave_duration
                    employee_profile.save()
                else:
                    self.message_user(request, "Yıllık izin yetersiz!", level='error')
            except EmployeeProfile.DoesNotExist:
                self.message_user(request, "Employee profile bulunamadı!", level='error')

        super().save_model(request, obj, form, change)
