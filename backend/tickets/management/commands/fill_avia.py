import random
from datetime import datetime, timedelta, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Airport, Booking, Fare, Flight, Ticket

AIRPORTS = [
    ('SGC', 'Сургут', 'Международный аэропорт Сургут', 5),
    ('SVO', 'Москва', 'Шереметьево', 3),
    ('LED', 'Санкт-Петербург', 'Пулково', 3),
    ('AER', 'Сочи', 'Международный аэропорт Сочи', 3),
    ('KZN', 'Казань', 'Международный аэропорт Казань', 3),
    ('SVX', 'Екатеринбург', 'Кольцово', 5),
]

FARES = [
    ('Лайт', 'economy', '1.00', 'Только ручная кладь до 10 кг', 0, 0, 1),
    ('Стандарт', 'economy', '1.35', 'Ручная кладь 10 кг и багаж 23 кг', 75, 25, 2),
    ('Бизнес', 'business', '2.80', 'Два места багажа по 32 кг', 100, 70, 3),
]

ROUTES = [
    ('ПЛ-101', 'SGC', 'SVO', '07:05', 215, 6900, 'Airbus A320', 25),
    ('ПЛ-103', 'SGC', 'SVO', '18:40', 215, 6300, 'Airbus A320', 25),
    ('ПЛ-102', 'SVO', 'SGC', '11:20', 195, 7100, 'Airbus A320', 25),
    ('ПЛ-211', 'SGC', 'LED', '09:30', 240, 7900, 'Boeing 737-800', 28),
    ('ПЛ-305', 'SGC', 'AER', '12:10', 300, 9900, 'Boeing 737-800', 28),
    ('ПЛ-407', 'SGC', 'KZN', '15:00', 150, 5600, 'Sukhoi Superjet 100', 16),
    ('ПЛ-509', 'SGC', 'SVX', '08:15', 75, 3900, 'Sukhoi Superjet 100', 16),
]

NAMES = [('ИВАНОВ', 'ПЁТР'), ('СМИРНОВА', 'АННА'), ('КУЗНЕЦОВ', 'ИЛЬЯ'), ('ПОПОВА', 'МАРИЯ'), ('СОКОЛОВ', 'ДЕНИС'), ('ЛЕБЕДЕВА', 'ОЛЬГА')]


class Command(BaseCommand):
    help = 'Заполняет базу аэропортами, тарифами и рейсами на две недели вперёд'

    def handle(self, *args, **options):
        random.seed(7)
        Ticket.objects.all().delete()
        Booking.objects.all().delete()
        Flight.objects.all().delete()
        Fare.objects.all().delete()
        Airport.objects.all().delete()

        airports = {}
        for code, city, name, offset in AIRPORTS:
            airports[code] = Airport.objects.create(code=code, city=city, name=name, utc_offset=offset)
        fares = []
        for name, cabin, coef, baggage, early, late, order in FARES:
            fares.append(Fare.objects.create(name=name, cabin=cabin, coefficient=coef, baggage=baggage,
                                             refund_early=early, refund_late=late, order=order))

        today = timezone.localdate()
        for day in range(0, 15):
            for number, origin, destination, at, minutes, price, aircraft, rows in ROUTES:
                tz = dt_timezone(timedelta(hours=airports[origin].utc_offset))
                hour, minute = map(int, at.split(':'))
                departure = datetime(today.year, today.month, today.day, hour, minute, tzinfo=tz) + timedelta(days=day)
                Flight.objects.create(number=number, origin=airports[origin], destination=airports[destination],
                                      departure=departure, arrival=departure + timedelta(minutes=minutes),
                                      aircraft=aircraft, rows=rows, base_price=price + random.choice([0, 300, 600, 900]))

        for flight in Flight.objects.filter(departure__date__lte=today + timedelta(days=4)):
            booking = Booking.objects.create(email='group@example.ru', phone='+7 900 000-00-00')
            seats = flight.all_seats('economy')
            for seat in random.sample(seats, len(seats) // 3) + random.sample(flight.all_seats('business'), 3):
                fare = fares[2] if seat[0] in '12' and len(seat) == 2 else random.choice(fares[:2])
                last, first = random.choice(NAMES)
                Ticket.objects.create(booking=booking, flight=flight, fare=fare, last_name=last, first_name=first,
                                      birth_date='1990-01-01', document='0000000000', seat=seat, price=flight.price_for(fare))
            booking.total = sum(t.price for t in booking.tickets.all())
            booking.save()

        self.stdout.write('Аэропортов: ' + str(Airport.objects.count()) + ', рейсов: ' + str(Flight.objects.count()) +
                          ', билетов: ' + str(Ticket.objects.count()))
