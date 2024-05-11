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

function drawCompass(bearing) {
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');

    // Move to center of the canvas
    ctx.translate(100, 100);

    // Convert bearing to radians and adjust rotation:
    // Subtract 90 degrees to align North correctly.
    const adjustedBearing = (bearing) * Math.PI / 180;
    ctx.rotate(adjustedBearing);

    // Draw the compass circle
    ctx.beginPath();
    ctx.arc(0, 0, 80, 0, 2 * Math.PI);
    ctx.strokeStyle = '#000000';
    ctx.stroke();

    // Draw the needle with arrow pointing north
    ctx.beginPath();
    ctx.moveTo(0, 10);  // Base of the needle (inside the circle)
    ctx.lineTo(0, -75); // Tip of the needle
    ctx.strokeStyle = '#FF0000';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Arrowhead
    ctx.beginPath();
    ctx.moveTo(0, -75);
    ctx.lineTo(-10, -60);
    ctx.lineTo(10, -60);
    ctx.closePath();
    ctx.fillStyle = '#FF0000';
    ctx.fill();

    // Reset rotation to add labels without rotation
    ctx.rotate(-adjustedBearing);

    // Draw direction labels
    ctx.fillStyle = '#000000';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle'; // This ensures that the text is centered both ways
    ctx.fillText('N', 0, -100);  // Move 'N' a bit further from the center
    ctx.fillText('S', 0, 100);   // Move 'S' a bit further from the center
    ctx.fillText('E', 100, 0);   // Move 'E' a bit further from the center
    ctx.fillText('W', -100, 0);  // Move 'W' a bit further from the center

    return canvas;
}




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
            document.getElementById('results').innerHTML = 'Your city coordinates: ' + data.city_coords + '<br><br>' +
            'Rhumb Line Bearing: ' + data.rhumb_bearing + ' degrees<br>' +
            'Rhumb Line Distance: ' + data.rhumb_distance + ' km<br><br>' +
            'Great Circle Initial Bearing: ' + data.gc_initial_bearing + ' degrees<br>' +
            'Great Circle Final Bearing: ' + data.gc_final_bearing + ' degrees<br>' +
            'Great Circle Distance: ' + data.gc_distance + ' km';
            const compassContainer = document.getElementById('compass');
            compassContainer.innerHTML = ''; // Clear previous compass
            compassContainer.appendChild(drawCompass(data.rhumb_bearing));
        }
    });
});
