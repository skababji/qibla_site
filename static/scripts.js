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
            document.getElementById('results').innerHTML = 'Your city coordinates: ' + data.city_coords + '<br><br>';
            
            const rhumbResults = document.getElementById('rhumbResults');
            const greatCircleResults = document.getElementById('greatCircleResults');
            document.getElementById('rhumbResultsText').innerHTML = 'Bearing Angle: ' + data.rhumb_bearing + ' degrees<br>' +
                                     'Distance: ' + data.rhumb_distance + ' km';
            document.getElementById('greatCircleResultsText').innerHTML = 'Initial Bearing Angle: ' + data.gc_initial_bearing + ' degrees<br>' +
                                           'Final Bearing Angle: ' + data.gc_final_bearing + ' degrees<br>' +
                                           'Distance: ' + data.gc_distance + ' km';
            
            rhumbResults.style.display = 'block';
            greatCircleResults.style.display = 'block';

            const compassContainer1 = document.getElementById('compass1');
            const compassContainer2 = document.getElementById('compass2');
            compassContainer1.innerHTML = ''; // Clear previous compass
            compassContainer2.innerHTML = ''; // Clear previous compass
            compassContainer1.appendChild(drawCompass(data.rhumb_bearing)); // Pass the rhumb bearing here
            compassContainer2.appendChild(drawCompass(data.gc_initial_bearing)); // Pass the great circle initial bearing here

            // Set up slider for Great Circle Line
            const slider = document.getElementById('bearingSlider');
            const startLabel = document.getElementById('startLabel');
            const endLabel = document.getElementById('endLabel');

            if (data.gc_initial_bearing > data.gc_final_bearing) {
                slider.min = data.gc_final_bearing;
                slider.max = data.gc_initial_bearing;
                slider.value = data.gc_final_bearing;
                startLabel.textContent = `Initial Bearing: ${data.gc_initial_bearing}`;
                endLabel.textContent = `Final Bearing: ${data.gc_final_bearing}`;
            } else {
                slider.min = data.gc_initial_bearing;
                slider.max = data.gc_final_bearing;
                slider.value = data.gc_initial_bearing;
            }

            const sliderContainer = document.querySelector('.bearing-slider-container');
            sliderContainer.classList.add('show'); // Add 'show' class to display the container

            // Set the start label to city, country
            startLabel.textContent = `${city}, ${country}`;

            slider.addEventListener('input', function() {
                console.log('Slider value:', slider.value);
                const bearingValue = parseFloat(slider.value);
                const adjustedBearing = data.gc_initial_bearing > data.gc_final_bearing ? data.gc_initial_bearing - (bearingValue - slider.min) : bearingValue;
                compassContainer2.innerHTML = ''; // Clear previous compass
                compassContainer2.appendChild(drawCompass(adjustedBearing)); // Update compass with adjusted bearing value
            });

            // Scroll to the compass container
            document.querySelector('.compass-container').scrollIntoView({ behavior: 'smooth' });

            // Show the note text
            document.getElementById('rhumbNote').style.display = 'block';
            document.getElementById('greatCircleNote').style.display = 'block';
        }
    });
});

function drawCompass(bearing) {
    const canvas = document.createElement('canvas');
    canvas.width = 350;
    canvas.height = 350;
    const ctx = canvas.getContext('2d');

    // Move to the center of the canvas
    ctx.translate(175, 175);

    // Draw the compass circle
    ctx.beginPath();
    ctx.arc(0, 0, 140, 0, 2 * Math.PI);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Adjust the bearing to the correct angle for the compass
    const adjustedBearing = bearing * Math.PI / 180;

    // Draw the needle (thin triangle) - make it red
    ctx.save(); // Save the current context state
    ctx.rotate(adjustedBearing); // Rotate the context to point the needle

    ctx.beginPath();
    ctx.moveTo(0, -120); // Tip of the needle
    ctx.lineTo(-10, 0);  // Left base of the needle
    ctx.lineTo(10, 0);   // Right base of the needle
    ctx.closePath();
    ctx.fillStyle = 'red';
    ctx.fill();

    // Draw the opposite side of the needle (light grey)
    ctx.beginPath();
    ctx.moveTo(0, 120); // Tip of the needle
    ctx.lineTo(-10, 0);  // Left base of the needle
    ctx.lineTo(10, 0);   // Right base of the needle
    ctx.closePath();
    ctx.fillStyle = 'lightgrey';
    ctx.fill();

    ctx.restore(); // Restore the context to its original state

    // Draw direction labels
    ctx.fillStyle = '#000000';
    ctx.font = '18px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const mainDirections = ['N', 'E', 'S', 'W'];
    const mainAngles = [0, 90, 180, 270];
    const secondaryDirections = ['NE', 'SE', 'SW', 'NW'];
    const secondaryAngles = [45, 135, 225, 315];

    mainDirections.forEach((direction, index) => {
        const angle = (mainAngles[index] - 90) * Math.PI / 180;
        const x = 160 * Math.cos(angle);
        const y = 160 * Math.sin(angle);
        ctx.fillText(direction, x, y);
    });

    ctx.font = '14px Arial';
    secondaryDirections.forEach((direction, index) => {
        const angle = (secondaryAngles[index] - 90) * Math.PI / 180;
        const x = 160 * Math.cos(angle);
        const y = 160 * Math.sin(angle);
        ctx.fillText(direction, x, y);
    });

    // Draw main lines for N, E, S, W
    ctx.lineWidth = 3;
    mainAngles.forEach(angle => {
        const radian = (angle - 90) * Math.PI / 180;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(100 * Math.cos(radian), 100 * Math.sin(radian));
        ctx.stroke();
    });

    // Draw secondary lines for NE, SE, SW, NW
    ctx.lineWidth = 1;
    secondaryAngles.forEach(angle => {
        const radian = (angle - 90) * Math.PI / 180;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(100 * Math.cos(radian), 100 * Math.sin(radian));
        ctx.stroke();
    });

    // Draw degree markings
    ctx.font = '10px Arial';
    for (let i = 0; i < 360; i += 10) {
        const angle = (i - 90) * Math.PI / 180; // Adjust angles for correct labeling
        const x = 110 * Math.cos(angle);
        const y = 110 * Math.sin(angle);
        ctx.fillText(i.toString(), x, y);
    }

    return canvas;
}
