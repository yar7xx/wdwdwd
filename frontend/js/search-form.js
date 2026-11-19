function fillSearchForm(airports, values) {
    var options = '';
    for (var i = 0; i < airports.length; i++) {
        options += '<option value="' + airports[i].code + '">' + esc(airports[i].city) + ' (' + airports[i].code + ')</option>';
    }
    document.getElementById('from').innerHTML = options;
    document.getElementById('to').innerHTML = options;
    document.getElementById('from').value = values.from || 'SGC';
    document.getElementById('to').value = values.to || 'SVO';
    var dateInput = document.getElementById('date');
    var tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.min = isoDate(new Date());
    dateInput.value = values.date || isoDate(tomorrow);
    document.getElementById('passengers').value = values.passengers || '1';

    document.getElementById('swap').onclick = function () {
        var a = document.getElementById('from').value;
        document.getElementById('from').value = document.getElementById('to').value;
        document.getElementById('to').value = a;
    };
    document.getElementById('search-form').onsubmit = function (event) {
        event.preventDefault();
        var from = document.getElementById('from').value;
        var to = document.getElementById('to').value;
        if (from === to) {
            toast('Город вылета и прилёта совпадают', 'error');
            return;
        }
        window.location.href = 'flights.html?from=' + from + '&to=' + to + '&date=' + dateInput.value +
            '&passengers=' + document.getElementById('passengers').value;
    };
}
