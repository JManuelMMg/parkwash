from django.urls import path
from . import views

app_name = 'carwash'

urlpatterns = [
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('service/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('appointment/create/', views.AppointmentCreateView.as_view(), name='create_appointment'),
    path('appointments/', views.AppointmentListView.as_view(), name='appointments'),
    path('appointment/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointment/<int:pk>/cancel/', views.AppointmentCancelView.as_view(), name='cancel_appointment'),
    path('services/register/', views.register_service, name='register_service'),
] 