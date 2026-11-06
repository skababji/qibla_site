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

        // Route animation (shown instead of the compasses when the switch is on)
        animState.data = data;
        animState.city = city.split(',')[0];
        document.getElementById('animSwitch').hidden = false;
        if (document.getElementById('animToggle').checked) {
            startAnimation();
        }

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


/* ---------- Route animation ----------
 * Draws each route on a globe (orthographic projection, seen from above the equator
 * so the North Pole is visible) with a point travelling from the city to the Kaaba.
 * The arrow at the point shows its heading; the dashed line shows local north.
 */
const ANIM_SIZE = 350;      // logical canvas size in CSS pixels
const ANIM_RADIUS = 138;    // globe radius
const ANIM_TRAVEL_MS = 9000;
const ANIM_HOLD_MS = 1800;
const animState = { data: null, city: '', frame: null, scenes: [] };

document.getElementById('animToggle').addEventListener('change', function() {
    document.body.classList.toggle('mode-animation', this.checked);
    if (this.checked) {
        startAnimation();
    } else {
        stopAnimation();
    }
});

function toRad(d) { return d * Math.PI / 180; }
function toDeg(r) { return r * 180 / Math.PI; }
function wrap180(d) { return ((d + 540) % 360) - 180; }

function chooseView(data) {
    const [startLat, startLon] = data.paths.rhumb[0];
    const [kLat, kLon] = data.kaaba;
    return {
        lon0: toRad(startLon + wrap180(kLon - startLon) / 2),
        lat0: toRad(Math.min(55, Math.max(15, (startLat + kLat) / 2 + 20))),
    };
}

// Orthographic projection; z < 0 means the point is on the far side of the globe
function project(view, lat, lon) {
    const phi = toRad(lat), dLon = toRad(lon) - view.lon0;
    const x = Math.cos(phi) * Math.sin(dLon);
    const y = Math.cos(view.lat0) * Math.sin(phi) - Math.sin(view.lat0) * Math.cos(phi) * Math.cos(dLon);
    const z = Math.sin(view.lat0) * Math.sin(phi) + Math.cos(view.lat0) * Math.cos(phi) * Math.cos(dLon);
    return { x: ANIM_SIZE / 2 + ANIM_RADIUS * x, y: ANIM_SIZE / 2 - ANIM_RADIUS * y, z };
}

// Point a small angular distance (degrees) away along a bearing, on a sphere
function offsetPoint(lat, lon, bearing, dist) {
    const p1 = toRad(lat), d = toRad(dist), b = toRad(bearing);
    const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
    const l2 = toRad(lon) + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1),
                                       Math.cos(d) - Math.sin(p1) * Math.sin(p2));
    return [toDeg(p2), toDeg(l2)];
}

// Stroke a lat/lon polyline, styling front and far-side runs separately
function strokeLatLon(ctx, view, points, front, back) {
    let run = [], runFront = null;
    const flush = () => {
        if (run.length > 1) {
            const style = runFront ? front : back;
            if (style) {
                ctx.save();
                Object.assign(ctx, style);
                ctx.setLineDash(style.dash || []);
                ctx.beginPath();
                run.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
                ctx.stroke();
                ctx.restore();
            }
        }
    };
    points.forEach(([lat, lon]) => {
        const p = project(view, lat, lon);
        const isFront = p.z >= 0;
        if (runFront !== null && isFront !== runFront) {
            run.push(p);   // close the gap at the horizon
            flush();
            run = [run[run.length - 1]];
        }
        runFront = isFront;
        run.push(p);
    });
    flush();
}

function drawLabel(ctx, p, text, color, font) {
    ctx.font = font;
    ctx.fillStyle = color;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    // Prefer the outer side of the dot, but flip or clamp so the label stays on the canvas
    const width = ctx.measureText(text).width, pad = 4, gap = 9;
    const leftX = p.x - gap - width, rightX = p.x + gap;
    let x = p.x < ANIM_SIZE / 2 ? leftX : rightX;
    if (x < pad) x = rightX;
    if (x + width > ANIM_SIZE - pad) x = leftX;
    x = Math.min(Math.max(x, pad), ANIM_SIZE - pad - width);
    ctx.fillText(text, x, p.y - gap);
}

