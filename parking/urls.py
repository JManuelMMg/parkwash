from django.urls import path
from . import views

app_name = 'parking'

urlpatterns = [
    # Vistas públicas
    path('', views.ParkingSpaceListView.as_view(), name='list'),
    path('<int:pk>/', views.ParkingSpaceDetailView.as_view(), name='detail'),
    path('space/<int:pk>/occupy/', views.SpaceOccupyView.as_view(), name='space_occupy'),
    
    # Endpoint API para AJAX
    path('api/spaces/status/', views.parking_spaces_status, name='spaces_status'),
    
    # Vistas de administrador
    path('create/', views.ParkingSpaceCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.ParkingSpaceUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ParkingSpaceDeleteView.as_view(), name='delete'),
    
    # Vistas de reservas
    path('reservations/create/', views.ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/my/', views.UserReservationListView.as_view(), name='my_reservations'),
    path('reservations/<int:pk>/', views.ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservations/<int:pk>/update/', views.ReservationUpdateView.as_view(), name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.ReservationDeleteView.as_view(), name='reservation_delete'),
    path('reservations/delete_all/', views.delete_all_reservations, name='delete_all_reservations'),
    path('reservations/create_reservation/', views.create_reservation, name='create_reservation'),
    path('reservations/<int:pk>/cancel/', views.ReservationCancelView.as_view(), name='reservation_cancel'),
    path('<int:pk>/occupy/', views.SpaceOccupyView.as_view(), name='occupy'),
    path('<int:pk>/exit/', views.SpaceExitView.as_view(), name='exit'),
    path('space-cost/<int:space_id>/', views.space_cost, name='space_cost'),
] 