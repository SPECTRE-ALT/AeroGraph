import json
from math import atan, cos, exp, radians, sin, sqrt
from typing import Any
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen

import numpy as np
from flask import Flask, jsonify, render_template, request
from scipy.optimize import Bounds, LinearConstraint, milp

from graph_solver import LOCATIONS, nearest_location, solve_dispatch

app = Flask(__name__)

def _fetch_json(url: str) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "Aerograph-Dispatch-Demo/1.0"})
    with urlopen(req, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


def _risk_level(probability: float) -> str:
    if probability >= 0.85:
        return "CRITICAL"
    if probability >= 0.7:
        return "SEVERE"
    if probability >= 0.45:
        return "ELEVATED"
    return "LOW"


def _assign_fleet() -> tuple[dict[str, Any], dict[str, Any]]:
    units = [
        {"role": "vehicle", "callsign": "AEGIS-04", "type": "Rapid response vehicle", "battery": 87},
        {"role": "vehicle", "callsign": "AEGIS-03", "type": "Rapid response vehicle", "battery": 74},
        {"role": "drone", "callsign": "SKYLARK-02", "type": "Aerial reconnaissance", "battery": 91},
        {"role": "drone", "callsign": "SKYLARK-01", "type": "Aerial reconnaissance", "battery": 69},
    ]
    costs = np.asarray([(100 - unit["battery"]) / 100 for unit in units])
    matrix = np.asarray([
        [int(unit["role"] == "vehicle") for unit in units],
        [int(unit["role"] == "drone") for unit in units],
    ])
    result = milp(
        c=costs,
        integrality=np.ones(len(units)),
        bounds=Bounds(np.zeros(len(units)), np.ones(len(units))),
        constraints=LinearConstraint(matrix, [1, 1], [1, 1]),
    )
    if not result.success or result.x is None:
        raise RuntimeError("Fleet assignment optimization did not find a solution")
    chosen = [unit for unit, selected in zip(units, result.x) if selected > 0.5]
    return next(unit for unit in chosen if unit["role"] == "vehicle"), next(unit for unit in chosen if unit["role"] == "drone")


def _coordinate(payload: dict[str, Any], key: str) -> tuple[float, float] | None:
    value = payload.get(key) or payload.get(f"{key}_coordinates")
    if value is None:
        return None
    if isinstance(value, dict):
        latitude, longitude = value.get("lat"), value.get("lng", value.get("lon"))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        latitude, longitude = value
    else:
        raise ValueError(f"{key} must contain lat and lng coordinates")
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} must contain numeric lat and lng coordinates") from error
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError(f"{key} coordinates are outside valid latitude/longitude bounds")
    return latitude, longitude


