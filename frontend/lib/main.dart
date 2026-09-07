import 'package:flutter/material.dart';
import 'controllers/auth_controller.dart';
import 'controllers/tracking_controller.dart';
import 'screens/login_screen.dart';
import 'screens/tracking_screen.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Instantiate services
  final apiService = ApiService(baseUrl: 'http://localhost:8000');
  final storageService = InMemoryStorageService();

  // Instantiate auth controller
  final authController = AuthController(
    apiService: apiService,
    storageService: storageService,
  );

  // Instantiate tracking controller with 401 unauthorization eviction callback
  final trackingController = TrackingController(
    apiService: apiService,
    onUnauthorized: () {
      authController.logout();
    },
  );

  // Check saved token on launch
  await authController.checkInitialAuth();

  runApp(GpsFinderApp(
    authController: authController,
    trackingController: trackingController,
  ));
}

class GpsFinderApp extends StatelessWidget {
  final AuthController authController;
  final TrackingController trackingController;

  const GpsFinderApp({
    Key? key,
    required this.authController,
    required this.trackingController,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GPS Finder',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2563EB),
          brightness: Brightness.light,
        ),
        fontFamily: 'Roboto',
      ),
      home: AnimatedBuilder(
        animation: authController,
        builder: (context, _) {
          if (authController.state.isAuthenticated) {
            return TrackingScreen(
              authController: authController,
              trackingController: trackingController,
            );
          }
          return LoginScreen(
            authController: authController,
          );
        },
      ),
    );
  }
}
