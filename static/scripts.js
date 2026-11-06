const COMPASS_SIZE = 350; // logical size in CSS pixels

function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function bearingToDirection(bearing) {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.floor(((bearing % 360) + 360 + 11.25) / 22.5) % 16];
}

function formatBearing(value) {
    const b = Math.round(Number(value));
    return `${b}° <small>${bearingToDirection(b)}</small>`;
}

function formatDistance(value) {
    return `${Math.round(Number(value)).toLocaleString()} km`;
}

function statsHtml(rows) {
    return '<dl class="stats">' +
        rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join('') +
        '</dl>';
}

function showCompass(containerId, bearing, routeVar) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    container.appendChild(drawCompass(bearing, cssVar(routeVar)));
}

// Empty dials before any calculation
showCompass('compass1', null, '--rhumb');
showCompass('compass2', null, '--gc');

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
            citySelect.add(new Option(city.label, city.id));
        });
        citySelect.style.display = 'block';
        document.getElementById('calculateButton').style.display = 'block';
    });
});

document.getElementById('calculateButton').addEventListener('click', function(event) {
    event.preventDefault();
    const country = document.getElementById('countrySelect').value;
    const citySelect = document.getElementById('citySelect');
    const cityId = citySelect.value;
    if (!cityId) {
        document.getElementById('results').textContent = 'Please select a city.';
        return;
    }
    const city = citySelect.options[citySelect.selectedIndex].text;
    fetch('/calculate_bearing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'city_id=' + encodeURIComponent(cityId)
    }).then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('results').textContent = data.error;
            return;
        }

        const initial = Number(data.gc_initial_bearing);
        const final = Number(data.gc_final_bearing);

        document.getElementById('results').textContent = 'Your city coordinates: ' + data.city_coords;

        document.getElementById('rhumbResultsText').innerHTML = statsHtml([
            ['Bearing angle', formatBearing(data.rhumb_bearing)],
            ['Distance', formatDistance(data.rhumb_distance)],
        ]);
        document.getElementById('greatCircleResultsText').innerHTML = statsHtml([
            ['Initial bearing', formatBearing(initial)],
            ['Final bearing', formatBearing(final)],
            ['Distance', formatDistance(data.gc_distance)],
        ]);

        document.getElementById('rhumbResults').style.display = 'block';
        document.getElementById('greatCircleResults').style.display = 'block';

        showCompass('compass1', data.rhumb_bearing, '--rhumb');
        showCompass('compass2', initial, '--gc');

        // Slider moves the great-circle compass from the initial to the final bearing
        const slider = document.getElementById('bearingSlider');
        const reversed = initial > final;
        slider.min = Math.min(initial, final);
        slider.max = Math.max(initial, final);
        slider.value = slider.min;
        slider.oninput = function() {
            const value = parseFloat(slider.value);
            const bearing = reversed ? initial - (value - Number(slider.min)) : value;
            showCompass('compass2', bearing, '--gc');
        };

        document.getElementById('startLabel').textContent = `${city}, ${country}`;
        document.querySelector('.bearing-slider-container').classList.add('show');

        document.getElementById('rhumbNote').style.display = 'block';
        document.getElementById('greatCircleNote').style.display = 'block';

        document.querySelector('.compass-title-container').scrollIntoView({ behavior: 'smooth' });
    });
});

// bearing: degrees clockwise from north, or null to draw an empty dial
function drawCompass(bearing, needleColor) {
    const ink = cssVar('--ink');
    const muted = cssVar('--muted');
    const line = cssVar('--line-strong');
    const face = cssVar('--surface-2');
    const accent = cssVar('--accent');

    const dpr = window.devicePixelRatio || 1;
    const canvas = document.createElement('canvas');
    canvas.width = COMPASS_SIZE * dpr;
    canvas.height = COMPASS_SIZE * dpr;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', bearing === null
        ? 'Compass'
        : `Compass pointing ${Math.round(bearing)} degrees`);
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.translate(COMPASS_SIZE / 2, COMPASS_SIZE / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Dial face and ring
    ctx.beginPath();
    ctx.arc(0, 0, 140, 0, 2 * Math.PI);
    ctx.fillStyle = face;
    ctx.fill();
    ctx.strokeStyle = ink;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Tick marks every 5°, longer every 10°
    for (let i = 0; i < 360; i += 5) {
        const a = (i - 90) * Math.PI / 180;
        const inner = i % 10 === 0 ? 128 : 133;
        ctx.beginPath();
        ctx.moveTo(inner * Math.cos(a), inner * Math.sin(a));
        ctx.lineTo(140 * Math.cos(a), 140 * Math.sin(a));
        ctx.strokeStyle = line;
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // Degree labels
    ctx.font = '10px system-ui, sans-serif';
    ctx.fillStyle = muted;
    for (let i = 0; i < 360; i += 10) {
        const a = (i - 90) * Math.PI / 180;
        ctx.fillText(i.toString(), 114 * Math.cos(a), 114 * Math.sin(a));
    }

    // Main (N, E, S, W) and secondary (NE, SE, SW, NW) lines
    ctx.strokeStyle = ink;
    [[0, 90, 180, 270], [45, 135, 225, 315]].forEach((angles, idx) => {
        ctx.lineWidth = idx === 0 ? 2 : 1;
        ctx.globalAlpha = idx === 0 ? 0.55 : 0.3;
        angles.forEach(angle => {
            const r = (angle - 90) * Math.PI / 180;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(100 * Math.cos(r), 100 * Math.sin(r));
            ctx.stroke();
        });
    });
    ctx.globalAlpha = 1;

    // Direction labels
    const labels = [['N', 0], ['E', 90], ['S', 180], ['W', 270],
                    ['NE', 45], ['SE', 135], ['SW', 225], ['NW', 315]];
    labels.forEach(([text, angle]) => {
        const a = (angle - 90) * Math.PI / 180;
        const main = text.length === 1;
        ctx.font = main ? '600 18px system-ui, sans-serif' : '13px system-ui, sans-serif';
        ctx.fillStyle = text === 'N' ? accent : (main ? ink : muted);
        ctx.fillText(text, 160 * Math.cos(a), 160 * Math.sin(a));
    });

    // Needle
    if (bearing !== null) {
        ctx.save();
        ctx.rotate(bearing * Math.PI / 180);

        ctx.beginPath();
        ctx.moveTo(0, -122);
        ctx.lineTo(-9, 0);
        ctx.lineTo(9, 0);
        ctx.closePath();
        ctx.fillStyle = needleColor;
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(0, 122);
        ctx.lineTo(-9, 0);
        ctx.lineTo(9, 0);
        ctx.closePath();
        ctx.fillStyle = line;
        ctx.fill();

        ctx.restore();
    }

    // Hub
    ctx.beginPath();
    ctx.arc(0, 0, 6, 0, 2 * Math.PI);
    ctx.fillStyle = ink;
    ctx.fill();

    return canvas;
}
