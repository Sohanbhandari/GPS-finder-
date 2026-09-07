/// Type-safe API Data Transfer Objects (DTOs) for GPS Finder backend REST contract.

class RouteStop {
  final String id;
  final int sequence;
  final String name;
  final double latitude;
  final double longitude;

  RouteStop({
    required this.id,
    required this.sequence,
    required this.name,
    required this.latitude,
    required this.longitude,
  });

  factory RouteStop.fromJson(Map<String, dynamic> json) {
    return RouteStop(
      id: json['id'] as String,
      sequence: json['sequence'] as int,
      name: json['name'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );
  }
}

class RouteInfo {
  final String id;
  final String code;
  final String name;
  final String description;
  final List<RouteStop> stops;

  RouteInfo({
    required this.id,
    required this.code,
    required this.name,
    required this.description,
    required this.stops,
  });

  factory RouteInfo.fromJson(Map<String, dynamic> json) {
    final stopsJson = json['stops'] as List<dynamic>? ?? [];
    return RouteInfo(
      id: json['id'] as String,
      code: json['code'] as String,
      name: json['name'] as String,
      description: json['description'] as String? ?? '',
      stops: stopsJson.map((s) => RouteStop.fromJson(s as Map<String, dynamic>)).toList(),
    );
  }
}

class UserAssignment {
  final String id;
  final String userId;
  final bool isActive;
  final String assignedAt;
  final String updatedAt;
  final RouteInfo route;

  UserAssignment({
    required this.id,
    required this.userId,
    required this.isActive,
    required this.assignedAt,
    required this.updatedAt,
    required this.route,
  });

  factory UserAssignment.fromJson(Map<String, dynamic> json) {
    return UserAssignment(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      isActive: json['is_active'] as bool,
      assignedAt: json['assigned_at'] as String,
      updatedAt: json['updated_at'] as String,
      route: RouteInfo.fromJson(json['route'] as Map<String, dynamic>),
    );
  }
}

class VehicleDetail {
  final String id;
  final String vehicleCode;
  final String routeId;
  final String status; // ACTIVE, OFFLINE, UNKNOWN
  final double? currentLatitude;
  final double? currentLongitude;
  final double? currentSpeed;
  final String? latestRecordedAt;
  final String? lastSeenAt;

  VehicleDetail({
    required this.id,
    required this.vehicleCode,
    required this.routeId,
    required this.status,
    this.currentLatitude,
    this.currentLongitude,
    this.currentSpeed,
    this.latestRecordedAt,
    this.lastSeenAt,
  });

  factory VehicleDetail.fromJson(Map<String, dynamic> json) {
    return VehicleDetail(
      id: json['id'] as String,
      vehicleCode: json['vehicle_code'] as String,
      routeId: json['route_id'] as String,
      status: json['status'] as String,
      currentLatitude: json['current_latitude'] != null ? (json['current_latitude'] as num).toDouble() : null,
      currentLongitude: json['current_longitude'] != null ? (json['current_longitude'] as num).toDouble() : null,
      currentSpeed: json['current_speed'] != null ? (json['current_speed'] as num).toDouble() : null,
      latestRecordedAt: json['latest_recorded_at'] as String?,
      lastSeenAt: json['last_seen_at'] as String?,
    );
  }
}

class VehicleLocation {
  final String vehicleId;
  final String vehicleCode;
  final String status;
  final double? latitude;
  final double? longitude;
  final double? speed;
  final String? latestRecordedAt;
  final String? lastSeenAt;

  VehicleLocation({
    required this.vehicleId,
    required this.vehicleCode,
    required this.status,
    this.latitude,
    this.longitude,
    this.speed,
    this.latestRecordedAt,
    this.lastSeenAt,
  });

  factory VehicleLocation.fromJson(Map<String, dynamic> json) {
    return VehicleLocation(
      vehicleId: json['vehicle_id'] as String,
      vehicleCode: json['vehicle_code'] as String,
      status: json['status'] as String,
      latitude: json['latitude'] != null ? (json['latitude'] as num).toDouble() : null,
      longitude: json['longitude'] != null ? (json['longitude'] as num).toDouble() : null,
      speed: json['speed'] != null ? (json['speed'] as num).toDouble() : null,
      latestRecordedAt: json['latest_recorded_at'] as String?,
      lastSeenAt: json['last_seen_at'] as String?,
    );
  }
}

class GpsPoint {
  final String id;
  final String vehicleId;
  final double latitude;
  final double longitude;
  final double speed;
  final String recordedAt;
  final String receivedAt;

  GpsPoint({
    required this.id,
    required this.vehicleId,
    required this.latitude,
    required this.longitude,
    required this.speed,
    required this.recordedAt,
    required this.receivedAt,
  });

  factory GpsPoint.fromJson(Map<String, dynamic> json) {
    return GpsPoint(
      id: json['id'] as String,
      vehicleId: json['vehicle_id'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      speed: (json['speed'] as num).toDouble(),
      recordedAt: json['recorded_at'] as String,
      receivedAt: json['received_at'] as String,
    );
  }
}

class VehicleHistoryResponse {
  final List<GpsPoint> items;
  final String? nextCursor;
  final bool hasMore;

  VehicleHistoryResponse({
    required this.items,
    this.nextCursor,
    required this.hasMore,
  });

  factory VehicleHistoryResponse.fromJson(Map<String, dynamic> json) {
    final itemsJson = json['items'] as List<dynamic>? ?? [];
    return VehicleHistoryResponse(
      items: itemsJson.map((i) => GpsPoint.fromJson(i as Map<String, dynamic>)).toList(),
      nextCursor: json['next_cursor'] as String?,
      hasMore: json['has_more'] as bool? ?? false,
    );
  }
}

class ApiErrorDetail {
  final String code;
  final String message;

  ApiErrorDetail({required this.code, required this.message});

  factory ApiErrorDetail.fromJson(Map<String, dynamic> json) {
    return ApiErrorDetail(
      code: json['code'] as String? ?? 'UNKNOWN_ERROR',
      message: json['message'] as String? ?? 'An unexpected error occurred.',
    );
  }
}

class ApiException implements Exception {
  final int statusCode;
  final ApiErrorDetail error;

  ApiException({required this.statusCode, required this.error});

  @override
  String toString() => 'ApiException [$statusCode ${error.code}]: ${error.message}';
}