function drawArrow(ctx, from, dx, dy, len, color, width, head) {
    const norm = Math.hypot(dx, dy);
    if (norm < 1e-6) return;
    const ux = dx / norm, uy = dy / norm;
    const tx = from.x + ux * len, ty = from.y + uy * len;
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(tx, ty);
    ctx.stroke();
    if (head) {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(tx + ux * 4, ty + uy * 4);
        ctx.lineTo(tx - ux * 7 - uy * 5, ty - uy * 7 + ux * 5);
        ctx.lineTo(tx - ux * 7 + uy * 5, ty - uy * 7 - ux * 5);
        ctx.closePath();
        ctx.fill();
    }
}

// Position along the sampled path at fraction f (0..1)
function samplePath(path, f) {
    const pos = f * (path.length - 1);
    const i = Math.min(Math.floor(pos), path.length - 2);
    const t = path.length > 1 ? pos - i : 0;
    const a = path[i], b = path[Math.min(i + 1, path.length - 1)];
    return {
        index: i,
        lat: a[0] + (b[0] - a[0]) * t,
        lon: a[1] + wrap180(b[1] - a[1]) * t,
        bearing: (a[2] + wrap180(b[2] - a[2]) * t + 360) % 360,
        remaining: a[3] + (b[3] - a[3]) * t,
    };
}

function drawScene(scene, f) {
    const { ctx, path, view } = scene;
    const c = {
        ink: cssVar('--ink'), muted: cssVar('--muted'), line: cssVar('--line'),
        lineStrong: cssVar('--line-strong'), face: cssVar('--surface-2'),
        surface: cssVar('--surface'), gold: cssVar('--gold'), accent: cssVar('--accent'),
        route: cssVar(scene.colorVar),
    };
    const mid = ANIM_SIZE / 2;
    ctx.clearRect(0, 0, ANIM_SIZE, ANIM_SIZE);

    // Globe
    ctx.beginPath();
    ctx.arc(mid, mid, ANIM_RADIUS, 0, 2 * Math.PI);
    ctx.fillStyle = c.face;
    ctx.fill();

    // Graticule: parallels and meridians every 30°
    const grid = { strokeStyle: c.lineStrong, lineWidth: 0.8, globalAlpha: 0.6 };
    for (let lat = -60; lat <= 60; lat += 30) {
        const pts = [];
        for (let lon = -180; lon <= 180; lon += 3) pts.push([lat, lon]);
        strokeLatLon(ctx, view, pts, lat === 0 ? { ...grid, lineWidth: 1.4 } : grid, null);
    }
    for (let lon = -180; lon < 180; lon += 30) {
        const pts = [];
        for (let lat = -90; lat <= 90; lat += 3) pts.push([lat, lon]);
        strokeLatLon(ctx, view, pts, grid, null);
    }

    ctx.beginPath();
    ctx.arc(mid, mid, ANIM_RADIUS, 0, 2 * Math.PI);
    ctx.strokeStyle = c.ink;
    ctx.globalAlpha = 0.7;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Route: whole path faint, travelled part bold, far side dashed
    const here = samplePath(path, f);
    const travelled = path.slice(0, here.index + 1).map(r => [r[0], r[1]]).concat([[here.lat, here.lon]]);
    const all = path.map(r => [r[0], r[1]]);
    strokeLatLon(ctx, view, all,
        { strokeStyle: c.route, lineWidth: 2, globalAlpha: 0.35 },
        { strokeStyle: c.route, lineWidth: 1.5, globalAlpha: 0.3, dash: [4, 4] });
    strokeLatLon(ctx, view, travelled,
        { strokeStyle: c.route, lineWidth: 3.5, globalAlpha: 1, lineCap: 'round' },
        { strokeStyle: c.route, lineWidth: 2, globalAlpha: 0.5, dash: [4, 4] });

    // North Pole, city and Kaaba
    const pole = project(view, 90, 0);
    if (pole.z >= 0) {
        ctx.fillStyle = c.accent;
        ctx.beginPath();
        ctx.arc(pole.x, pole.y, 3.5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.font = '600 12px system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('North Pole', pole.x, pole.y - 6);
    }

    const start = project(view, path[0][0], path[0][1]);
    ctx.globalAlpha = start.z >= 0 ? 1 : 0.4;
    ctx.fillStyle = c.ink;
    ctx.beginPath();
    ctx.arc(start.x, start.y, 4, 0, 2 * Math.PI);
    ctx.fill();
    drawLabel(ctx, start, animState.city, c.ink, '600 12px system-ui, sans-serif');

    const kaaba = project(view, animState.data.kaaba[0], animState.data.kaaba[1]);
    ctx.globalAlpha = kaaba.z >= 0 ? 1 : 0.4;
    ctx.fillStyle = '#111';
    ctx.fillRect(kaaba.x - 4.5, kaaba.y - 4.5, 9, 9);
    ctx.fillStyle = c.gold;
    ctx.fillRect(kaaba.x - 4.5, kaaba.y - 2, 9, 2);
    ctx.strokeStyle = c.ink;
    ctx.lineWidth = 1;
    ctx.strokeRect(kaaba.x - 4.5, kaaba.y - 4.5, 9, 9);
    drawLabel(ctx, kaaba, 'Makkah', c.ink, '600 12px system-ui, sans-serif');
    ctx.globalAlpha = 1;

    // Moving point with local north (dashed) and heading (arrow)
    const p = project(view, here.lat, here.lon);
    const visible = p.z >= 0;
    if (visible && f < 1) {
        const n = project(view, ...offsetPoint(here.lat, here.lon, 0, 2));
        const h = project(view, ...offsetPoint(here.lat, here.lon, here.bearing, 2));
        ctx.save();
        ctx.setLineDash([3, 3]);
        drawArrow(ctx, p, n.x - p.x, n.y - p.y, 30, c.muted, 1.5, false);
        ctx.restore();
        drawArrow(ctx, p, h.x - p.x, h.y - p.y, 34, c.route, 2.5, true);
    }
    ctx.globalAlpha = visible ? 1 : 0.45;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6.5, 0, 2 * Math.PI);
    ctx.fillStyle = c.route;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = c.surface;
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Readout under the globe
    const b = Math.round(here.bearing);
    const text = f >= 1
        ? `Arrived · final bearing ${b}° ${bearingToDirection(b)}`
        : `Bearing ${b}° ${bearingToDirection(b)} · ${Math.round(here.remaining).toLocaleString()} km to go`;
    if (scene.readout.textContent !== text) {
        scene.readout.textContent = text;
    }
}

