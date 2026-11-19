var flight = null;
var fare = null;
var count = Number(getParam('passengers') || 1);
var seats = [];
var active = 0;

function passengerForm(i) {
    return '<div class="passenger' + (i === active ? ' active' : '') + '" data-index="' + i + '">' +
        '<div style="display:flex;justify-content:space-between"><b>Пассажир ' + (i + 1) + '</b><span class="seat-label" id="seat-' + i + '">' + (seats[i] ? 'место ' + seats[i] : 'место не выбрано') + '</span></div>' +
        '<div class="grid">' +
        '<div class="field"><label>Фамилия</label><input type="text" id="last-' + i + '" placeholder="Иванов"></div>' +
        '<div class="field"><label>Имя</label><input type="text" id="first-' + i + '" placeholder="Иван"></div>' +
        '<div class="field"><label>Дата рождения</label><input type="date" id="birth-' + i + '"></div>' +
        '<div class="field"><label>Паспорт: серия и номер</label><input type="text" id="doc-' + i + '" placeholder="67 18 123456"></div>' +
        '</div></div>';
}

function drawPassengers() {
    var html = '';
    for (var i = 0; i < count; i++) {
        html += passengerForm(i);
    }
    document.getElementById('passengers').innerHTML = html;
    var cards = document.querySelectorAll('.passenger[data-index]');
    for (var j = 0; j < cards.length; j++) {
        cards[j].onclick = function () {
            active = Number(this.dataset.index);
            refreshActive();
        };
    }
}

function refreshActive() {
    var cards = document.querySelectorAll('.passenger[data-index]');
    for (var i = 0; i < cards.length; i++) {
        cards[i].classList.toggle('active', i === active);
        document.getElementById('seat-' + i).textContent = seats[i] ? 'место ' + seats[i] : 'место не выбрано';
    }
}

function seatButton(row, letter, cabin) {
    var code = row + letter;
    var cls = 'seat' + (cabin === 'business' ? ' business' : '');
    var disabled = '';
    if (flight.taken.indexOf(code) !== -1) {
        cls += ' taken';
        disabled = ' disabled';
    } else if (cabin !== fare.cabin) {
        cls += ' blocked';
        disabled = ' disabled';
    }
    if (seats.indexOf(code) !== -1) {
        cls += ' mine';
    }
    return '<button class="' + cls + '" data-seat="' + code + '"' + disabled + ' title="Место ' + code + '">' + code + '</button>';
}

function drawSeatmap() {
    var html = '';
    for (var row = 1; row <= flight.rows; row++) {
        var business = row <= 2;
        var letters = business ? ['A', 'C', '', 'D', 'F'] : ['A', 'B', 'C', '', 'D', 'E', 'F'];
        html += '<div class="seat-row"><span class="num">' + row + '</span>';
        for (var i = 0; i < letters.length; i++) {
            if (letters[i] === '') {
                html += '<span class="num"></span>';
            } else {
                html += seatButton(row, letters[i], business ? 'business' : 'economy');
            }
        }
        html += '<span class="num">' + row + '</span></div>';
    }
    var map = document.getElementById('seatmap');
    map.innerHTML = html;
    var buttons = map.querySelectorAll('.seat:not([disabled])');
    for (var j = 0; j < buttons.length; j++) {
        buttons[j].onclick = function () {
            var code = this.dataset.seat;
            var other = seats.indexOf(code);
            if (other !== -1) {
                seats[other] = null;
            }
            seats[active] = code;
            for (var k = 0; k < count; k++) {
                if (!seats[k]) {
                    active = k;
                    break;
                }
            }
            drawSeatmap();
            refreshActive();
            drawSummary();
        };
    }
}

function drawSummary() {
    var html = '<div class="summary-row"><span>Рейс</span><b>' + esc(flight.number) + ', ' + niceDate(flight.date) + '</b></div>' +
        '<div class="summary-row"><span>Маршрут</span><b>' + flight.origin.code + ' ' + flight.departure_time + ' → ' + flight.destination.code + ' ' + flight.arrival_time + '</b></div>' +
        '<div class="summary-row"><span>Тариф</span><b>' + esc(fare.name) + '</b></div>' +
        '<div class="summary-row"><span>Багаж</span><b>' + esc(fare.baggage) + '</b></div>' +
        '<div class="summary-row"><span>Билеты</span><b>' + count + ' × ' + rub(fare.price) + '</b></div>' +
        '<div class="summary-row"><span>Места</span><b>' + (seats.filter(Boolean).join(', ') || '—') + '</b></div>';
    document.getElementById('summary').innerHTML = html;
    document.getElementById('total').textContent = rub(fare.price * count);
}

function buy() {
    var passengers = [];
    for (var i = 0; i < count; i++) {
        passengers.push({
            last_name: document.getElementById('last-' + i).value.trim(),
            first_name: document.getElementById('first-' + i).value.trim(),
            birth_date: document.getElementById('birth-' + i).value,
            document: document.getElementById('doc-' + i).value.trim(),
            seat: seats[i] || '',
        });
    }
    postJson('bookings/', {
        flight: flight.id,
        fare: fare.id,
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        agree: document.getElementById('agree').checked,
        passengers: passengers,
    })
        .then(function (result) {
            if (!result.ok) {
                showErrors(document.getElementById('errors'), result.data.errors);
                return;
            }
            var b = result.data;
            var rows = '';
            for (var j = 0; j < b.tickets.length; j++) {
                rows += '<div class="summary-row" style="border-color:var(--line)"><span>' + esc(b.tickets[j].last_name) + ' ' + esc(b.tickets[j].first_name) + '</span><b>место ' + b.tickets[j].seat + '</b></div>';
            }
            document.getElementById('form').style.display = 'none';
            document.getElementById('result').innerHTML =
                '<div class="box" style="max-width:640px;margin:30px auto 70px;text-align:center">' +
                '<h2>Билеты оформлены!</h2><p>Код бронирования — по нему можно посмотреть и вернуть билеты:</p>' +
                '<div class="pnr">' + b.code + '</div>' +
                '<div style="text-align:left">' + rows + '<div class="summary-row" style="border-color:var(--line)"><span>Оплачено</span><b>' + rub(b.total) + '</b></div></div>' +
                '<p style="color:var(--muted)">Маршрутная квитанция отправлена на ' + esc(b.email) + '</p>' +
                '<a class="btn blue" href="manage.html?code=' + b.code + '">Мои билеты</a></div>';
            window.scrollTo(0, 0);
        })
        .catch(function () {
            toast('Сервер не отвечает', 'error');
        });
}

getJson('flights/' + getParam('flight') + '/')
    .then(function (result) {
        if (!result.ok) {
            document.getElementById('form').innerHTML = '<div class="empty" style="grid-column:1/-1">Рейс не найден</div>';
            return;
        }
        flight = result.data;
        for (var i = 0; i < flight.fares.length; i++) {
            if (String(flight.fares[i].id) === getParam('fare')) {
                fare = flight.fares[i];
            }
        }
        if (!fare) {
            fare = flight.fares[0];
        }
        document.getElementById('subtitle').textContent = flight.origin.city + ' → ' + flight.destination.city + ' · ' + niceDate(flight.date) + ' · тариф «' + fare.name + '»';
        drawPassengers();
        drawSeatmap();
        drawSummary();
    })
    .catch(function () {
        serverDown(document.getElementById('form'));
    });
