var COLORS = ['#2f6fed', '#ff6b4a', '#12a150', '#7c4ddb', '#0b1f4d'];

getJson('airports/')
    .then(function (result) {
        fillSearchForm(result.data, {});
        var tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        var html = '';
        var n = 0;
        for (var i = 0; i < result.data.length; i++) {
            var a = result.data[i];
            if (a.code === 'SGC') continue;
            html += '<a class="city" style="--c:' + COLORS[n % COLORS.length] + '" href="flights.html?from=SGC&to=' + a.code + '&date=' + isoDate(tomorrow) + '&passengers=1">' +
                '<small>Сургут →</small><div><h3>' + esc(a.city) + '</h3><small>' + esc(a.name) + '</small></div></a>';
            n++;
        }
        document.getElementById('cities').innerHTML = html;
    })
    .catch(function () {
        serverDown(document.getElementById('cities'));
    });

getJson('fares/')
    .then(function (result) {
        var html = '';
        for (var i = 0; i < result.data.length; i++) {
            var f = result.data[i];
            var early = f.refund_early ? 'Возврат ' + f.refund_early + '% стоимости, если до вылета больше 24 часов' : 'Невозвратный тариф';
            var late = f.refund_late ? 'Возврат ' + f.refund_late + '%, если до вылета меньше 24 часов' : 'Менее чем за 24 часа возврат невозможен';
            html += '<div class="fare-card"><span class="label">' + esc(f.cabin_display) + '</span><h3>' + esc(f.name) + '</h3>' +
                '<ul><li>' + esc(f.baggage) + '</li><li>' + early + '</li><li>' + late + '</li><li>После вылета билет не возвращается</li></ul></div>';
        }
        document.getElementById('fare-list').innerHTML = html;
    })
    .catch(function () {
        serverDown(document.getElementById('fare-list'));
    });
