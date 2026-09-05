# GPS-finder-
GPS-Based Vehicle Tracking System is a full-stack application built with Flutter and Python FastAPI to track buses/vehicles in real time
GPS Vehicle Tracking Flutter App

Flutter client for the GPS vehicle tracking assessment. The frontend intentionally stays simple: the backend carries the important business logic, authentication, authorization, route assignment, and GPS data rules.

Screens

1. Login

email

password

submit button

loading state

API error message

save JWT securely after successful login

2. Home / Tracking

Show:

assigned route name/code

assigned vehicle code

vehicle status

latest latitude/longitude

latest speed

last updated time

refresh action

map

The assessment explicitly requires the logged-in user to see their assigned route, vehicle, latest GPS location, and status.

Recommended Flutter architecture

Keep the UI simple but do not put API calls directly inside widgets.

lib/
├── main.dart
├── core/
│   ├── config/
│   │   └── api_config.dart
│   ├── network/
│   │   └── api_client.dart
│   ├── storage/
│   │   └── token_storage.dart
│   └── errors/
│       └── app_exception.dart
├── features/
│   ├── auth/
│   │   ├── data/
│   │   ├── models/
│   │   ├── presentation/
│   │   └── auth_controller.dart
│   └── tracking/
│       ├── data/
│       ├── models/
│       ├── presentation/
│       └── tracking_controller.dart
└── app/
    ├── app.dart
    └── router.dart

Use a lightweight state-management solution such as Riverpod. Do not over-engineer the frontend because the assessment emphasis is the end-to-end backend flow.

API contract

Configure one base URL, for example:

http://10.0.2.2:8000/api/v1

Endpoints consumed by Flutter:

POST /auth/login
GET  /me/assignment
GET  /me/vehicle
GET  /me/vehicle/location
GET  /me/vehicle/history

Attach:

Authorization: Bearer <token>

to protected requests.

Data flow

LoginScreen
   |
   v
AuthController
   |
   v
FastAPI /auth/login
   |
   v
JWT stored securely
   |
   v
TrackingScreen
   |
   +--> /me/assignment
   +--> /me/vehicle
   +--> /me/vehicle/location
   |
   v
Map + vehicle status UI

Map implementation

For the assessment, the simplest good approach is:

route stops from the backend -> List<LatLng> -> polyline

current vehicle location -> marker

fit map bounds to the route/current marker

Google Maps or another Flutter map package can be used. Keep map rendering separate from API/state logic.

Error states

The UI should explicitly show:

loading spinner during login/data retrieval

invalid credentials

expired/invalid token -> clear token and return to login

server unavailable

no GPS data yet

empty history

unexpected server error

Important security rule

Flutter should not contain logic such as:

if (vehicleId == 'BUS-001') { ... }

The server decides what the authenticated user can access. The Flutter app only renders the response from the secured API.

Interview explanation

“The Flutter app is deliberately thin. It handles authentication, state, API communication, map rendering, loading, and error states. It does not enforce the assignment rule because client-side authorization is not trustworthy. The FastAPI backend resolves the logged-in user and returns only that user's assigned route and vehicle.”

Suggested packages

dio for HTTP

flutter_riverpod for state management

flutter_secure_storage for JWT storage

go_router for navigation

google_maps_flutter or another suitable map package

Definition of done

A reviewer should be able to:

Start the FastAPI stack.

Start Flutter.

Log in as User A and see Route A/BUS-001.

Start the GPS simulator and see the latest location update.

Log out.

Log in as User B and see Route B/BUS-002.

Confirm that User A cannot retrieve User B's vehicle through the API.
