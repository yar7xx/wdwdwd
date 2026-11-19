import re
from datetime import date, datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Airport, Booking, Fare, Flight, Ticket
from .serializers import AirportSerializer, BookingSerializer, FareSerializer, FlightSerializer

MAX_PASSENGERS = 5
NAME_RE = re.compile(r'^[А-Яа-яЁёA-Za-z\- ]{2,60}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$')


def digits(text):
    return re.sub(r'\D', '', str(text))


def error(text, code=status.HTTP_400_BAD_REQUEST):
    return Response({'errors': [text]}, status=code)


@api_view(['GET'])
def airports(request):
    return Response(AirportSerializer(Airport.objects.all(), many=True).data)


@api_view(['GET'])
def fares(request):
    return Response(FareSerializer(Fare.objects.all(), many=True).data)


@api_view(['GET'])
def search(request):
    origin = request.GET.get('from', '').upper()
    destination = request.GET.get('to', '').upper()
    try:
        day = datetime.strptime(request.GET.get('date', ''), '%Y-%m-%d').date()
        passengers = int(request.GET.get('passengers', 1))
    except ValueError:
        return error('Проверьте дату и количество пассажиров')
    if origin == destination:
        return error('Город вылета и прилёта совпадают')
    if day < date.today():
        return error('Эта дата уже прошла')

    flights = Flight.objects.filter(origin__code=origin, destination__code=destination, departure__date=day,
                                    departure__gt=timezone.now()).select_related('origin', 'destination')
    result = []
    for flight in flights:
        data = FlightSerializer(flight).data
        data['fares'] = [f for f in data['fares'] if f['free_seats'] >= passengers]
        if data['fares']:
            result.append(data)
    return Response(result)


@api_view(['GET'])
def flight_detail(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    data = FlightSerializer(flight).data
    data['rows'] = flight.rows
    data['taken'] = sorted(flight.taken_seats())
    data['departed'] = flight.departure <= timezone.now()
    return Response(data)


def check_passenger(number, p, fare, flight, used_seats):
    problems = []
    prefix = 'Пассажир ' + str(number) + ': '
    last_name = str(p.get('last_name', '')).strip()
    first_name = str(p.get('first_name', '')).strip()
    if not NAME_RE.match(last_name):
        problems.append(prefix + 'укажите фамилию буквами')
    if not NAME_RE.match(first_name):
        problems.append(prefix + 'укажите имя буквами')
    try:
        birth = datetime.strptime(str(p.get('birth_date', '')), '%Y-%m-%d').date()
        if birth > date.today():
            problems.append(prefix + 'дата рождения в будущем')
    except ValueError:
        problems.append(prefix + 'укажите дату рождения')
    if len(digits(p.get('document', ''))) != 10:
        problems.append(prefix + 'серия и номер паспорта — 10 цифр')
    seat = str(p.get('seat', '')).upper()
    if seat not in flight.all_seats(fare.cabin):
        problems.append(prefix + 'выберите место в салоне класса «' + fare.get_cabin_display() + '»')
    elif seat in flight.taken_seats():
        problems.append(prefix + 'место ' + seat + ' уже занято')
    elif seat in used_seats:
        problems.append(prefix + 'место ' + seat + ' выбрано для другого пассажира')
    used_seats.append(seat)
    return problems


@api_view(['POST'])
def create_booking(request):
    flight = Flight.objects.filter(id=request.data.get('flight')).first()
    fare = Fare.objects.filter(id=request.data.get('fare')).first()
    if flight is None or fare is None:
        return error('Рейс или тариф не найдены', status.HTTP_404_NOT_FOUND)
    if flight.departure <= timezone.now():
        return error('Продажа билетов на этот рейс закрыта')

    email = str(request.data.get('email', '')).strip()
    phone = str(request.data.get('phone', '')).strip()
    passengers = request.data.get('passengers', [])

    errors = []
    if not EMAIL_RE.match(email):
        errors.append('Укажите e-mail, на него придёт маршрутная квитанция')
    if len(digits(phone)) not in (10, 11):
        errors.append('Телефон должен содержать 10 или 11 цифр')
    if request.data.get('agree') is not True:
        errors.append('Нужно согласиться с правилами тарифа и обработкой данных')
    if not isinstance(passengers, list) or not 1 <= len(passengers) <= MAX_PASSENGERS:
        errors.append('В одном заказе можно оформить от 1 до ' + str(MAX_PASSENGERS) + ' билетов')
        passengers = []

    used_seats = []
    for number, p in enumerate(passengers, start=1):
        errors += check_passenger(number, p if isinstance(p, dict) else {}, fare, flight, used_seats)

    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    price = flight.price_for(fare)
    with transaction.atomic():
        booking = Booking.objects.create(email=email, phone=phone, total=price * len(passengers))
        for p in passengers:
            Ticket.objects.create(
                booking=booking, flight=flight, fare=fare,
                last_name=p['last_name'].strip().upper(), first_name=p['first_name'].strip().upper(),
                birth_date=p['birth_date'], document=digits(p['document']), seat=p['seat'].upper(), price=price,
            )
    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


def find_booking(data):
    code = str(data.get('code', '')).strip().upper()
    last_name = str(data.get('last_name', '')).strip().upper()
    booking = Booking.objects.filter(code=code).first()
    if booking is None or not booking.tickets.filter(last_name=last_name).exists():
        return None
    return booking


@api_view(['POST'])
def booking_lookup(request):
    booking = find_booking(request.data)
    if booking is None:
        return error('Бронирование с таким кодом и фамилией не найдено', status.HTTP_404_NOT_FOUND)
    return Response(BookingSerializer(booking).data)


@api_view(['POST'])
def refund_ticket(request, pk):
    booking = find_booking(request.data)
    if booking is None:
        return error('Бронирование с таким кодом и фамилией не найдено', status.HTTP_404_NOT_FOUND)
    ticket = booking.tickets.filter(id=pk).first()
    if ticket is None:
        return error('Билет не найден в этом бронировании', status.HTTP_404_NOT_FOUND)

    amount, reason = ticket.refund_quote()
    if amount == 0:
        return error(reason)

    ticket.status = 'refunded'
    ticket.refund_amount = amount
    ticket.refunded_at = timezone.now()
    ticket.save()
    data = BookingSerializer(booking).data
    data['message'] = 'Билет ' + ticket.last_name + ' ' + ticket.first_name + ' возвращён, к возврату ' + str(amount) + ' руб.'
    return Response(data)
