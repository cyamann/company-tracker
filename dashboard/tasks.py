from celery import shared_task
from datetime import datetime, date, time
from django.contrib.auth.models import User
from .models import Notification
import logging

# İş başlangıç saati
START_TIME = time(8, 0)

# Logger tanımlama
logger = logging.getLogger(__name__)

@shared_task
def notify_admin_for_late_employee(employee_id, check_in_time_str):
    """
    Geç check-in yapan çalışan için adminlere bildirim gönderir.
    """
    try:
        logger.info(f"Görev başladı: employee_id={employee_id}, check_in_time_str={check_in_time_str}")

        # Kullanıcıyı al
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            logger.error(f"Kullanıcı bulunamadı: employee_id={employee_id}")
            return

        # Check-in zamanını string'den datetime.time objesine çevir
        try:
            check_in_time = datetime.strptime(check_in_time_str, "%H:%M:%S").time()
        except ValueError as e:
            logger.error(f"Check-in saati format hatası: {check_in_time_str}. Hata: {e}")
            return

        # Geç kalma süresini hesapla
        if check_in_time > START_TIME:
            late_minutes = (datetime.combine(date.today(), check_in_time) - datetime.combine(date.today(), START_TIME)).seconds // 60
            logger.info(f"Geç kalma süresi hesaplandı: {late_minutes} dakika")
        else:
            logger.info("Geç kalma durumu yok.")
            return

        # Adminler için bildirim oluştur
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Geç Kalma Bildirimi",
                message=f"{employee.username} adlı personel {late_minutes} dakika geç kalmıştır.",
            )
            logger.info(f"Bildirim oluşturuldu: {admin.username} için")
    except Exception as e:
        logger.error(f"Task error: {e}")
        raise
