import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/route_model.dart';
import 'glass_overlay_card.dart';

class AppleMapHud extends StatelessWidget {
  const AppleMapHud({super.key, required this.route});
  final DispatchRoute? route;
  @override
  Widget build(BuildContext context) {
    final hazardous = route?.rerouted == true;
    final points = route?.coordinates.map((item) => item.position).toList() ?? const <LatLng>[];
    return Stack(children: [
      FlutterMap(options: const MapOptions(initialCenter: LatLng(11.260, 75.787), initialZoom: 13.0), children: [
        TileLayer(urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', subdomains: const ['a', 'b', 'c', 'd'], retinaMode: true, userAgentPackageName: 'com.example.aerograph_ai'),
        if (points.length > 1) PolylineLayer(polylines: [Polyline(points: points, color: (hazardous ? const Color(0xFFFF3B30) : const Color(0xFF007AFF)).withOpacity(.25), strokeWidth: 14), Polyline(points: points, color: hazardous ? const Color(0xFFFF3B30) : const Color(0xFF007AFF), strokeWidth: 6)]),
        MarkerLayer(markers: _markers()),
      ]),
      Positioned(top: 16, left: 16, right: 16, child: _statusCard(hazardous)),
    ]);
  }
  Widget _statusCard(bool hazardous) => GlassOverlayCard(child: Row(children: [
    Icon(hazardous ? Icons.warning_amber_rounded : Icons.verified_rounded, color: hazardous ? const Color(0xFFFF3B30) : const Color(0xFF34C759), size: 30), const SizedBox(width: 12),
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(hazardous ? 'CRITICAL PREDICTIVE REROUTE' : 'NOMINAL ROUTING', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: .6)), Text(route == null ? 'Loading telemetry…' : '${route!.etaMinutes.toStringAsFixed(1)} min  •  ${route!.distanceKm.toStringAsFixed(2)} km  •  ${(route!.activeHazard * 100).round()}% risk')]))
  ]));
  List<Marker> _markers() {
    final active = route?.coordinates ?? const <RouteCoordinate>[];
    final output = <Marker>[_marker(const LatLng(11.265, 75.790), Icons.warning_amber_rounded, const Color(0xFFFF3B30), 'Hazard')];
    for (final point in active) {
      final origin = point.name == 'Hospital';
      output.add(_marker(point.position, origin ? Icons.local_hospital : Icons.emergency, origin ? const Color(0xFF34C759) : const Color(0xFFFF3B30), point.name.replaceAll('_', ' ')));
    }
    return output;
  }
  Marker _marker(LatLng point, IconData icon, Color color, String label) => Marker(point: point, width: 104, height: 58, child: TweenAnimationBuilder<double>(tween: Tween(begin: .7, end: 1), duration: const Duration(milliseconds: 950), curve: Curves.easeInOut, builder: (context, value, child) => Transform.scale(scale: value, child: child), child: Column(children: [Container(padding: const EdgeInsets.all(6), decoration: BoxDecoration(shape: BoxShape.circle, color: color.withOpacity(.25), boxShadow: [BoxShadow(color: color, blurRadius: 16)]), child: Icon(icon, color: color)), Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold))])));
}
