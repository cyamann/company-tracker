from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import EmployeeProfile,Notification

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if created:
        EmployeeProfile.objects.create(user=instance)

@receiver(post_save, sender=EmployeeProfile)
def check_annual_leave(sender, instance, **kwargs):
    """
    Personelin yıllık izni 3 günden az kaldığında adminlere bildirim gönderir.
    """
    if instance.annual_leave_days < 3:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Düşük Yıllık İzin Bildirimi",
                message=f"{instance.user.username} adlı personelin yıllık izni 3 günden azdır ({instance.annual_leave_days:.2f} gün).",
            )
