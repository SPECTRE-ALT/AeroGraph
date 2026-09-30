import 'package:latlong2/latlong.dart';

class RouteCoordinate {
  const RouteCoordinate({required this.name, required this.position});
  final String name;
  final LatLng position;
  factory RouteCoordinate.fromJson(Map<String, dynamic> json) => RouteCoordinate(name: json['name'] as String, position: LatLng((json['lat'] as num).toDouble(), (json['lng'] as num).toDouble()));
}

class EdgeHazard {
  const EdgeHazard({required this.from, required this.to, required this.probability, required this.impassable});
  final String from;
  final String to;
  final double probability;
  final bool impassable;
  factory EdgeHazard.fromJson(Map<String, dynamic> json) => EdgeHazard(from: json['from'] as String, to: json['to'] as String, probability: (json['probability'] as num).toDouble(), impassable: json['is_impassable'] as bool);
}

class DispatchRoute {
  const DispatchRoute({required this.pathNodes, required this.coordinates, required this.etaMinutes, required this.distanceKm, required this.rerouted, required this.activeHazard, required this.hazards, required this.alert});
  final List<String> pathNodes;
  final List<RouteCoordinate> coordinates;
  final double etaMinutes;
  final double distanceKm;
  final bool rerouted;
  final double activeHazard;
  final List<EdgeHazard> hazards;
  final String alert;
  factory DispatchRoute.fromJson(Map<String, dynamic> json) => DispatchRoute(pathNodes: List<String>.from(json['path_nodes'] as List), coordinates: (json['coordinates'] as List).map((item) => RouteCoordinate.fromJson(item as Map<String, dynamic>)).toList(), etaMinutes: (json['total_eta_minutes'] as num).toDouble(), distanceKm: (json['total_distance_km'] as num).toDouble(), rerouted: json['is_rerouted'] as bool, activeHazard: (json['active_hazard_probability'] as num).toDouble(), hazards: (json['hazard_scores'] as List).map((item) => EdgeHazard.fromJson(item as Map<String, dynamic>)).toList(), alert: json['alert_message'] as String);
}
