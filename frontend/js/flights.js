var search = {
    from: getParam('from') || 'SGC',
    to: getParam('to') || 'SVO',
    date: getParam('date'),
    passengers: getParam('passengers') || '1',
};

function fareButton(flight, fare) {
    return '<div class="fare-option">' +
        '<b>' + esc(fare.name) + '</b>' +
        '<span class="price">' + rub(fare.price) + '</span>' +
        '<small>' + esc(fare.baggage) + '<br>' + (fare.refund_early ? 'возврат до ' + fare.refund_early + '%' : 'невозвратный') + ' · мест: ' + fare.free_seats + '</small>' +
        '<a class="btn small" href="booking.html?flight=' + flight.id + '&fare=' + fare.id + '&passengers=' + search.passengers + '">Выбрать</a>' +
        '</div>';
}

getJson('flights/search/?from=' + search.from + '&to=' + search.to + '&date=' + search.date + '&passengers=' + search.passengers)
    .then(function (result) {
        var place = document.getElementById('flights');
        if (!result.ok) {
            place.innerHTML = '<div class="empty">' + esc(result.data.errors[0]) + '</div>';
            return;
        }
        if (result.data.length === 0) {
            place.innerHTML = '<div class="empty"><h3>На эту дату рейсов нет</h3><p>Попробуйте выбрать другой день.</p><a href="index.html" class="btn small blue">Изменить поиск</a></div>';
            return;
        }
        var first = result.data[0];
        document.getElementById('title').textContent = first.origin.city + ' → ' + first.destination.city;
        document.getElementById('subtitle').textContent = niceDate(search.date) + ' · пассажиров: ' + search.passengers + ' · найдено рейсов: ' + result.data.length;
        var html = '';
        for (var i = 0; i < result.data.length; i++) {
            var f = result.data[i];
            var fares = '';
            for (var j = 0; j < f.fares.length; j++) {
                fares += fareButton(f, f.fares[j]);
            }
            html += '<div class="flight">' + routeBlock(f) + '<div class="fare-options">' + fares + '</div></div>';
        }
        place.innerHTML = html;
    })
    .catch(function () {
        serverDown(document.getElementById('flights'));
    });
