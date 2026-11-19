from rest_framework import serializers

from .models import Airport, Booking, Fare, Flight, Ticket


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ['code', 'city', 'name', 'utc_offset']


class FareSerializer(serializers.ModelSerializer):
    cabin_display = serializers.CharField(source='get_cabin_display')

    class Meta:
        model = Fare
        fields = ['id', 'name', 'cabin', 'cabin_display', 'baggage', 'refund_early', 'refund_late']


class FlightSerializer(serializers.ModelSerializer):
    origin = AirportSerializer()
    destination = AirportSerializer()
    date = serializers.SerializerMethodField()
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()
    arrival_date = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    fares = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = ['id', 'number', 'origin', 'destination', 'date', 'departure_time', 'arrival_time', 'arrival_date', 'duration', 'aircraft', 'fares']

    def get_date(self, obj):
        return obj.local_departure().date().isoformat()

    def get_departure_time(self, obj):
        return obj.local_departure().strftime('%H:%M')

    def get_arrival_time(self, obj):
        return obj.local_arrival().strftime('%H:%M')

    def get_arrival_date(self, obj):
        return obj.local_arrival().date().isoformat()

    def get_duration(self, obj):
        minutes = int((obj.arrival - obj.departure).total_seconds() // 60)
        return str(minutes // 60) + ' ч ' + str(minutes % 60).zfill(2) + ' мин'

    def get_fares(self, obj):
        result = []
        for fare in Fare.objects.all():
            item = FareSerializer(fare).data
            item['price'] = obj.price_for(fare)
            item['free_seats'] = obj.free_count(fare.cabin)
            result.append(item)
        return result


class TicketSerializer(serializers.ModelSerializer):
    flight = FlightSerializer()
    fare_name = serializers.CharField(source='fare.name')
    status_display = serializers.CharField(source='get_status_display')
    refund = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'last_name', 'first_name', 'birth_date', 'seat', 'price', 'fare_name', 'status', 'status_display',
                  'refund_amount', 'refunded_at', 'refund', 'flight']

    def get_refund(self, obj):
        amount, reason = obj.refund_quote()
        return {'amount': amount, 'reason': reason, 'possible': amount > 0}


class BookingSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)
    refunded_total = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['code', 'email', 'total', 'refunded_total', 'created_at', 'tickets']

    def get_refunded_total(self, obj):
        return obj.refunded_total()
