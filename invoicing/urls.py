from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.InvoiceListView.as_view(), name='invoice_list'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('generate/', views.GenerateInvoiceView.as_view(), name='generate_invoice'),
    path('<int:pk>/update-status/', views.UpdateInvoiceStatusView.as_view(), name='update_invoice_status'),
    path('<int:invoice_id>/download-txt/', views.download_invoice_txt, name='download_invoice_txt'),
    path('<int:invoice_id>/send-email/', views.send_invoice_email, name='send_invoice_email'),
] 