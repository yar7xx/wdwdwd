from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Airport, Booking, Fare, Flight, Ticket


class AviaTests(APITestCase):
    def setUp(self):
        self.sgc = Airport.objects.create(code='SGC', city='Сургут', name='Сургут', utc_offset=5)
        self.svo = Airport.objects.create(code='SVO', city='Москва', name='Шереметьево', utc_offset=3)
        self.light = Fare.objects.create(name='Лайт', cabin='economy', coefficient='1.00', baggage='10 кг', refund_early=0, refund_late=0, order=1)
        self.standard = Fare.objects.create(name='Стандарт', cabin='economy', coefficient='1.50', baggage='23 кг', refund_early=75, refund_late=25, order=2)
        self.business = Fare.objects.create(name='Бизнес', cabin='business', coefficient='3.00', baggage='2 × 32 кг', refund_early=100, refund_late=70, order=3)
        departure = timezone.now() + timedelta(days=3)
        self.flight = Flight.objects.create(number='ПЛ-101', origin=self.sgc, destination=self.svo, departure=departure,
                                            arrival=departure + timedelta(minutes=215), rows=10, base_price=6000)

    def passenger(self, seat='5A', **change):
        p = {'last_name': 'Подляскин', 'first_name': 'Ян', 'birth_date': '2006-05-01', 'document': '67 18 123456', 'seat': seat}
        p.update(change)
        return p

    def book(self, fare=None, passengers=None, **change):
        data = {'flight': self.flight.id, 'fare': (fare or self.standard).id, 'email': 'yan@example.ru', 'phone': '+7 912 111-22-33',
                'agree': True, 'passengers': passengers or [self.passenger()]}
        data.update(change)
        return self.client.post('/api/bookings/', data, format='json')

    def test_api_returns_json(self):
        response = self.client.get('/api/airports/')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(len(response.json()), 2)

    def test_search(self):
        day = timezone.localtime(self.flight.departure).date().isoformat()
        rows = self.client.get('/api/flights/search/', {'from': 'SGC', 'to': 'SVO', 'date': day, 'passengers': 1}).json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['fares'][1]['price'], 9000)
        self.assertEqual(rows[0]['fares'][2]['free_seats'], 8)

    def test_search_errors(self):
        self.assertEqual(self.client.get('/api/flights/search/', {'from': 'SGC', 'to': 'SGC', 'date': '2030-01-01'}).status_code, 400)
        self.assertEqual(self.client.get('/api/flights/search/', {'from': 'SGC', 'to': 'SVO', 'date': '2000-01-01'}).status_code, 400)

    def test_local_times(self):
        data = self.client.get('/api/flights/' + str(self.flight.id) + '/').json()
        dep = self.flight.departure.astimezone(timezone.get_fixed_timezone(300)).strftime('%H:%M')
        arr = (self.flight.arrival).astimezone(timezone.get_fixed_timezone(180)).strftime('%H:%M')
        self.assertEqual(data['departure_time'], dep)
        self.assertEqual(data['arrival_time'], arr)

    def test_booking_created(self):
        response = self.book(passengers=[self.passenger('5A'), self.passenger('5B', first_name='Анна')])
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(len(data['code']), 6)
        self.assertEqual(data['total'], 18000)
        self.assertEqual(data['tickets'][0]['last_name'], 'ПОДЛЯСКИН')

    def test_booking_errors(self):
        response = self.book(email='mail', phone='1', agree=False, passengers=[self.passenger(last_name='1', document='123', seat='99Z')])
        errors = response.json()['errors']
        self.assertEqual(response.status_code, 400)
        self.assertIn('Телефон должен содержать 10 или 11 цифр', errors)
        self.assertIn('Пассажир 1: серия и номер паспорта — 10 цифр', errors)
        self.assertIn('Пассажир 1: укажите фамилию буквами', errors)

    def test_seat_taken_and_duplicate(self):
        self.book()
        response = self.book(passengers=[self.passenger('5A')])
        self.assertIn('Пассажир 1: место 5A уже занято', response.json()['errors'])
        response = self.book(passengers=[self.passenger('6A'), self.passenger('6A')])
        self.assertIn('Пассажир 2: место 6A выбрано для другого пассажира', response.json()['errors'])

    def test_business_seat_only_in_business(self):
        response = self.book(fare=self.standard, passengers=[self.passenger('1A')])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.book(fare=self.business, passengers=[self.passenger('1A')]).status_code, 201)

    def test_lookup(self):
        code = self.book().json()['code']
        self.assertEqual(self.client.post('/api/bookings/lookup/', {'code': code.lower(), 'last_name': 'подляскин'}, format='json').status_code, 200)
        self.assertEqual(self.client.post('/api/bookings/lookup/', {'code': code, 'last_name': 'Иванов'}, format='json').status_code, 404)

    def test_refund_standard_early(self):
        data = self.book().json()
        ticket = data['tickets'][0]
        self.assertEqual(ticket['refund']['amount'], 6750)
        response = self.client.post('/api/tickets/' + str(ticket['id']) + '/refund/', {'code': data['code'], 'last_name': 'Подляскин'}, format='json')
        self.assertEqual(response.json()['refunded_total'], 6750)
        self.assertEqual(Ticket.objects.get(id=ticket['id']).status, 'refunded')

    def test_refund_late(self):
        data = self.book().json()
        self.flight.departure = timezone.now() + timedelta(hours=5)
        self.flight.save()
        ticket = Ticket.objects.get(id=data['tickets'][0]['id'])
        self.assertEqual(ticket.refund_quote()[0], 2250)

    def test_light_not_refundable(self):
        data = self.book(fare=self.light).json()
        response = self.client.post('/api/tickets/' + str(data['tickets'][0]['id']) + '/refund/', {'code': data['code'], 'last_name': 'Подляскин'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Тариф «Лайт» невозвратный', response.json()['errors'])

    def test_no_refund_after_departure(self):
        data = self.book().json()
        Flight.objects.filter(id=self.flight.id).update(departure=timezone.now() - timedelta(hours=1))
        ticket = Ticket.objects.get(id=data['tickets'][0]['id'])
        self.assertEqual(ticket.refund_quote(), (0, 'Рейс уже вылетел, вернуть билет нельзя'))

    def test_refund_twice(self):
        data = self.book().json()
        url = '/api/tickets/' + str(data['tickets'][0]['id']) + '/refund/'
        self.client.post(url, {'code': data['code'], 'last_name': 'Подляскин'}, format='json')
        response = self.client.post(url, {'code': data['code'], 'last_name': 'Подляскин'}, format='json')
        self.assertIn('Билет уже возвращён', response.json()['errors'])

    def test_refunded_seat_becomes_free(self):
        data = self.book().json()
        self.client.post('/api/tickets/' + str(data['tickets'][0]['id']) + '/refund/', {'code': data['code'], 'last_name': 'Подляскин'}, format='json')
        self.assertEqual(self.book().status_code, 201)

    def test_no_html_pages(self):
        response = self.client.get('/api/airports/', HTTP_ACCEPT='text/html')
        self.assertEqual(response['Content-Type'], 'application/json')