def _haversine_km(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    radius = 6371.0
    delta_lat = radians(lat_b - lat_a)
    delta_lng = radians(lng_b - lng_a)
    value = sin(delta_lat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(delta_lng / 2) ** 2
    return 2 * radius * atan(sqrt(value) / sqrt(max(1e-15, 1 - value)))


def _bounded_probability(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _terrain_slope(lat: float, lng: float) -> tuple[float | None, float | None]:
    lat_step = 0.005
    lng_step = 0.005 / max(0.2, cos(radians(lat)))
    points = [
        (lat, lng),
        (lat + lat_step, lng),
        (lat - lat_step, lng),
        (lat, lng + lng_step),
        (lat, lng - lng_step),
    ]
    params = urlencode({
        "latitude": ",".join(f"{point[0]:.5f}" for point in points),
        "longitude": ",".join(f"{point[1]:.5f}" for point in points),
    })
    try:
        elevations = _fetch_json(f"https://api.open-meteo.com/v1/elevation?{params}").get("elevation")
        if not isinstance(elevations, list) or len(elevations) != len(points) or any(value is None for value in elevations):
            return None, None
        center = float(elevations[0])
        north_south = abs(float(elevations[1]) - float(elevations[2])) / (2 * lat_step * 111000)
        east_west = abs(float(elevations[3]) - float(elevations[4])) / (2 * lat_step * 111000)
        slope_degrees = atan(sqrt(north_south ** 2 + east_west ** 2)) * 180 / 3.141592653589793
        return round(center, 1), round(slope_degrees, 2)
    except (URLError, TimeoutError, OSError, ValueError, TypeError, KeyError):
        return None, None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/locations")
def locations():
    return jsonify([
        {"name": name, "lng": longitude, "lat": latitude}
        for name, (longitude, latitude) in LOCATIONS.items()
    ])


@app.get("/api/predict_hazards")
def predict_hazards():
    try:
        latitude = float(request.args["lat"])
        longitude = float(request.args.get("lon", request.args.get("lng")))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat and lon query parameters are required."}), 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return jsonify({"error": "Coordinates are outside valid latitude/longitude bounds."}), 400

    weather_variables = "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,weather_code,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,is_day"
    hourly_variables = "temperature_2m,precipitation_probability,rain,dew_point_2m,uv_index"
    daily_variables = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    weather_params = urlencode({
        "latitude": str(latitude),
        "longitude": str(longitude),
        "current": weather_variables,
        "hourly": hourly_variables,
        "daily": daily_variables,
        "forecast_days": 5,
        "timezone": "auto",
    })
    try:
        weather = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{weather_params}")
        current = weather.get("current")
        if not isinstance(current, dict):
            raise ValueError("Open-Meteo did not return current conditions")
    except (URLError, TimeoutError, OSError, ValueError) as error:
        return jsonify({"error": f"Weather data is temporarily unavailable: {error}"}), 503

    air_params = urlencode({"latitude": f"{latitude:.5f}", "longitude": f"{longitude:.5f}", "current": "us_aqi"})
    try:
        air_data = _fetch_json(f"https://air-quality-api.open-meteo.com/v1/air-quality?{air_params}")
        aqi = (air_data.get("current") or {}).get("us_aqi")
    except (URLError, TimeoutError, OSError, ValueError):
        aqi = None

    sources = {"weather": "Open-Meteo", "air_quality": "Open-Meteo" if aqi is not None else "unavailable"}
    usgs_params = urlencode({"format": "geojson", "minmagnitude": 2.5, "limit": 10, "orderby": "time"})
    earthquakes = []
    try:
        seismic = _fetch_json(f"https://earthquake.usgs.gov/fdsnws/event/1/query?{usgs_params}")
        for feature in seismic.get("features", []):
            properties = feature.get("properties") or {}
            coordinates = (feature.get("geometry") or {}).get("coordinates") or []
            if len(coordinates) < 2:
                continue
            event_lat, event_lng = float(coordinates[1]), float(coordinates[0])
            earthquakes.append({
                "magnitude": float(properties.get("mag") or 0),
                "place": properties.get("place") or "Unspecified location",
                "time": properties.get("time"),
                "lat": event_lat,
                "lng": event_lng,
                "distance_km": round(_haversine_km(latitude, longitude, event_lat, event_lng), 2),
            })
        sources["seismic"] = "USGS"
    except (URLError, TimeoutError, OSError, ValueError, TypeError):
        sources["seismic"] = "unavailable"

    elevation, slope_degrees = _terrain_slope(latitude, longitude)
    sources["terrain"] = "Open-Meteo elevation" if slope_degrees is not None else "unavailable"
    precipitation = max(float(current.get("precipitation") or 0), float(current.get("rain") or 0) + float(current.get("showers") or 0))
    humidity = float(current.get("relative_humidity_2m") or 0)
    nearest_quake = min(earthquakes, key=lambda event: event["distance_km"], default=None)
    earthquake_probability = None
    if nearest_quake is not None:
        magnitude_factor = max(0.0, min(1.0, (nearest_quake["magnitude"] - 2.0) / 4.5))
        proximity_factor = exp(-nearest_quake["distance_km"] / 120)
        earthquake_probability = _bounded_probability(magnitude_factor * proximity_factor)
    flood_probability = _bounded_probability(0.78 * min(1.0, precipitation / 15) + 0.22 * humidity / 100)
    slope_factor = min(1.0, (slope_degrees or 0.0) / 35)
    landslide_probability = _bounded_probability(0.5 * slope_factor + 0.38 * min(1.0, precipitation / 15) + 0.12 * humidity / 100)
    risks = [
        {"kind": "earthquake", "label": "Earthquake", "probability": earthquake_probability, "level": _risk_level(earthquake_probability) if earthquake_probability is not None else "UNAVAILABLE"},
        {"kind": "flood", "label": "Flood", "probability": flood_probability, "level": _risk_level(flood_probability)},
        {"kind": "landslide", "label": "Landslide", "probability": landslide_probability, "level": _risk_level(landslide_probability)},
    ]
    current_time = current.get("time")
    hourly = weather.get("hourly") or {}
    daily = weather.get("daily") or {}
    return jsonify({
        "status": "success",
        "coordinates": {"lat": latitude, "lon": longitude},
        "sources": sources,
        "weather": {"current": current, "hourly": hourly, "daily": daily, "aqi": aqi},
        "terrain": {"elevation_m": elevation, "slope_degrees": slope_degrees},
        "rainfall_mm_h": precipitation,
        "earthquakes": earthquakes,
        "nearest_earthquake": nearest_quake,
        "risks": risks,
        "hazards": [
            {"kind": risk["kind"], "probability": risk["probability"], "level": risk["level"], "lat": latitude, "lng": longitude}
            for risk in risks if risk["probability"] is not None
        ],
        "updated_at": current_time,
    })


@app.post("/api/predict_and_dispatch")
def predict_and_dispatch():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON request body is required."}), 400

    try:
        rainfall = float(payload.get("rainfall_rate_mm", payload.get("rainfall", 82)))
        displacement = float(payload.get("insar_displacement_mm", payload.get("displacement", 24)))
        if not 0 <= rainfall <= 150:
            raise ValueError("rainfall_rate_mm must be between 0 and 150")
        if not 0 <= displacement <= 50:
            raise ValueError("insar_displacement_mm must be between 0 and 50")

        start = _coordinate(payload, "start")
        end = _coordinate(payload, "end")
        start_node = payload.get("start_node", "Hospital")
        end_node = payload.get("end_node", "Emergency_Site")
        if start:
            start_node = nearest_location(start[1], start[0])
        if end:
            end_node = nearest_location(end[1], end[0])

        active_hazards = payload.get("active_hazards", [])
        if not isinstance(active_hazards, list):
            raise ValueError("active_hazards must be a list")
        hazard_zones = []
        for zone in active_hazards[:32]:
            if not isinstance(zone, dict):
                continue
            coordinate = _coordinate(zone, "location")
            if coordinate is None:
                coordinate = _coordinate(zone, "coordinates")
            if coordinate is None:
                try:
                    coordinate = float(zone["lat"]), float(zone["lng"])
                except (KeyError, TypeError, ValueError):
                    continue
            hazard_zones.append({
                "kind": zone.get("kind", "unknown"),
                "lat": coordinate[0],
                "lng": coordinate[1],
                "radius_km": zone.get("radius_km", 0.25),
                "risk": zone.get("risk", 0.5),
            })

        result = solve_dispatch(
            rainfall,
            displacement,
            start_node,
            end_node,
            hazard_zones=hazard_zones,
        )
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400

    risk = result["active_hazard_probability"]
    risk_level = "CRITICAL" if risk >= 0.75 else "ELEVATED" if risk >= 0.45 else "GUARDED"
    vehicle, drone = _assign_fleet()
    battery = max(18, round(vehicle["battery"] - result["total_distance_km"] * 3.4))
    route_coordinates = [[point["lat"], point["lng"]] for point in result["coordinates"]]
    if end and route_coordinates:
        clicked_coordinate = [end[0], end[1]]
        if route_coordinates[-1] != clicked_coordinate:
            route_coordinates.append(clicked_coordinate)
    return jsonify({
        "status": "success",
        "path_nodes": result["path_nodes"],
        "coordinates": route_coordinates,
        "risk_score": risk,
        "risk_level": risk_level,
        "eta_minutes": result["total_eta_minutes"],
        "path_cost": result["total_distance_km"],
        "distance_km": result["total_distance_km"],
        "is_rerouted": result["is_rerouted"],
        "hazard_scores": result["hazard_scores"],
        "alert_message": result["alert_message"],
        "dispatched_unit": {
            "callsign": vehicle["callsign"],
            "vehicle_type": vehicle["type"],
            "status": "EN ROUTE",
            "battery_percent": battery,
        },
        "drone": {
            "callsign": drone["callsign"],
            "status": "RECON ACTIVE",
            "battery_percent": drone["battery"],
        },
        "active_fleet_status": "04 / 06 UNITS AVAILABLE",
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)