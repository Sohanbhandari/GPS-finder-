# GPS-finder-
GPS-Based Vehicle Tracking System is a full-stack application built with Flutter and Python FastAPI to track buses/vehicles in real time
# GPS Vehicle Tracking Backend

### Overview

A FastAPI backend for a GPS-based vehicle tracking system.

The backend handles:

* User authentication
* Route and vehicle assignments
* Live vehicle location
* GPS history
* Backend-level authorization
* MQTT-based GPS ingestion

**Database:** PostgreSQL
**Communication:** MQTT
**Authentication:** JWT

---

## 1. System Flow

```text
GPS Device / Simulator
        |
        | MQTT
        v
   Mosquitto Broker
        |
        v
  FastAPI MQTT Worker
        |
        +----> GPS History
        |
        +----> Latest Location
        |
        v
    PostgreSQL
        ^
        |
    FastAPI API
        ^
        |
    Flutter App
```

---

## 2. Backend Structure

```text
app/
├── api/            # API endpoints
├── core/           # Config & security
├── models/         # Database models
├── schemas/        # Request/response schemas
├── services/       # Business logic
├── repositories/   # Database queries
├── mqtt/           # GPS message handling
├── db/             # Database & migrations
└── tests/          # Automated tests
```

The main idea is to keep **API, business logic, database access, and MQTT processing separate**.

---

## 3. Database

### Users

* ID
* Email
* Password hash
* Name
* Role
* Active status

### Routes

* ID
* Name
* Code
* Description

### Vehicles

* ID
* Vehicle code
* Route
* Current latitude/longitude
* Speed
* Status
* Last seen

### Assignments

Connects:

```text
User → Route → Vehicle
```

### GPS Points

Stores historical:

```text
Vehicle
Latitude
Longitude
Speed
Recorded time
Received time
```

---

## 4. Authorization

This is one of the most important parts of the system.

The backend decides which vehicle a user can access.

```text
JWT
 ↓
User
 ↓
Assignment
 ↓
Route + Vehicle
 ↓
Allowed data
```

For example:

```text
User A → Route A → BUS-001
User B → Route B → BUS-002
```

User A must never be able to access BUS-002 by changing an ID in the request.

Prefer user-scoped APIs:

```text
GET /api/v1/me/assignment
GET /api/v1/me/vehicle
GET /api/v1/me/vehicle/location
GET /api/v1/me/vehicle/history
```

---

## 5. GPS / MQTT Flow

MQTT topic:

```text
vehicles/{vehicle_id}/gps
```

Example:

```json
{
  "latitude": 10.1234,
  "longitude": 76.5432,
  "speed": 42.5,
  "timestamp": "2026-09-05T12:30:00Z"
}
```

When a GPS message arrives:

1. Read the vehicle ID.
2. Validate the GPS data.
3. Check that the vehicle exists.
4. Save the GPS point to history.
5. Update the vehicle's latest location.
6. Log invalid or unknown messages.

This gives two separate read paths:

```text
Current location → vehicles table
GPS history      → gps_points table
```

---

## 6. Main APIs

### Authentication

```text
POST /api/v1/auth/login
```

### User

```text
GET /api/v1/me/assignment
GET /api/v1/me/vehicle
GET /api/v1/me/vehicle/location
GET /api/v1/me/vehicle/history
```

### Admin

```text
POST /api/v1/admin/users
POST /api/v1/admin/routes
POST /api/v1/admin/vehicles
POST /api/v1/admin/assignments
```

---

## 7. Technology Stack

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Alembic
JWT
MQTT / Mosquitto
Pytest
Docker Compose
```

---

## 8. Testing

The important tests are:

* Login works
* Invalid password is rejected
* Inactive users cannot log in
* Users receive only their assigned vehicle
* Cross-user vehicle access is blocked
* GPS messages are stored
* Latest vehicle location is updated
* Invalid GPS messages are rejected
* Unknown vehicles are not persisted

---

## 9. Definition of Done

The project is ready when:

* The backend starts successfully.
* Users can log in.
* Users can see their assigned route and vehicle.
* GPS data can be received through MQTT.
* Current location is available through the API.
* GPS history is stored.
* Users cannot access another user's vehicle.
* The complete stack can be demonstrated using Docker Compose and a GPS simulator.
