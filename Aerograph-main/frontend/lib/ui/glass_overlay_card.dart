import 'dart:ui';
import 'package:flutter/material.dart';

class GlassOverlayCard extends StatelessWidget {
  const GlassOverlayCard({super.key, required this.child, this.padding = const EdgeInsets.all(16)});
  final Widget child;
  final EdgeInsets padding;
  @override
  Widget build(BuildContext context) => ClipRRect(borderRadius: BorderRadius.circular(22), child: BackdropFilter(filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18), child: Container(padding: padding, decoration: BoxDecoration(color: const Color(0xFF1E293B).withOpacity(.75), borderRadius: BorderRadius.circular(22), border: Border.all(color: Colors.white.withOpacity(.14))), child: child)));
}
