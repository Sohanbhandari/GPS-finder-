import 'package:flutter_test/flutter_test.dart';
import '../lib/models/api_models.dart';
import '../lib/models/auth_state.dart';
import '../lib/models/tracking_state.dart';
import '../lib/services/api_service.dart';
import '../lib/services/storage_service.dart';
import '../lib/controllers/auth_controller.dart';
import '../lib/controllers/tracking_controller.dart';

void main() {
  group('AuthController Unit Tests', () {
    test('Initial AuthState is unauthenticated', () {
      final storage = InMemoryStorageService();
      final api = ApiService();
      final controller = AuthController(apiService: api, storageService: storage);

      expect(controller.state.status, equals(AuthStatus.unauthenticated));
      expect(controller.state.isAuthenticated, isFalse);
    });

    test('Login validation fails on empty credentials', () async {
      final storage = InMemoryStorageService();
      final api = ApiService();
      final controller = AuthController(apiService: api, storageService: storage);

      final success = await controller.login('', '');
      expect(success, isFalse);
      expect(controller.state.status, equals(AuthStatus.failure));
      expect(controller.state.errorMessage, contains('cannot be empty'));
    });
  });

  group('TrackingState Unit Tests', () {
    test('Initial TrackingState is initial', () {
      final api = ApiService();
      final controller = TrackingController(apiService: api);

      expect(controller.state.status, equals(TrackingStatus.initial));
      expect(controller.state.isLoaded, isFalse);
    });

    test('Polling timer start and stop lifecycle', () {
      final api = ApiService();
      final controller = TrackingController(apiService: api);

      controller.startPolling('test_token', interval: const Duration(milliseconds: 100));
      controller.stopPolling();
      // Verifies startPolling and stopPolling complete without throw
      expect(controller.state.status, equals(TrackingStatus.initial));
    });
  });
}
