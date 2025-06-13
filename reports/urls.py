from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='list'),
    path('create/', views.ReportCreateView.as_view(), name='create'),
    path('detail/<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('daily/', views.DailyReportView.as_view(), name='daily'),
    path('weekly/', views.WeeklyReportView.as_view(), name='weekly'),
    path('monthly/', views.MonthlyReportView.as_view(), name='monthly'),
    path('custom/', views.CustomReportView.as_view(), name='custom'),
    path('export/<int:pk>/', views.ExportReportView.as_view(), name='export'),
    path('parking-stats/', views.ParkingStatsReportView.as_view(), name='parking_stats'),
    path('parking-stats/excel/', views.ExportParkingStatsExcelView.as_view(), name='parking_stats_excel'),
    path('parking-stats/pdf/', views.ExportParkingStatsPDFView.as_view(), name='parking_stats_pdf'),
] 