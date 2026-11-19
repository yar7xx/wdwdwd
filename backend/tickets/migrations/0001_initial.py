import django.db.models.deletion
import tickets.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Airport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, unique=True, verbose_name='Код IATA')),
                ('city', models.CharField(max_length=60, verbose_name='Город')),
                ('name', models.CharField(max_length=100, verbose_name='Аэропорт')),
                ('utc_offset', models.IntegerField(default=3, verbose_name='Часовой пояс, UTC+')),
            ],
            options={
                'verbose_name': 'Аэропорт',
                'verbose_name_plural': 'Аэропорты',
                'ordering': ['city'],
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=tickets.models.make_pnr, editable=False, max_length=6, unique=True, verbose_name='Код бронирования')),
                ('email', models.EmailField(max_length=254, verbose_name='E-mail')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('total', models.PositiveIntegerField(default=0, verbose_name='Сумма покупки, руб')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Оформлено')),
            ],
            options={
                'verbose_name': 'Бронирование',
                'verbose_name_plural': 'Бронирования',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Fare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='Тариф')),
                ('cabin', models.CharField(choices=[('economy', 'Эконом'), ('business', 'Бизнес')], default='economy', max_length=10, verbose_name='Класс')),
                ('coefficient', models.DecimalField(decimal_places=2, default=1, max_digits=4, verbose_name='Коэффициент к цене')),
                ('baggage', models.CharField(max_length=80, verbose_name='Багаж')),
                ('refund_early', models.PositiveIntegerField(default=0, verbose_name='Возврат раньше чем за 24 ч, %')),
                ('refund_late', models.PositiveIntegerField(default=0, verbose_name='Возврат позже чем за 24 ч, %')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={
                'verbose_name': 'Тариф',
                'verbose_name_plural': 'Тарифы',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Flight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=10, verbose_name='Номер рейса')),
                ('departure', models.DateTimeField(verbose_name='Вылет')),
                ('arrival', models.DateTimeField(verbose_name='Прилёт')),
                ('aircraft', models.CharField(default='Airbus A320', max_length=40, verbose_name='Самолёт')),
                ('rows', models.PositiveIntegerField(default=20, verbose_name='Рядов в салоне')),
                ('base_price', models.PositiveIntegerField(verbose_name='Базовая цена, руб')),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='arrivals', to='tickets.airport', verbose_name='Куда')),
                ('origin', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='departures', to='tickets.airport', verbose_name='Откуда')),
            ],
            options={
                'verbose_name': 'Рейс',
                'verbose_name_plural': 'Рейсы',
                'ordering': ['departure'],
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_name', models.CharField(max_length=60, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=60, verbose_name='Имя')),
                ('birth_date', models.DateField(verbose_name='Дата рождения')),
                ('document', models.CharField(max_length=20, verbose_name='Паспорт')),
                ('seat', models.CharField(max_length=4, verbose_name='Место')),
                ('price', models.PositiveIntegerField(verbose_name='Цена, руб')),
                ('status', models.CharField(choices=[('active', 'Действует'), ('refunded', 'Возвращён')], default='active', max_length=10, verbose_name='Статус')),
                ('refund_amount', models.PositiveIntegerField(default=0, verbose_name='Возвращено, руб')),
                ('refunded_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата возврата')),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='tickets.booking', verbose_name='Бронирование')),
                ('fare', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tickets.fare', verbose_name='Тариф')),
                ('flight', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='tickets.flight', verbose_name='Рейс')),
            ],
            options={
                'verbose_name': 'Билет',
                'verbose_name_plural': 'Билеты',
            },
        ),
    ]
