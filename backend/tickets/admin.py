from django.contrib import admin

from .models import Airport, Booking, Fare, Flight, Ticket


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['code', 'city', 'name']


@admin.register(Fare)
class FareAdmin(admin.ModelAdmin):
    list_display = ['name', 'cabin', 'coefficient', 'baggage', 'refund_early', 'refund_late']
    list_editable = ['coefficient', 'refund_early', 'refund_late']


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ['number', 'origin', 'destination', 'departure', 'arrival', 'base_price']
    list_filter = ['origin', 'destination']
    date_hierarchy = 'departure'


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    fields = ['last_name', 'first_name', 'flight', 'fare', 'seat', 'price', 'status', 'refund_amount']
    readonly_fields = ['price', 'refund_amount']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['code', 'email', 'phone', 'total', 'created_at']
    search_fields = ['code', 'email', 'tickets__last_name']
    inlines = [TicketInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'flight', 'fare', 'seat', 'price', 'status', 'refund_amount']
    list_filter = ['status', 'fare']
    search_fields = ['last_name', 'booking__code']
