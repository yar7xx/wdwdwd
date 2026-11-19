import random
from decimal import Decimal
from datetime import timedelta
from datetime import timezone as dt_timezone

from django.db import models
from django.utils import timezone

BUSINESS_ROWS = 2
BUSINESS_LETTERS = 'ACDF'
ECONOMY_LETTERS = 'ABCDEF'


def make_pnr():
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code = ''.join(random.choice(letters) for _ in range(6))
        if not Booking.objects.filter(code=code).exists():
            return code


class Airport(models.Model):
    code = models.CharField('Код IATA', max_length=3, unique=True)
    city = models.CharField('Город', max_length=60)
    name = models.CharField('Аэропорт', max_length=100)
    utc_offset = models.IntegerField('Часовой пояс, UTC+', default=3)

    class Meta:
        verbose_name = 'Аэропорт'
        verbose_name_plural = 'Аэропорты'
        ordering = ['city']

    def __str__(self):
        return self.city + ' (' + self.code + ')'


class Fare(models.Model):
    CABINS = [('economy', 'Эконом'), ('business', 'Бизнес')]

    name = models.CharField('Тариф', max_length=40)
    cabin = models.CharField('Класс', max_length=10, choices=CABINS, default='economy')
    coefficient = models.DecimalField('Коэффициент к цене', max_digits=4, decimal_places=2, default=1)
    baggage = models.CharField('Багаж', max_length=80)
    refund_early = models.PositiveIntegerField('Возврат раньше чем за 24 ч, %', default=0)
    refund_late = models.PositiveIntegerField('Возврат позже чем за 24 ч, %', default=0)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
        ordering = ['order']

    def __str__(self):
        return self.name


class Flight(models.Model):
    number = models.CharField('Номер рейса', max_length=10)
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='departures', verbose_name='Откуда')
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='arrivals', verbose_name='Куда')
    departure = models.DateTimeField('Вылет')
    arrival = models.DateTimeField('Прилёт')
    aircraft = models.CharField('Самолёт', max_length=40, default='Airbus A320')
    rows = models.PositiveIntegerField('Рядов в салоне', default=20)
    base_price = models.PositiveIntegerField('Базовая цена, руб')

    class Meta:
        verbose_name = 'Рейс'
        verbose_name_plural = 'Рейсы'
        ordering = ['departure']

    def __str__(self):
        return self.number + ' ' + self.origin.code + '–' + self.destination.code + ' ' + self.local_departure().strftime('%d.%m %H:%M')

    def local_departure(self):
        return self.departure.astimezone(dt_timezone(timedelta(hours=self.origin.utc_offset)))

    def local_arrival(self):
        return self.arrival.astimezone(dt_timezone(timedelta(hours=self.destination.utc_offset)))

    def all_seats(self, cabin):
        seats = []
        if cabin == 'business':
            for row in range(1, BUSINESS_ROWS + 1):
                for letter in BUSINESS_LETTERS:
                    seats.append(str(row) + letter)
        else:
            for row in range(BUSINESS_ROWS + 1, self.rows + 1):
                for letter in ECONOMY_LETTERS:
                    seats.append(str(row) + letter)
        return seats

    def taken_seats(self):
        return set(Ticket.objects.filter(flight=self, status='active').values_list('seat', flat=True))

    def free_count(self, cabin):
        taken = self.taken_seats()
        return len([s for s in self.all_seats(cabin) if s not in taken])

    def price_for(self, fare):
        return int(round(self.base_price * Decimal(str(fare.coefficient)), -1))


class Booking(models.Model):
    code = models.CharField('Код бронирования', max_length=6, unique=True, default=make_pnr, editable=False)
    email = models.EmailField('E-mail')
    phone = models.CharField('Телефон', max_length=20)
    total = models.PositiveIntegerField('Сумма покупки, руб', default=0)
    created_at = models.DateTimeField('Оформлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def refunded_total(self):
        return sum(t.refund_amount for t in self.tickets.all())


class Ticket(models.Model):
    STATUSES = [('active', 'Действует'), ('refunded', 'Возвращён')]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets', verbose_name='Бронирование')
    flight = models.ForeignKey(Flight, on_delete=models.PROTECT, related_name='tickets', verbose_name='Рейс')
    fare = models.ForeignKey(Fare, on_delete=models.PROTECT, verbose_name='Тариф')
    last_name = models.CharField('Фамилия', max_length=60)
    first_name = models.CharField('Имя', max_length=60)
    birth_date = models.DateField('Дата рождения')
    document = models.CharField('Паспорт', max_length=20)
    seat = models.CharField('Место', max_length=4)
    price = models.PositiveIntegerField('Цена, руб')
    status = models.CharField('Статус', max_length=10, choices=STATUSES, default='active')
    refund_amount = models.PositiveIntegerField('Возвращено, руб', default=0)
    refunded_at = models.DateTimeField('Дата возврата', null=True, blank=True)

    class Meta:
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

    def __str__(self):
        return self.last_name + ' ' + self.first_name + ', ' + self.flight.number + ', место ' + self.seat

    def refund_quote(self, now=None):
        now = now or timezone.now()
        if self.status != 'active':
            return 0, 'Билет уже возвращён'
        hours = (self.flight.departure - now).total_seconds() / 3600
        if hours <= 0:
            return 0, 'Рейс уже вылетел, вернуть билет нельзя'
        percent = self.fare.refund_early if hours >= 24 else self.fare.refund_late
        if percent == 0:
            return 0, 'Тариф «' + self.fare.name + '» невозвратный'
        when = 'больше чем за 24 часа' if hours >= 24 else 'меньше чем за 24 часа'
        return self.price * percent // 100, 'Возврат ' + str(percent) + '% стоимости: до вылета ' + when