function startAnimation() {
    stopAnimation();
    const data = animState.data;
    if (!data) return;
    const view = chooseView(data);
    const dpr = window.devicePixelRatio || 1;

    animState.scenes = [
        ['anim1', data.paths.rhumb, '--rhumb', 'rhumb line'],
        ['anim2', data.paths.gc, '--gc', 'great circle'],
    ].map(([id, path, colorVar, name]) => {
        const box = document.getElementById(id);
        box.innerHTML = '';
        const canvas = document.createElement('canvas');
        canvas.width = ANIM_SIZE * dpr;
        canvas.height = ANIM_SIZE * dpr;
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', `Animation of the ${name} route from ${animState.city} to Makkah`);
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        const readout = document.createElement('p');
        readout.className = 'anim-readout';
        box.append(canvas, readout);
        return { ctx, path, view, colorVar, readout };
    });

    const t0 = performance.now();
    const tick = (now) => {
        const phase = (now - t0) % (ANIM_TRAVEL_MS + ANIM_HOLD_MS);
        const f = Math.min(phase / ANIM_TRAVEL_MS, 1);
        animState.frame = requestAnimationFrame(tick);
        // Draw each globe separately so a problem in one never stops the other
        animState.scenes.forEach(scene => {
            if (scene.failed) return;
            try {
                drawScene(scene, f);
            } catch (err) {
                scene.failed = true;
                console.error('Route animation failed:', err);
                scene.readout.textContent = 'Animation error: ' + err.message;
            }
        });
    };
    animState.frame = requestAnimationFrame(tick);
}

function stopAnimation() {
    if (animState.frame !== null) {
        cancelAnimationFrame(animState.frame);
        animState.frame = null;
    }
}
