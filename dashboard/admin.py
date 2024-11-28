from django.contrib import admin
from .models import Attendance, LeaveRequest,EmployeeProfile,Notification

admin.site.register(Attendance)
admin.site.register(LeaveRequest)

admin.site.register(EmployeeProfile)
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user_username')
