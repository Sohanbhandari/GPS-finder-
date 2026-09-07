# GPS Vehicle Tracking System - Flutter Mobile Client

Production-grade **Flutter** mobile application providing real-time GPS vehicle tracking, Google Maps polyline rendering, and server-side authorized vehicle status monitoring.

---

## 1. Prerequisites & Environment Setup

- **Flutter SDK**: `>=3.0.0 <4.0.0`
- **Dart SDK**: `^3.0.0`
- **Dependencies**: `http: ^1.2.0`, `google_maps_flutter: ^2.5.0`

### Installation:
```bash
cd frontend
flutter pub get
```

---

## 2. API Connection Configuration

The application communicates with the FastAPI backend via [`ApiService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/api_service.dart):

```dart
// Android Emulator
final apiService = ApiService(baseUrl: 'http://10.0.2.2:8000');

// iOS Simulator / Desktop / Web
final apiService = ApiService(baseUrl: 'http://localhost:8000');
```

---

## 3. Secure Token Storage & Auth Architecture

- **Token Management**: JWT tokens acquired during login are saved using [`StorageService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/storage_service.dart).
- **Automatic Authorization Header**: All HTTP requests in `ApiService` automatically attach `Authorization: Bearer <token>`.
- **401 Unauthorized Eviction**: If background location polling encounters HTTP 401 (token expired/invalid), [`TrackingController`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/tracking_controller.dart) triggers `onUnauthorized()`, clearing stored tokens and reactively redirecting to [`LoginScreen`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/screens/login_screen.dart).

---

## 4. Google Maps & Polyline Setup

- **Maps Plugin**: Uses `google_maps_flutter`.
- **API Key Setup (Android)**: Add Google Maps API key to `android/app/src/main/AndroidManifest.xml`:
  ```xml
  <meta-data
      android:name="com.google.android.geo.API_KEY"
      android:value="YOUR_GOOGLE_MAPS_API_KEY_HERE"/>
  ```
- **Polyline Rendering**: Polyline waypoints are built strictly from route stops returned by `GET /api/v1/me/assignment`, sorted by `sequence ASC` to prevent polyline crisscrossing on the map.

---

## 5. State Management & Polling Flow

- **Pattern**: Clean Controller-State pattern using `ChangeNotifier`.
- **Polling Loop**: [`TrackingController`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/tracking_controller.dart) manages a 5-second periodic `Timer` that calls `GET /api/v1/me/vehicle/location` to fetch real-time updates and update vehicle marker position on the map.

---

## 6. Automated Testing

Run Flutter unit and widget tests:
```bash
cd frontend
flutter test
```

---

## 7. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `SocketException: Connection Refused` | Android Emulator cannot reach host machine `localhost`. | Change `baseUrl` to `http://10.0.2.2:8000`. |
| `Google Maps Blank / Gray Screen` | Missing or invalid Google Maps API Key in AndroidManifest.xml. | Ensure valid Maps API key is configured in Android manifest. |
| `Auto-Logout on Launch` | Saved JWT token expired or backend database re-seeded. | Re-enter credentials (`driver_a@example.com` / `Password123!`) on login screen. |
