from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('employee/', views.employee, name='employee_page'),
    path('admin/', views.admin, name='admin_page'),
]
