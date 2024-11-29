from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('employee/', views.employee, name='employee_page'),
    path('admin/', views.admin, name='admin_page'),
    path('employee/check-in/', views.check_in, name='check_in'),  
    path('employee/check-out/', views.check_out, name='check_out'), 
    path('manage-leaves/', views.manage_leaves, name='manage_leaves'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),

]
