import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/api_models.dart';

/// Pure Dart REST API Service communicating with the FastAPI backend security boundary.

class ApiService {
  final String baseUrl;
  final http.Client client;

  ApiService({
    this.baseUrl = 'http://localhost:8000',
    http.Client? client,
  }) : client = client ?? http.Client();

  Map<String, String> _headers([String? token]) {
    final map = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      map['Authorization'] = 'Bearer $token';
    }
    return map;
  }

  ApiException _handleError(http.Response response) {
    try {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      if (json.containsKey('error') && json['error'] is Map<String, dynamic>) {
        final errorDetail = ApiErrorDetail.fromJson(json['error'] as Map<String, dynamic>);
        return ApiException(statusCode: response.statusCode, error: errorDetail);
      }
    } catch (_) {}
    return ApiException(
      statusCode: response.statusCode,
      error: ApiErrorDetail(
        code: 'HTTP_${response.statusCode}',
        message: 'HTTP Request failed with status ${response.statusCode}.',
      ),
    );
  }

  /// POST /api/v1/auth/login
  Future<String> login(String email, String password) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/auth/login');
      final response = await client.post(
        uri,
        headers: _headers(),
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return json['access_token'] as String;
      }
      throw _handleError(response);
    } on SocketException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Unable to connect to backend server: ${e.message}'),
      );
    } on http.ClientException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Network request failed: ${e.message}'),
      );
    }
  }

  /// GET /api/v1/me/assignment
  Future<UserAssignment> getAssignment(String token) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/me/assignment');
      final response = await client.get(uri, headers: _headers(token));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return UserAssignment.fromJson(json);
      }
      throw _handleError(response);
    } on SocketException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Network error: ${e.message}'),
      );
    }
  }

  /// GET /api/v1/me/vehicle
  Future<VehicleDetail> getVehicle(String token) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/me/vehicle');
      final response = await client.get(uri, headers: _headers(token));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return VehicleDetail.fromJson(json);
      }
      throw _handleError(response);
    } on SocketException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Network error: ${e.message}'),
      );
    }
  }

  /// GET /api/v1/me/vehicle/location
  Future<VehicleLocation> getVehicleLocation(String token) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/me/vehicle/location');
      final response = await client.get(uri, headers: _headers(token));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return VehicleLocation.fromJson(json);
      }
      throw _handleError(response);
    } on SocketException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Network error: ${e.message}'),
      );
    }
  }

  /// GET /api/v1/me/vehicle/history
  Future<VehicleHistoryResponse> getVehicleHistory(
    String token, {
    int limit = 50,
    String? fromTime,
    String? toTime,
    String? cursor,
  }) async {
    try {
      final queryParams = <String, String>{'limit': limit.toString()};
      if (fromTime != null) queryParams['from'] = fromTime;
      if (toTime != null) queryParams['to'] = toTime;
      if (cursor != null) queryParams['cursor'] = cursor;

      final uri = Uri.parse('$baseUrl/api/v1/me/vehicle/history').replace(queryParameters: queryParams);
      final response = await client.get(uri, headers: _headers(token));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return VehicleHistoryResponse.fromJson(json);
      }
      throw _handleError(response);
    } on SocketException catch (e) {
      throw ApiException(
        statusCode: 503,
        error: ApiErrorDetail(code: 'NETWORK_ERROR', message: 'Network error: ${e.message}'),
      );
    }
  }
}
