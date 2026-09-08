# GPS Vehicle Tracking System - Flutter Mobile Client

Production-grade **Flutter** mobile application providing real-time GPS vehicle tracking, Google Maps polyline rendering, and server-side authorized vehicle status monitoring.

---

## 1. Prerequisites & Environment Setup

- **Flutter SDK**: `>=3.0.0 <4.0.0`
- **Dart SDK**: `^3.0.0`
- **Android SDK**: API level 34 (compileSdk 34, minSdk 21)
- **Dependencies**: `http: ^1.2.0`, `google_maps_flutter: ^2.5.0`

### Installation:
```bash
cd frontend
flutter pub get
```

---

## 2. Android Build Scaffolding & Configuration

The Android platform files are located in `frontend/android/`:

- **Root Build Script**: `frontend/android/build.gradle` (Configured with AGP 8.1.0 & Kotlin 1.8.22)
- **Settings Script**: `frontend/android/settings.gradle`
- **App Module Build Script**: `frontend/android/app/build.gradle`
- **Manifest**: `frontend/android/app/src/main/AndroidManifest.xml`
- **Kotlin Entry Point**: `frontend/android/app/src/main/kotlin/com/example/gps_finder_flutter/MainActivity.kt`

---

## 3. Secure Google Maps API Key Configuration

The Google Maps API key is injected dynamically into `AndroidManifest.xml` at build time via Gradle manifest placeholders. **Secrets are never committed to source control.**

### Setting Up Your Maps API Key:
1. Create a `local.properties` file inside `frontend/android/` (or copy from `local.properties.example`):
   ```properties
   sdk.dir=C:\\Users\\Asus\\AppData\\Local\\Android\\Sdk
   flutter.sdk=C:\\path\\to\\flutter
   MAPS_API_KEY=YOUR_ACTUAL_GOOGLE_MAPS_API_KEY_HERE
   ```
2. Alternatively, set an environment variable before building:
   ```bash
   export GOOGLE_MAPS_API_KEY="YOUR_ACTUAL_GOOGLE_MAPS_API_KEY_HERE"
   ```
3. If no key is configured, Gradle automatically falls back to `GOOGLE_MAPS_API_KEY_REQUIRED` so the build succeeds structurally while preventing fake keys from being committed.

---

## 4. API Connection Configuration

The application communicates with the FastAPI backend via [`ApiService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/api_service.dart):

```dart
// Android Emulator (automatically detected)
final apiService = ApiService(baseUrl: 'http://10.0.2.2:8000');

// iOS Simulator / Desktop / Web
final apiService = ApiService(baseUrl: 'http://localhost:8000');
```

---

## 5. Secure Token Storage & Auth Architecture

- **Token Management**: JWT tokens acquired during login are saved using [`StorageService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/storage_service.dart).
- **Automatic Authorization Header**: All HTTP requests in `ApiService` automatically attach `Authorization: Bearer <token>`.
- **401 Unauthorized Eviction**: If background location polling encounters HTTP 401 (token expired/invalid), [`TrackingController`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/tracking_controller.dart) triggers `onUnauthorized()`, clearing stored tokens and reactively redirecting to [`LoginScreen`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/screens/login_screen.dart).

---

## 6. Google Maps & Polyline Setup

- **Maps Plugin**: Uses `google_maps_flutter`.
- **Polyline Rendering**: Polyline waypoints are built strictly from route stops returned by `GET /api/v1/me/assignment`, sorted by `sequence ASC` to prevent polyline crisscrossing on the map.
- **Vehicle Telemetry Marker**: The vehicle marker position is updated dynamically using backend telemetry points fetched via `GET /api/v1/me/vehicle/location`. Phone/device GPS is explicitly disabled (`myLocationEnabled: false`).

---

## 7. Running the Application on Android Emulator

1. Start your local FastAPI backend (via Docker Compose or bare-metal Uvicorn):
   ```bash
   docker-compose up --build -d
   ```
2. Launch your Android Emulator in Android Studio (Device Manager -> Start Device).
3. Verify the emulator is detected:
   ```bash
   flutter devices
   ```
4. Run the Flutter app:
   ```bash
   cd frontend
   flutter pub get
   flutter run
   ```

---

## 8. Automated Testing

Run Flutter unit and widget tests:
```bash
cd frontend
flutter test
```

---

## 9. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `SocketException: Connection Refused` | Android Emulator cannot reach host machine `localhost`. | Ensure `baseUrl` is set to `http://10.0.2.2:8000`. |
| `Google Maps Blank / Gray Screen` | Missing or invalid Google Maps API Key. | Set `MAPS_API_KEY` in `android/local.properties` or environment variable. |
| `Auto-Logout on Launch` | Saved JWT token expired or backend database re-seeded. | Re-enter credentials (`driver.a@example.com` / `Password123!`) on login screen. |
| `Gradle Build Error` | Missing Android SDK path in `local.properties`. | Ensure `sdk.dir` is specified in `android/local.properties`. |
