import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/api_models.dart';
import '../models/tracking_state.dart';
import '../services/api_service.dart';

/// Flutter State Controller managing Vehicle Tracking Data & Real-time State.

class TrackingController extends ChangeNotifier {
  final ApiService _apiService;
  final VoidCallback? onUnauthorized;
  Timer? _pollingTimer;

  TrackingState _state = TrackingState.initial();
  TrackingState get state => _state;

  TrackingController({
    required ApiService apiService,
    this.onUnauthorized,
  }) : _apiService = apiService;

  /// Loads full tracking dataset for authenticated user token
  Future<void> loadTrackingData(String token) async {
    _state = TrackingState.loading();
    notifyListeners();

    try {
      // 1. Fetch user's active route and vehicle assignment
      final assignment = await _apiService.getAssignment(token);

      // 2. Fetch vehicle detail metadata & computed status (ACTIVE / OFFLINE / UNKNOWN)
      final vehicle = await _apiService.getVehicle(token);

      // 3. Fetch latest live location telemetry point
      final location = await _apiService.getVehicleLocation(token);

      // 4. Fetch historical telemetry coordinates log
      final historyResponse = await _apiService.getVehicleHistory(token, limit: 50);

      _state = TrackingState.loaded(
        assignment: assignment,
        vehicle: vehicle,
        location: location,
        history: historyResponse.items,
      );
      notifyListeners();
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        // Trigger 401 token clearance callback
        stopPolling();
        onUnauthorized?.call();
        _state = TrackingState.error('Session expired. Please log in again.');
      } else if (e.error.code == 'NO_ACTIVE_ASSIGNMENT' || e.statusCode == 404) {
        // Handle empty assignment state cleanly
        _state = TrackingState.noAssignment();
      } else {
        _state = TrackingState.error(e.error.message);
      }
      notifyListeners();
    } catch (e) {
      _state = TrackingState.error('Failed to load vehicle tracking data. Please check connection.');
      notifyListeners();
    }
  }

  /// Polls backend periodically for fresh telemetry position data
  void startPolling(String token, {Duration interval = const Duration(seconds: 5)}) {
    stopPolling();
    _pollingTimer = Timer.periodic(interval, (_) async {
      if (_state.isLoaded) {
        await refreshLocation(token);
      }
    });
  }

  /// Stops telemetry polling timer
  void stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }

  /// Fetches fresh vehicle location and status quietly without triggering a full screen loader
  Future<void> refreshLocation(String token) async {
    if (!_state.isLoaded) return;
    try {
      final updatedLocation = await _apiService.getVehicleLocation(token);
      final updatedVehicle = await _apiService.getVehicle(token);

      _state = TrackingState.loaded(
        assignment: _state.assignment!,
        vehicle: updatedVehicle,
        location: updatedLocation,
        history: _state.history,
      );
      notifyListeners();
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        stopPolling();
        onUnauthorized?.call();
      }
    } catch (_) {}
  }

  /// Reset state to initial on logout
  void reset() {
    stopPolling();
    _state = TrackingState.initial();
    notifyListeners();
  }

  @override
  void dispose() {
    stopPolling();
    super.dispose();
  }
}
