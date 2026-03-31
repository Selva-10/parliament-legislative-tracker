from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/<uuid:pk>/', views.bill_detail, name='bill_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('map/', views.map_view, name='map'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/bills/', views.api_bills, name='api_bills'),
    # download
    path('download/', views.download_page, name='download_page'),
    path('download/download/', views.download_bills, name='download_bills'),
    #mp's mla's
    path('mps/', views.mp_list, name='mp_list'),
    path('mps/<int:pk>/', views.mp_detail, name='mp_detail'),
    path('mlas/', views.mla_list, name='mla_list'),
    path('mlas/<int:pk>/', views.mla_detail, name='mla_detail'),
]
