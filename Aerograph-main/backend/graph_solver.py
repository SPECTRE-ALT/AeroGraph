from math import inf
from typing import Any

import networkx as nx
import numpy as np
from scipy.spatial.distance import euclidean

from ml_engine import predict_edge_hazards

LOCATIONS = {
    "Hospital": (75.7804, 11.2588), "Junction_A": (75.7900, 11.2650),
    "Junction_B": (75.7700, 11.2500), "Emergency_Site": (75.8000, 11.2750),
}


def build_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    for name, (lng, lat) in LOCATIONS.items(): graph.add_node(name, lng=lng, lat=lat)
    graph.add_edge("Hospital", "Junction_A", base_time=8.0, length_km=1.25, slope=32.0, soil=0.82)
    graph.add_edge("Junction_A", "Emergency_Site", base_time=9.0, length_km=1.90, slope=28.0, soil=0.76)
    graph.add_edge("Hospital", "Junction_B", base_time=12.0, length_km=2.40, slope=6.0, soil=0.25)
    graph.add_edge("Junction_B", "Emergency_Site", base_time=13.0, length_km=2.85, slope=8.0, soil=0.28)
    return graph


def _heuristic(left: str, right: str) -> float:
    return euclidean(LOCATIONS[left], LOCATIONS[right]) * 111.0 / 0.55


def nearest_location(lng: float, lat: float) -> str:
    return min(
        LOCATIONS,
        key=lambda name: euclidean((lng, lat), LOCATIONS[name]),
    )


def _distance_to_edge_km(lng: float, lat: float, left: str, right: str) -> float:
    scale_x = 111.0 * np.cos(np.radians(lat))
    point = np.asarray([lng * scale_x, lat * 111.0])
    start_lng, start_lat = LOCATIONS[left]
    end_lng, end_lat = LOCATIONS[right]
    start = np.asarray([start_lng * scale_x, start_lat * 111.0])
    end = np.asarray([end_lng * scale_x, end_lat * 111.0])
    segment = end - start
    fraction = np.clip(np.dot(point - start, segment) / max(np.dot(segment, segment), 1e-12), 0, 1)
    return float(np.linalg.norm(point - (start + fraction * segment)))


def solve_dispatch(
    rainfall_rate_mm: float,
    insar_displacement_mm: float,
    start_node: str = "Hospital",
    end_node: str = "Emergency_Site",
    hazard_zones: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    graph = build_graph()
    if start_node not in graph or end_node not in graph:
        raise ValueError("start_node and end_node must be known graph locations")
    edges = list(graph.edges(data=True))
    features = []
    for index, (_, _, edge) in enumerate(edges):
        arrival = index * 5.0
        edge["arrival_minutes"] = arrival
        features.append((min(50, insar_displacement_mm * (1 + arrival * .008)), min(150, rainfall_rate_mm * (1 + arrival * .012)), edge["slope"], edge["soil"]))
    for (_, _, edge), risk in zip(edges, predict_edge_hazards(np.asarray(features))):
        edge["hazard_probability"] = round(float(risk), 4)
        edge["weight"] = inf if risk >= .85 else edge["base_time"] * (1 + 4 * float(risk) ** 2)
    for left, right, edge in edges:
        for zone in hazard_zones or []:
            try:
                zone_lng, zone_lat = float(zone["lng"]), float(zone["lat"])
                radius_km = max(0.05, float(zone.get("radius_km", 0.25)))
                zone_risk = min(1.0, max(0.0, float(zone.get("risk", 0.5))))
            except (KeyError, TypeError, ValueError):
                continue
            distance = _distance_to_edge_km(zone_lng, zone_lat, left, right)
            if distance <= radius_km:
                if zone_risk >= 0.85 and zone.get("kind") != "flood":
                    edge["weight"] = inf
                elif edge["weight"] != inf:
                    edge["weight"] *= 1 + zone_risk * 5 * (1 - distance / radius_km)
    path = nx.astar_path(
        graph,
        start_node,
        end_node,
        heuristic=_heuristic,
        weight="weight",
    )
    selected = list(zip(path, path[1:]))
    eta = sum(graph[a][b]["weight"] for a, b in selected)
    distance = sum(graph[a][b]["length_km"] for a, b in selected)
    hazards = [{"from": a, "to": b, "probability": edge["hazard_probability"], "is_impassable": edge["weight"] == inf, "projected_arrival_minutes": edge["arrival_minutes"]} for a, b, edge in edges]
    rerouted = "Junction_B" in path
    return {"path_nodes": path, "coordinates": [{"name": name, "lng": LOCATIONS[name][0], "lat": LOCATIONS[name][1]} for name in path], "total_eta_minutes": round(float(eta), 1), "total_distance_km": round(float(distance), 2), "is_rerouted": rerouted, "active_hazard_probability": max(item["probability"] for item in hazards), "hazard_scores": hazards, "alert_message": "Critical failure risk detected on the valley road. Safe highland route selected." if rerouted else "Route conditions remain within operational thresholds."}
