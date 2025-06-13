from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileEditView.as_view(), name='edit_profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html'
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('preferences/', views.UserPreferenceView.as_view(), name='preferences'),
    path('vehicles/', views.UserVehicleListView.as_view(), name='vehicles'),
    path('vehicles/add/', views.UserVehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.UserVehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', views.UserVehicleDeleteView.as_view(), name='vehicle_delete'),
    path('recurring-reservations/', views.RecurringReservationListView.as_view(), name='recurring_reservations'),
    path('2fa/setup/', views.TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('2fa/verify/', views.TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('2fa/disable/', views.TwoFactorDisableView.as_view(), name='2fa_disable'),
] 