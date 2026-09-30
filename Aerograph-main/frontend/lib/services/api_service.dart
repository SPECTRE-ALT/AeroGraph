import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/route_model.dart';

class ApiService {
  const ApiService({this.baseUrl = 'http://127.0.0.1:8000'});
  final String baseUrl;
  Future<DispatchRoute> predictDispatch({required double rainfall, required double insar}) async {
    final response = await http.post(Uri.parse('$baseUrl/api/v1/predict-dispatch'), headers: const {'Content-Type': 'application/json'}, body: jsonEncode({'rainfall_rate_mm': rainfall, 'insar_displacement_mm': insar})).timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) throw Exception('Dispatch request failed (${response.statusCode})');
    return DispatchRoute.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }
}
