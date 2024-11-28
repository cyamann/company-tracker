from django.db import models
from django.contrib.auth.models import User  # Yerleşik User modeli


class Attendance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)  # Kullanıcı modeli ile ilişki
    date = models.DateField()  # Tarih

    def __str__(self):
        return f"{self.employee.username} - {self.date}"

class AttendanceLog(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='logs')  # Attendance ile ilişki
    timestamp = models.DateTimeField(auto_now_add=True)  # Zaman damgası
    action = models.CharField(max_length=10, choices=[('Check-In', 'Check-In'), ('Check-Out', 'Check-Out')])

    def __str__(self):
        return f"{self.attendance.employee.username} - {self.action} at {self.timestamp}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)  # Kullanıcı ile ilişkilendirme
    start_date = models.DateField()  # İzin başlangıç tarihi
    end_date = models.DateField()  # İzin bitiş tarihi
    reason = models.TextField()  # İzin nedeni
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Talep durumu

    def __str__(self):
        return f"{self.employee.username} - {self.start_date} to {self.end_date} ({self.status})"
