# GPS Vehicle Tracking - Android Run Guide

This guide details exactly how to set up, build, and run the GPS Vehicle Tracking Flutter application on an Android Emulator using Android Studio, and how to start and connect to the local FastAPI + MQTT backend.

## 1. Install Flutter
1. Download the Flutter SDK for your operating system from the [official Flutter website](https://docs.flutter.dev/get-started/install).
2. Extract the archive and add the `flutter/bin` directory to your system's `PATH` environment variable.
3. Run `flutter doctor -v` in your terminal to verify the installation and identify any missing dependencies.

## 2. Install Android Studio
1. Download and install [Android Studio](https://developer.android.com/studio).
2. Follow the standard installation wizard.
3. Open Android Studio and install the **Flutter** and **Dart** plugins from the plugins marketplace.

## 3. Configure Android SDK
1. In Android Studio, go to **Tools -> SDK Manager**.
2. Under the **SDK Platforms** tab, ensure Android 14 (API level 34) is checked.
3. Under the **SDK Tools** tab, ensure the following are checked:
   - Android SDK Build-Tools
   - Android Emulator
   - Android SDK Platform-Tools
4. Click **Apply** and wait for the downloads to finish.
5. Run `flutter doctor --android-licenses` in your terminal and accept the licenses.

## 4. Create Android Emulator
1. Open Android Studio.
2. Go to **Tools -> Device Manager** (or click the Device Manager icon on the toolbar).
3. Click **Create Virtual Device**.
4. Choose a suitable device profile, for example, **Pixel 7** or **Pixel 8**.
5. Choose a compatible Android system image (e.g., API 34 / Android 14 x86_64) and download it if necessary.
6. Click **Next**, name the AVD (e.g., "Pixel_7_API_34"), and click **Finish**.

## 5. Start Emulator
1. In the Android Studio Device Manager, click the **Play** (Run) button next to your virtual device.
2. Wait for the emulator to fully boot up and display the Android home screen.

## 6. Verify `flutter devices`
1. Open your terminal.
2. Run the command:
   ```bash
   flutter devices
   ```
3. You should see your running Android emulator listed as an available target.

## 7. Start Docker Backend
1. Ensure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed and running.
2. Open a terminal in the root directory of this project (`GPS-finder-`).
3. Run the following command to start PostgreSQL, Mosquitto MQTT, FastAPI, and the GPS Simulator:
   ```bash
   docker-compose up --build -d
   ```

## 8. Verify FastAPI
1. Verify the backend containers are running without errors using `docker-compose ps` and `docker-compose logs -f backend`.
2. Open your web browser or use Postman/curl and go to:
   ```
   http://localhost:8000/api/v1/health
   ```
3. You should receive a JSON response indicating the system is healthy: `{"status": "ok", "version": "1.0.0", ...}`.

## 9. Configure Android API Base URL
The project dynamically resolves the API base URL in `frontend/lib/main.dart`:
```dart
  // Determine backend URL (10.0.2.2 for Android Emulator, localhost for Desktop/iOS/Web)
  final String backendUrl = (!kIsWeb && Platform.isAndroid)
      ? 'http://10.0.2.2:8000'
      : 'http://localhost:8000';
```
*Note: `10.0.2.2` is a special alias to your host loopback interface (localhost) from the Android emulator.*

## 10. Configure Google Maps API Key
The repository includes complete Android build scaffolding (`frontend/android/build.gradle`, `settings.gradle`, `app/build.gradle`, `AndroidManifest.xml`). To configure your Google Maps API key:

1. Create a `local.properties` file inside `frontend/android/` (or copy from `local.properties.example`):
   ```properties
   sdk.dir=C:\\Users\\Asus\\AppData\\Local\\Android\\Sdk
   flutter.sdk=C:\\path\\to\\flutter
   MAPS_API_KEY=YOUR_ACTUAL_GOOGLE_MAPS_API_KEY_HERE
   ```
2. Or set the environment variable:
   ```bash
   export GOOGLE_MAPS_API_KEY="YOUR_ACTUAL_GOOGLE_MAPS_API_KEY_HERE"
   ```
3. Gradle automatically reads `MAPS_API_KEY` (or `GOOGLE_MAPS_API_KEY`) and injects it into `AndroidManifest.xml` via manifest placeholders at build time. If absent, it defaults to `GOOGLE_MAPS_API_KEY_REQUIRED` so the project remains structurally buildable.

## 11. Run Flutter
1. In your terminal, navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Run `flutter pub get` to download dependencies.
3. Launch the app on the running emulator:
   ```bash
   flutter run
   ```
   (If multiple devices are found, specify the device ID with `-d <device_id>`).

## 12. Login Flow
1. Once the application launches, the **Login Screen** will appear.
2. Enter the development credentials for User A:
   - **Email:** `driver.a@example.com`
   - **Password:** `Password123!`
3. Click the **Log In** button.

## 13. Verify Tracking Dashboard
1. After a successful login, you will be redirected to the **Live Tracking Dashboard**.
2. Verify that it correctly displays **Route A** and assigned vehicle **BUS-001**.
3. Confirm that the Google Maps view is rendered and displaying the polyline for Route A stops.

## 14. Verify Live GPS Movement
1. The Docker stack includes a GPS simulator publishing live telemetry.
2. Keep the app open on the Tracking Screen.
3. Observe the vehicle marker on the map. It will update position automatically every 5 seconds as new coordinates flow from Mosquitto to FastAPI, and over REST to the Flutter app.

## 15. Test User B Flow
1. Tap the **Log Out** button in the app bar to return to the Login screen.
2. Login using User B's credentials:
   - **Email:** `driver.b@example.com`
   - **Password:** `Password123!`
3. Verify that the Tracking Screen now displays **Route B** and vehicle **BUS-002**.

## 16. Security & Server-Side Authorization Test
1. The backend enforces strict server-side vehicle authorization boundaries.
2. While logged in as User B (assigned to BUS-002), any attempt to access BUS-001 endpoints directly will fail with HTTP `403 Forbidden` (`VEHICLE_ACCESS_DENIED`).

## 17. Troubleshooting

* **Flutter cannot connect to FastAPI:**
  * **Symptom:** App hangs on login or shows a network error (`SocketException`).
  * **Cause:** The emulator cannot reach `10.0.2.2` or the Docker backend is not mapping port `8000` to the host.
  * **Fix:** Ensure Docker is running and `docker-compose ps` shows port 8000 exposed.

* **Google Maps is blank or gray:**
  * **Symptom:** Map area displays a plain grey background or error overlay.
  * **Cause:** The `MAPS_API_KEY` is missing or invalid in `android/local.properties`.
  * **Fix:** Ensure a valid Google Maps API Key is specified in `frontend/android/local.properties` or exported as `GOOGLE_MAPS_API_KEY`.

* **GPS marker not moving:**
  * **Symptom:** Map loads but vehicle marker remains stationary.
  * **Cause:** GPS Simulator container is stopped or Mosquitto MQTT broker connection failed.
  * **Fix:** Check backend logs (`docker-compose logs -f simulator`).
