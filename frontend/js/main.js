var API = 'http://127.0.0.1:8000/api/';
var MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
var WEEKDAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

function esc(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

function rub(value) {
    return Number(value).toLocaleString('ru-RU') + ' ₽';
}

function niceDate(text) {
    var parts = text.split('-');
    var d = new Date(text + 'T12:00:00');
    return Number(parts[2]) + ' ' + MONTHS[Number(parts[1]) - 1] + ', ' + WEEKDAYS[d.getDay()];
}

function isoDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}

function getJson(path) {
    return fetch(API + path).then(function (response) {
        return response.json().then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
        });
    });
}

function postJson(path, body) {
    return fetch(API + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    }).then(function (response) {
        return response.json().then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
        });
    });
}

function toast(text, type) {
    var div = document.createElement('div');
    div.className = 'toast ' + (type || '');
    div.textContent = text;
    document.body.appendChild(div);
    setTimeout(function () {
        div.remove();
    }, 4000);
}

function showErrors(place, list) {
    var html = '';
    for (var i = 0; i < list.length; i++) {
        html += '<p>• ' + esc(list[i]) + '</p>';
    }
    place.innerHTML = '<div class="errors">' + html + '</div>';
}

function serverDown(place) {
    place.innerHTML = '<div class="empty"><h3>Сервер не отвечает</h3><p>Проверьте, что бэкенд запущен на порту 8000.</p></div>';
}

function routeBlock(f) {
    var nextDay = f.arrival_date !== f.date ? '<small> +1 день</small>' : '';
    return '<div class="route">' +
        '<div class="time"><b>' + f.departure_time + '</b><small>' + esc(f.origin.city) + ', ' + f.origin.code + '</small></div>' +
        '<div class="line">' + f.duration + '<i></i>' + esc(f.number) + '</div>' +
        '<div class="time" style="text-align:right"><b>' + f.arrival_time + '</b>' + nextDay + '<small>' + esc(f.destination.city) + ', ' + f.destination.code + '</small></div>' +
        '<div class="flight-info">' + niceDate(f.date) + ' · ' + esc(f.aircraft) + ' · время местное</div>' +
        '</div>';
}

function toggleMenu() {
    document.getElementById('menu').classList.toggle('open');
}
