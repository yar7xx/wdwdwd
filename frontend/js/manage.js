var lastQuery = null;

function ticketCard(t) {
    var refunded = t.status === 'refunded';
    var side = '';
    if (refunded) {
        side = '<span class="status refunded">Возвращён</span><b>Возвращено ' + rub(t.refund_amount) + '</b>' +
            '<small style="color:var(--muted)">Деньги вернутся на карту в течение 7 дней</small>';
    } else if (t.refund.possible) {
        side = '<span class="status">Действует</span><small style="color:var(--muted)">' + esc(t.refund.reason) + '</small>' +
            '<b>К возврату: ' + rub(t.refund.amount) + '</b>' +
            '<button class="btn small ghost" onclick="refund(' + t.id + ', ' + t.refund.amount + ')">Оформить возврат</button>';
    } else {
        side = '<span class="status">Действует</span><small style="color:var(--muted)">' + esc(t.refund.reason) + '</small>' +
            '<button class="btn small ghost" disabled>Возврат недоступен</button>';
    }
    return '<div class="ticket' + (refunded ? ' refunded' : '') + '"><div class="ticket-main">' +
        '<div style="display:flex;justify-content:space-between;gap:10px"><h3>' + esc(t.last_name) + ' ' + esc(t.first_name) + '</h3><b>Место ' + t.seat + '</b></div>' +
        '<div class="route" style="padding:10px 0;border:none">' +
        '<div class="time"><b>' + t.flight.departure_time + '</b><small>' + esc(t.flight.origin.city) + '</small></div>' +
        '<div class="line">' + t.flight.duration + '<i></i>' + esc(t.flight.number) + '</div>' +
        '<div class="time" style="text-align:right"><b>' + t.flight.arrival_time + '</b><small>' + esc(t.flight.destination.city) + '</small></div></div>' +
        '<small style="color:var(--muted)">' + niceDate(t.flight.date) + ' · тариф «' + esc(t.fare_name) + '» · ' + rub(t.price) + '</small></div>' +
        '<div class="ticket-side">' + side + '</div></div>';
}

function drawBooking(b) {
    var html = '<div class="box"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px"><div><small style="color:var(--muted)">Код бронирования</small><h2>' + b.code + '</h2></div>' +
        '<div style="text-align:right"><small style="color:var(--muted)">Оплачено / возвращено</small><h3>' + rub(b.total) + ' / ' + rub(b.refunded_total) + '</h3></div></div></div>';
    for (var i = 0; i < b.tickets.length; i++) {
        html += ticketCard(b.tickets[i]);
    }
    document.getElementById('booking').innerHTML = html;
}

function findBooking() {
    lastQuery = {
        code: document.getElementById('code').value.trim(),
        last_name: document.getElementById('last_name').value.trim(),
    };
    postJson('bookings/lookup/', lastQuery)
        .then(function (result) {
            if (!result.ok) {
                document.getElementById('booking').innerHTML = '<div class="empty">' + esc(result.data.errors[0]) + '</div>';
                return;
            }
            drawBooking(result.data);
        })
        .catch(function () {
            serverDown(document.getElementById('booking'));
        });
}

function refund(id, amount) {
    if (!confirm('Вернуть билет? К возврату ' + rub(amount) + '. Отменить возврат будет нельзя.')) {
        return;
    }
    postJson('tickets/' + id + '/refund/', lastQuery)
        .then(function (result) {
            if (!result.ok) {
                toast(result.data.errors[0], 'error');
                return;
            }
            toast(result.data.message);
            drawBooking(result.data);
        });
}

if (getParam('code')) {
    document.getElementById('code').value = getParam('code');
}
