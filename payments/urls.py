from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create/', views.PaymentCreateView.as_view(), name='create'),
    path('list/', views.PaymentListView.as_view(), name='list'),
    path('detail/<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
] 