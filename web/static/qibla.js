/* Qibla calculations: rhumb line (sphere) and great circle (WGS-84 ellipsoid).
 *
 * Rhumb line: the formulas in the README, on a sphere of mean Earth radius.
 * Great circle: GeographicLib's geodesic on the WGS-84 ellipsoid (C. F. F. Karney).
 * Works in the browser (window.qibla) and in Node (module.exports) for testing.
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory(require('./vendor/geographiclib-geodesic.min.js'));
    } else {
        root.qibla = factory(root.geodesic);
    }
})(typeof self !== 'undefined' ? self : this, function (geodesic) {
    'use strict';

    // The Kaaba, Masjid al-Haram, Makkah (latitude, longitude in degrees)
    const KAABA = [21.422487, 39.826206];
    const EARTH_RADIUS_M = 6371008.771415;  // WGS-84 mean radius R1 = (2a + b) / 3
    const ROUTE_SAMPLES = 150;              // points per route for the animation

    const WGS84 = geodesic.Geodesic.WGS84;
    const RAD = Math.PI / 180;

    const norm360 = (deg) => ((deg % 360) + 360) % 360;
    const wrapPi = (rad) => {
        const r = (rad + Math.PI) % (2 * Math.PI);
        return (r < 0 ? r + 2 * Math.PI : r) - Math.PI;
    };
    const wrap180 = (deg) => wrapPi(deg * RAD) / RAD;

    // Isometric latitude difference (Mercator "stretched" north-south distance)
    function deltaPsi(phi1, phi2) {
        return Math.log(Math.tan(Math.PI / 4 + phi2 / 2) / Math.tan(Math.PI / 4 + phi1 / 2));
    }

    // q = dPhi / dPsi, or cos(phi) for an east-west line
    function rhumbQ(phi1, dPhi, dPsi) {
        return Math.abs(dPsi) > 1e-12 ? dPhi / dPsi : Math.cos(phi1);
    }

    function rhumbInverse(lat1, lon1, lat2, lon2) {
        const phi1 = lat1 * RAD, phi2 = lat2 * RAD;
        const dPhi = phi2 - phi1;
        const dLambda = wrapPi((lon2 - lon1) * RAD);
        const dPsi = deltaPsi(phi1, phi2);
        const q = rhumbQ(phi1, dPhi, dPsi);
        return {
            bearing: norm360(Math.atan2(dLambda, dPsi) / RAD),
            distance: EARTH_RADIUS_M * Math.hypot(dPhi, q * dLambda),
        };
    }

    function rhumbDirect(lat1, lon1, bearing, distance) {
        const phi1 = lat1 * RAD, theta = bearing * RAD;
        const delta = distance / EARTH_RADIUS_M;
        const dPhi = delta * Math.cos(theta);
        let phi2 = phi1 + dPhi;
        if (Math.abs(phi2) > Math.PI / 2) {
            phi2 = phi2 > 0 ? Math.PI - phi2 : -Math.PI - phi2;
        }
        const q = rhumbQ(phi1, dPhi, deltaPsi(phi1, phi2));
        const dLambda = delta * Math.sin(theta) / q;
        return [phi2 / RAD, wrap180(lon1 + dLambda / RAD)];
    }

    function round(x, digits) {
        const f = Math.pow(10, digits || 0);
        return Math.round(x * f) / f;
    }

    // Same result shape the Flask app returned, so the page code is unchanged
    function compute(lat, lng) {
        const [kLat, kLon] = KAABA;

        const rhumb = rhumbInverse(lat, lng, kLat, kLon);

        const inv = WGS84.Inverse(lat, lng, kLat, kLon);
        const gcInitial = norm360(inv.azi1);
        const gcFinal = norm360(inv.azi2);
        const gcDistance = inv.s12;

        const rhumbPath = [], gcPath = [];
        const line = WGS84.InverseLine(lat, lng, kLat, kLon);
        for (let i = 0; i <= ROUTE_SAMPLES; i++) {
            const frac = i / ROUTE_SAMPLES;

            const [rLat, rLon] = rhumbDirect(lat, lng, rhumb.bearing, rhumb.distance * frac);
            rhumbPath.push([round(rLat, 4), round(rLon, 4), round(rhumb.bearing, 1),
                            Math.round(rhumb.distance * (1 - frac) / 1000)]);

            const p = line.Position(gcDistance * frac);
            const heading = i === ROUTE_SAMPLES ? gcFinal : norm360(p.azi2);
            gcPath.push([round(p.lat2, 4), round(wrap180(p.lon2), 4), round(heading, 1),
                         Math.round(gcDistance * (1 - frac) / 1000)]);
        }

        return {
            rhumb_bearing: Math.round(rhumb.bearing),
            rhumb_distance: Math.round(rhumb.distance / 1000),
            gc_initial_bearing: Math.round(gcInitial),
            gc_final_bearing: Math.round(gcFinal),
            gc_distance: Math.round(gcDistance / 1000),
            city_coords: `${lat}, ${lng}`,
            kaaba: KAABA,
            paths: { rhumb: rhumbPath, gc: gcPath },
        };
    }

    return { KAABA, compute, rhumbInverse, rhumbDirect };
});
