import 'package:flutter/material.dart';
import 'glass_overlay_card.dart';

class TelemetryControls extends StatelessWidget {
  const TelemetryControls({super.key, required this.rainfall, required this.insar, required this.busy, required this.onRainfall, required this.onInsar, required this.onSync});
  final double rainfall;
  final double insar;
  final bool busy;
  final ValueChanged<double> onRainfall;
  final ValueChanged<double> onInsar;
  final VoidCallback onSync;
  @override
  Widget build(BuildContext context) => GlassOverlayCard(child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('SIMULATION CONTROLS', style: TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1.2)), const SizedBox(height: 14),
    Text('Satellite Rainfall  ${rainfall.round()} mm/hr'), Slider(value: rainfall, min: 0, max: 150, divisions: 150, onChanged: onRainfall),
    Text('InSAR Terrain Shift  ${insar.round()} mm'), Slider(value: insar, min: 0, max: 50, divisions: 50, onChanged: onInsar),
    const SizedBox(height: 8), SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: busy ? null : onSync, icon: busy ? const SizedBox.square(dimension: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.sync), label: const Text('Sync Satellite Feeds'))),
  ]));
}
