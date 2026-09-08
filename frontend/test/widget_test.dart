import 'package:flutter_test/flutter_test.dart';
import 'package:gps_finder_flutter/controllers/auth_controller.dart';
import 'package:gps_finder_flutter/controllers/tracking_controller.dart';
import 'package:gps_finder_flutter/main.dart';
import 'package:gps_finder_flutter/services/api_service.dart';
import 'package:gps_finder_flutter/services/storage_service.dart';

void main() {
  testWidgets('GpsFinderApp renders LoginScreen on launch', (WidgetTester tester) async {
    final storage = InMemoryStorageService();
    final api = ApiService();
    final authController = AuthController(apiService: api, storageService: storage);
    final trackingController = TrackingController(apiService: api);

    await tester.pumpWidget(GpsFinderApp(
      authController: authController,
      trackingController: trackingController,
    ));

    expect(find.text('GPS Finder'), findsOneWidget);
    expect(find.text('Vehicle Tracking System'), findsOneWidget);
    expect(find.text('Log In'), findsOneWidget);
  });
}
