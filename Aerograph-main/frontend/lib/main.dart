import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'models/route_model.dart';
import 'services/api_service.dart';
import 'ui/apple_map_hud.dart';
import 'ui/telemetry_controls.dart';

void main() => runApp(const AerographApp());

class AerographApp extends StatelessWidget {
  const AerographApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(debugShowCheckedModeBanner: false, theme: ThemeData.dark(useMaterial3: true).copyWith(scaffoldBackgroundColor: const Color(0xFF0B0F19), textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme), colorScheme: const ColorScheme.dark(primary: Color(0xFF007AFF))), home: const DispatchDashboard());
}

class DispatchDashboard extends StatefulWidget {
  const DispatchDashboard({super.key});
  @override
  State<DispatchDashboard> createState() => _DispatchDashboardState();
}

class _DispatchDashboardState extends State<DispatchDashboard> {
  final _api = const ApiService();
  double _rainfall = 25, _insar = 8;
  bool _busy = false;
  String? _error;
  DispatchRoute? _route;
  @override
  void initState() { super.initState(); _sync(); }
  Future<void> _sync() async {
    setState(() { _busy = true; _error = null; });
    HapticFeedback.lightImpact();
    try { final route = await _api.predictDispatch(rainfall: _rainfall, insar: _insar); if (mounted) setState(() => _route = route); } catch (error) { if (mounted) setState(() => _error = 'Connection unavailable: $error'); } finally { if (mounted) setState(() => _busy = false); }
  }
  @override
  Widget build(BuildContext context) => Scaffold(body: SafeArea(child: Stack(children: [
    Positioned.fill(child: ClipRRect(borderRadius: BorderRadius.circular(20), child: AppleMapHud(route: _route))),
    Positioned(left: 16, right: 16, bottom: 16, child: TelemetryControls(rainfall: _rainfall, insar: _insar, busy: _busy, onRainfall: (value) => setState(() => _rainfall = value), onInsar: (value) => setState(() => _insar = value), onSync: _sync)),
    if (_error != null) Positioned(top: 112, left: 16, right: 16, child: Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: Color(0xFFFF3B30)))),
  ])));
}
