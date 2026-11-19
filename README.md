# Авиабилеты «Полёт»

Курсовая работа: «Проектирование и разработка веб-приложения авиабилетов: покупка и возврат билетов».

Автор: Подляскин Ян Игоревич, группа ИС-23/9-3.

Проект разделён на два отдельных сервера:

- `backend` — Django + Django REST Framework, работает с базой данных и отдаёт только JSON (API);
- `frontend` — HTML, CSS и JavaScript, получает данные с бэкенда через API.

## Запуск бэкенда (порт 8000)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
python manage.py migrate
python manage.py fill_avia
python manage.py createsuperuser
python manage.py runserver 8000
```

Команда `fill_avia` создаёт рейсы на две недели вперёд от текущей даты. Если рейсы закончились, запустите её ещё раз.

## Запуск фронтенда (порт 5500)

Во втором окне терминала:

```
cd frontend
python -m http.server 5500
```

Сайт: http://127.0.0.1:5500, API: http://127.0.0.1:8000/api/, панель администратора: http://127.0.0.1:8000/admin/

## Тесты

```
cd backend
python manage.py test tickets
```
