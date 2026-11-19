from django.contrib import admin
from django.urls import path

from tickets import views

admin.site.site_header = 'Авиакасса «Полёт»'
admin.site.site_title = 'Полёт'
admin.site.index_title = 'Рейсы и билеты'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/airports/', views.airports),
    path('api/fares/', views.fares),
    path('api/flights/search/', views.search),
    path('api/flights/<int:pk>/', views.flight_detail),
    path('api/bookings/', views.create_booking),
    path('api/bookings/lookup/', views.booking_lookup),
    path('api/tickets/<int:pk>/refund/', views.refund_ticket),
]
