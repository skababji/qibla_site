document.getElementById('countrySelect').addEventListener('change', function() {
    const country = this.value;
    if (!country) {
        document.getElementById('citySelect').style.display = 'none';
        document.getElementById('calculateButton').style.display = 'none';
        return;
    }
    fetch('/get_cities', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'country=' + encodeURIComponent(country)
    }).then(response => response.json())
    .then(data => {
        let citySelect = document.getElementById('citySelect');
        citySelect.innerHTML = '<option value="">Select your city</option>';
        data.forEach(city => {
            let option = new Option(city, city);
            citySelect.add(option);
        });
        citySelect.style.display = 'block';
        document.getElementById('calculateButton').style.display = 'block';
    });
});

document.getElementById('calculateButton').addEventListener('click', function(event) {
    event.preventDefault();
    const country = document.getElementById('countrySelect').value;
    const city = document.getElementById('citySelect').value;
    fetch('/calculate_bearing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'country=' + encodeURIComponent(country) + '&city=' + encodeURIComponent(city)
    }).then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('results').textContent = data.error;
        } else {
            document.getElementById('results').innerHTML = 'Your city coordinates: ' + data.city_coords + '<br>Rhumb Line Bearing: ' + data.rhumb_bearing + ' degrees<br>Distance to Mecca: ' + data.rhumb_distance + ' km';
        }
    });
});
