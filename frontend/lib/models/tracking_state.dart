import 'api_models.dart';

/// Tracking State Model representing Vehicle & Location Data Lifecycle.

enum TrackingStatus {
  initial,
  loading,
  loaded,
  noAssignment,
  error,
}

class TrackingState {
  final TrackingStatus status;
  final UserAssignment? assignment;
  final VehicleDetail? vehicle;
  final VehicleLocation? location;
  final List<GpsPoint> history;
  final String? errorMessage;

  const TrackingState({
    required this.status,
    this.assignment,
    this.vehicle,
    this.location,
    this.history = const [],
    this.errorMessage,
  });

  factory TrackingState.initial() {
    return const TrackingState(status: TrackingStatus.initial);
  }

  factory TrackingState.loading() {
    return const TrackingState(status: TrackingStatus.loading);
  }

  factory TrackingState.loaded({
    required UserAssignment assignment,
    required VehicleDetail vehicle,
    required VehicleLocation location,
    required List<GpsPoint> history,
  }) {
    return TrackingState(
      status: TrackingStatus.loaded,
      assignment: assignment,
      vehicle: vehicle,
      location: location,
      history: history,
    );
  }

  factory TrackingState.noAssignment() {
    return const TrackingState(status: TrackingStatus.noAssignment);
  }

  factory TrackingState.error(String errorMessage) {
    return TrackingState(status: TrackingStatus.error, errorMessage: errorMessage);
  }

  bool get isLoading => status == TrackingStatus.loading;
  bool get isLoaded => status == TrackingStatus.loaded;
  bool get hasNoAssignment => status == TrackingStatus.noAssignment;
  bool get hasError => status == TrackingStatus.error;
}
