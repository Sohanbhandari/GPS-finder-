# GPS-finder-
GPS-Based Vehicle Tracking System is a full-stack application built with Flutter and Python FastAPI to track buses/vehicles in real time
GPS Vehicle Tracking Flutter App
# GPS Vehicle Tracking System

A simple GPS vehicle tracking system built with **Flutter** and **FastAPI**.

The backend handles authentication, authorization, vehicle assignments, and GPS data. The Flutter app displays the assigned route, vehicle, and live location.

## Tech Stack

* **Flutter** — Mobile application
* **FastAPI** — Backend API
* **PostgreSQL** — Database
* **MQTT / Mosquitto** — GPS data communication
* **JWT** — Authentication
* **Docker Compose** — Local development

## Architecture

```text
GPS Device / Simulator
        |
       MQTT
        |
    Mosquitto
        |
   FastAPI Backend
        |
   PostgreSQL
        ^
        |
   Flutter App
```

## Main Flow

```text
Login
  ↓
JWT Authentication
  ↓
User Assignment
  ↓
Route + Vehicle
  ↓
Current Location / GPS History
  ↓
Flutter Map
```

## Backend

The backend is responsible for:

* User authentication
* Route and vehicle assignments
* GPS data ingestion
* Current vehicle location
* GPS history
* API authorization

### Database

```text
Users
  |
Assignments
  |
Route ─── Vehicle
           |
       GPS Points
```

## GPS Tracking

GPS data is received through MQTT.

**Topic:**

```text
vehicles/{vehicle_id}/gps
```

**Example payload:**

```json
{
  "latitude": 10.1234,
  "longitude": 76.5432,
  "speed": 42.5,
  "timestamp": "2026-09-05T12:30:00Z"
}
```

When a GPS message is received, the backend:

1. Validates the data.
2. Verifies the vehicle.
3. Stores the GPS point.
4. Updates the vehicle's latest location.

## Authorization

Authorization is handled by the **backend**, not Flutter.

```text
JWT
 ↓
User
 ↓
Assignment
 ↓
Allowed Vehicle
```

Example:

```text
User A → Route A → BUS-001
User B → Route B → BUS-002
```

A user cannot access another user's vehicle or GPS history.

## API

### Authentication

```http
POST /api/v1/auth/login
```

### User APIs

```http
GET /api/v1/me/assignment
GET /api/v1/me/vehicle
GET /api/v1/me/vehicle/location
GET /api/v1/me/vehicle/history
```

Protected requests use:

```http
Authorization: Bearer <token>
```

## Flutter App

The Flutter application contains two main screens:

### Login

* Email and password
* Loading state
* Login errors
* Secure JWT storage

### Tracking

* Assigned route
* Vehicle information
* Vehicle status
* Current location
* Speed
* Last updated time
* Map with route and vehicle marker

The Flutter app only displays data returned by the secured backend. Business rules and authorization remain on the server.

## Project Structure

### Backend

```text
backend/
├── api/
├── core/
├── models/
├── schemas/
├── services/
├── repositories/
├── mqtt/
├── db/
└── tests/
```

### Flutter

```text
frontend/
└── lib/
    ├── core/
    ├── features/
    │   ├── auth/
    │   └── tracking/
    ├── app/
    └── main.dart
```

## Testing

The important test cases include:

* Valid login
* Invalid credentials
* User assignment
* Vehicle authorization
* GPS message storage
* Latest location update
* Invalid GPS data
* Cross-user vehicle access

## Running the Project

Start the backend services with:

```bash
docker compose up --build
```

Then start the Flutter application.

A GPS simulator can be used to publish test locations and demonstrate the vehicle moving on the map.

## Definition of Done

The system is ready when:

* Users can log in.
* Each user sees their assigned route and vehicle.
* GPS data is received through MQTT.
* Current and historical locations are available.
* Vehicle movement can be shown on the Flutter map.
* Users cannot access another user's vehicle or GPS history.

## Key Principle

> **Flutter displays the data. FastAPI owns the business logic and security.**
