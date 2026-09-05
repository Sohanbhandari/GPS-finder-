# GPS Vehicle Tracking System - Technical Documentation & Master Specification

> **Primary Reference**: [README.md](README.md)  
> **Core Architectural Principle**: *"Flutter is the presentation client; FastAPI is the authoritative source of truth for authentication, authorization, assignment integrity, vehicle status calculation, and GPS telemetry business logic; PostgreSQL stores current state and historical tracking data; MQTT carries telemetry."*

---

## Table of Contents

1. [System Architecture & Flow](#1-system-architecture--flow)
2. [Assignment Model & Integrity Rules](#2-assignment-model--integrity-rules)
3. [GPS Telemetry & Timestamp Rules](#3-gps-telemetry--timestamp-rules)
4. [Out-of-Order Telemetry & Latest State Engine](#4-out-of-order-telemetry--latest-state-engine)
5. [Vehicle Status Engine](#5-vehicle-status-engine)
6. [Backend Architecture (FastAPI)](#6-backend-architecture-fastapi)
7. [PostgreSQL Database Design](#7-postgresql-database-design)
8. [Authentication & Server-Side Authorization](#8-authentication--server-side-authorization)
9. [REST API Specifications & History Contract](#9-rest-api-specifications--history-contract)
10. [Standard API Error Format](#10-standard-api-error-format)
11. [Frontend Architecture (Flutter) & Map Rendering](#11-frontend-architecture-flutter--map-rendering)
12. [Environment, Secrets & Credential Management](#12-environment-secrets--credential-management)
13. [AI Implementation & Clarification Rule](#13-ai-implementation--clarification-rule)
14. [Development vs. Production Deployment](#14-development-vs-production-deployment)
15. [Debugging & Data Flow Traceability](#15-debugging--data-flow-traceability)
16. [Testing Strategy & Test Matrix](#16-testing-strategy--test-matrix)
17. [Documentation & Traceability Architecture](#17-documentation--traceability-architecture)
18. [Definition of Done Checklist](#18-definition-of-done-checklist)

---

## 1. System Architecture & Flow

### 1.1 High-Level Topology Diagram
```text
┌──────────────────────────────────────────────────────────┐
│                   Flutter Mobile App                     │
│               Login / Tracking UI / Map                  │
└────────────────────────────┬─────────────────────────────┘
                             │ HTTPS + JWT Bearer
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│         Routers ──► Services ──► Repositories            │
└──────────────┬─────────────────────────────┬─────────────┘
               │ Async SQL                   │ MQTT Protocol
               ▼                             ▼
┌──────────────────────────┐   ┌───────────────────────────┐
│   PostgreSQL Database    │   │  Mosquitto MQTT Broker    │
│ Users/Routes/GPS History │   └─────────────▲─────────────┘
└──────────────────────────┘                 │ Telemetry
                                             │
                               ┌─────────────┴─────────────┐
                               │   GPS Simulator / Hardware│
                               └───────────────────────────┘
```

### 1.2 Data Pipeline
1. **Authentication**: User logs in via Flutter (`POST /api/v1/auth/login`). FastAPI verifies `users.password_hash` and issues a signed JWT access token containing the `sub` claim (User UUID).
2. **Active Assignment Resolution**: Flutter queries `GET /api/v1/me/assignment`. FastAPI queries `assignments` where `user_id = current_user.id` AND `is_active = TRUE`, resolving the assigned `route_id` and `vehicle_id`.
3. **Telemetry Ingestion**: The vehicle or GPS simulator publishes telemetry to `vehicles/{vehicle_code}/gps`. The FastAPI MQTT subscriber parses the payload, validates structural bounds, appends an immutable row to `gps_points`, and evaluates whether to update `vehicles` location.
4. **Map Rendering**: Flutter queries `/api/v1/me/vehicle/location` and `/api/v1/me/vehicle/history` to render the vehicle marker and historical polyline on Google Maps.

---

## 2. Assignment Model & Integrity Rules

### 2.1 Active vs. Historical Assignments
The assignment system distinguishes between active and historical assignments to preserve record history:

- **Attributes**:
  - `id`: UUID (Primary Key)
  - `user_id`: UUID (Foreign Key $\rightarrow$ `users.id`)
  - `route_id`: UUID (Foreign Key $\rightarrow$ `routes.id`)
  - `vehicle_id`: UUID (Foreign Key $\rightarrow$ `vehicles.id`)
  - `is_active`: BOOLEAN (Default: `TRUE`)
  - `assigned_at`: TIMESTAMPTZ (Timestamp when assignment was created)
  - `updated_at`: TIMESTAMPTZ (Timestamp when assignment status changed)

- **Rules**:
  1. A user MAY have multiple historical assignment records (`is_active = FALSE`), but MUST have **at most one ACTIVE assignment** (`is_active = TRUE`).
  2. Database constraint: `CREATE UNIQUE INDEX idx_unique_active_user_assignment ON assignments(user_id) WHERE is_active = TRUE;`
  3. All `/api/v1/me/*` endpoints resolve ONLY active assignments (`is_active = TRUE`).
  4. If a user has no active assignment, the backend MUST reject data access with `HTTP 404 Not Found` (or `HTTP 403 Forbidden` for vehicle endpoints) carrying error code `NO_ACTIVE_ASSIGNMENT`.

### 2.2 Assignment Integrity Invariant
- **Invariant**: `assignment.route_id` MUST equal `vehicle.route_id`.
- **Validation**: The backend service layer MUST verify that the assigned `vehicle_id` actually belongs to `assignment.route_id` prior to inserting or activating an assignment row.
- **Rejection**: If a client or seed script attempts to assign `User A → Route A → Vehicle B (belonging to Route B)`, the backend MUST reject the transaction with `HTTP 400 Bad Request` (`ASSIGNMENT_INTEGRITY_VIOLATION`).

---

## 3. GPS Telemetry & Timestamp Rules

To eliminate ambiguity, telemetry processing distinguishes two explicit timestamp fields across all database schemas, MQTT payloads, API responses, and services:

1. **`recorded_at`**: The UTC timestamp generated by the vehicle hardware or GPS simulator indicating when the coordinate was measured at the source.
2. **`received_at`**: The UTC timestamp generated by the FastAPI backend when the telemetry packet was ingested at the server.

### MQTT Envelope & Schema Definition
- **Topic**: `vehicles/{vehicle_code}/gps`
- **JSON Payload Contract**:
```json
{
  "latitude": 10.1234,
  "longitude": 76.5432,
  "speed": 42.5,
  "timestamp": "2026-09-05T12:30:00Z"
}
```
*Note: In the incoming MQTT payload, `"timestamp"` maps directly to domain attribute `recorded_at`.*

---

## 4. Out-of-Order Telemetry & Latest State Engine

Network delays can cause telemetry messages to arrive out of order. The backend enforces strict atomic rules to preserve data integrity:

1. **Immutable History**: EVERY valid incoming GPS telemetry record MUST be inserted into the `gps_points` table as an append-only historical event (storing both `recorded_at` and server `received_at`).
2. **Latest Location Snapshot**: The `vehicles` table maintains denormalized columns (`current_latitude`, `current_longitude`, `current_speed`, `latest_recorded_at`, `last_seen_at`) for $O(1)$ live map rendering.
3. **Out-of-Order Guard Rule**:
   - When a new GPS message arrives with `recorded_at`:
   - If `recorded_at >= vehicles.latest_recorded_at` (or `latest_recorded_at IS NULL`): Update `vehicles.current_latitude`, `vehicles.current_longitude`, `vehicles.current_speed`, `vehicles.latest_recorded_at = recorded_at`, and `vehicles.last_seen_at = received_at`.
   - If `recorded_at < vehicles.latest_recorded_at`: Save the point in `gps_points` history, but **DO NOT overwrite `vehicles` current location state**. Stale telemetry must never move the vehicle's current location backwards in time.
4. **Atomicity**: Telemetry processing (history insert + state evaluation) executes inside a single database transaction.

---

## 5. Vehicle Status Engine

Vehicle status is calculated authoritatively by FastAPI based on a configurable threshold. Flutter MUST NOT invent independent status calculation rules.

### Status Definitions
- **`UNKNOWN`**: No valid GPS telemetry has ever been received for this vehicle (`latest_recorded_at IS NULL`).
- **`ACTIVE`**: Telemetry has been received within the configured freshness threshold (`(NOW() - last_seen_at) <= ONLINE_THRESHOLD_SECONDS`).
- **`OFFLINE`**: Telemetry exists, but the latest telemetry is older than the freshness threshold (`(NOW() - last_seen_at) > ONLINE_THRESHOLD_SECONDS`).

### Configuration
- `ONLINE_THRESHOLD_SECONDS`: Integer environment variable (Default: `60` seconds).

---

## 6. Backend Architecture (FastAPI)

The backend follows **Layered Clean Architecture** with strict Separation of Concerns:

```text
backend/
├── app/
│   ├── main.py                   # FastAPI entrypoint & app factory
│   ├── core/                     # Configuration, JWT security, dependencies
│   │   ├── config.py             # BaseSettings loading from environment
│   │   ├── security.py           # Passlib bcrypt hashing & JWT token encoding
│   │   └── dependencies.py       # FastAPI HTTP Bearer & current_user resolver
│   ├── db/                       # Session management & declarative base
│   │   ├── session.py            # Async SQLAlchemy engine & sessionmaker
│   │   └── base.py               # Base ORM class
│   ├── models/                   # ORM Entity Models
│   │   ├── user.py               # User model
│   │   ├── route.py              # Route model
│   │   ├── route_stop.py         # RouteStop model
│   │   ├── vehicle.py            # Vehicle model (with denormalized latest state)
│   │   ├── assignment.py         # Assignment model (with is_active, assigned_at)
│   │   └── gps_point.py          # GPSPoint append-only model
│   ├── schemas/                  # Pydantic Validation Schemas (DTOs)
│   │   ├── auth.py               # Login request/response DTOs
│   │   ├── route.py              # Route and RouteStop DTOs
│   │   ├── vehicle.py            # Vehicle DTOs
│   │   ├── assignment.py         # Assignment DTOs
│   │   ├── gps.py                # GPS Telemetry DTOs
│   │   └── common.py             # Error response DTOs
│   ├── repositories/             # Data Access Layer (Raw SQL / ORM Queries)
│   │   ├── user_repository.py
│   │   ├── assignment_repository.py
│   │   ├── vehicle_repository.py
│   │   └── gps_repository.py
│   ├── services/                 # Domain Business Logic Layer
│   │   ├── auth_service.py       # User auth & JWT issuance
│   │   ├── assignment_service.py # Active assignment resolution & integrity checks
│   │   ├── vehicle_service.py    # Vehicle status calculation & location queries
│   │   └── gps_service.py        # Out-of-order evaluation & atomic telemetry ingestion
│   ├── api/                      # HTTP Router Controllers
│   │   └── v1/
│   │       ├── router.py         # Main v1 router aggregator
│   │       ├── auth.py           # /api/v1/auth endpoints
│   │       └── me.py             # /api/v1/me endpoints
│   └── mqtt/                     # Telemetry Transport Adapter
│       ├── client.py             # Async MQTT client connection manager
│       └── handlers.py           # Topic routing & payload parsing
├── migrations/                   # Alembic database migrations
├── tests/                        # Pytest suite
├── scripts/                      # DB Seed scripts
│   └── seed.py
├── simulator/                    # Telemetry simulator script
│   └── gps_simulator.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. PostgreSQL Database Design

### 7.1 Schema Specifications

#### `users`
- `id`: UUID (PK, Default: `gen_random_uuid()`)
- `email`: VARCHAR(255) (UNIQUE, NOT NULL)
- `password_hash`: VARCHAR(255) (NOT NULL)
- `full_name`: VARCHAR(255) (NOT NULL)
- `role`: VARCHAR(50) (Default: `'driver'`)
- `is_active`: BOOLEAN (Default: `TRUE`)
- `created_at`: TIMESTAMPTZ (Default: `NOW()`)

#### `routes`
- `id`: UUID (PK)
- `code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `name`: VARCHAR(255) (NOT NULL)
- `description`: TEXT
- `created_at`: TIMESTAMPTZ (Default: `NOW()`)

#### `route_stops`
- `id`: UUID (PK)
- `route_id`: UUID (FK $\rightarrow$ `routes.id`, NOT NULL)
- `sequence`: INT (NOT NULL, Polyline order index)
- `name`: VARCHAR(255) (NOT NULL)
- `latitude`: DOUBLE PRECISION (NOT NULL)
- `longitude`: DOUBLE PRECISION (NOT NULL)
- *Indexes*: `INDEX idx_route_stops_seq (route_id, sequence ASC)`

#### `vehicles`
- `id`: UUID (PK)
- `vehicle_code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `route_id`: UUID (FK $\rightarrow$ `routes.id`, NOT NULL)
- `current_latitude`: DOUBLE PRECISION (NULLABLE)
- `current_longitude`: DOUBLE PRECISION (NULLABLE)
- `current_speed`: DOUBLE PRECISION (NULLABLE)
- `latest_recorded_at`: TIMESTAMPTZ (NULLABLE, Out-of-order telemetry guard)
- `last_seen_at`: TIMESTAMPTZ (NULLABLE, Server receipt timestamp)
- `created_at`: TIMESTAMPTZ (Default: `NOW()`)
- *Indexes*: `INDEX idx_vehicles_route (route_id)`

#### `assignments`
- `id`: UUID (PK)
- `user_id`: UUID (FK $\rightarrow$ `users.id`, NOT NULL)
- `route_id`: UUID (FK $\rightarrow$ `routes.id`, NOT NULL)
- `vehicle_id`: UUID (FK $\rightarrow$ `vehicles.id`, NOT NULL)
- `is_active`: BOOLEAN (Default: `TRUE`, NOT NULL)
- `assigned_at`: TIMESTAMPTZ (Default: `NOW()`)
- `updated_at`: TIMESTAMPTZ (Default: `NOW()`)
- *Indexes*:
  - `CREATE UNIQUE INDEX idx_unique_active_user ON assignments(user_id) WHERE is_active = TRUE;`
  - `INDEX idx_assignments_route_vehicle (route_id, vehicle_id)`

#### `gps_points`
- `id`: UUID (PK)
- `vehicle_id`: UUID (FK $\rightarrow$ `vehicles.id`, NOT NULL)
- `latitude`: DOUBLE PRECISION (NOT NULL)
- `longitude`: DOUBLE PRECISION (NOT NULL)
- `speed`: DOUBLE PRECISION (NOT NULL)
- `recorded_at`: TIMESTAMPTZ (NOT NULL, Source timestamp)
- `received_at`: TIMESTAMPTZ (NOT NULL, Server receipt timestamp)
- *Indexes*: `INDEX idx_gps_points_vehicle_time (vehicle_id, recorded_at DESC, id DESC)`

---

## 8. Authentication & Server-Side Authorization

### 8.1 Authorization Architecture
1. **Client Identity**: The client passes `Authorization: Bearer <token>` on all protected API requests.
2. **Identity Resolution**: FastAPI extracts and decodes the JWT `sub` claim to retrieve `current_user`.
3. **Active Assignment Scoping**: Normal `/api/v1/me/*` endpoints query the database for the active assignment mapped to `current_user.id`.
4. **Client Parameter Tampering Prevention**: Endpoints do NOT accept client-supplied `vehicle_id` or `route_id` query parameters for normal tracking flows. The allowed vehicle is determined exclusively on the server.
5. **Unauthorized Access Enforcement**: If an administrative or explicit endpoint receives a request for a vehicle not belonging to the user's active assignment, FastAPI returns `HTTP 403 Forbidden` with code `VEHICLE_ACCESS_DENIED`.

### 8.2 Interview Authorization Case Study
- **Setup**:
  - `User A` $\rightarrow$ Active Assignment: `BUS-001` (Route A)
  - `User B` $\rightarrow$ Active Assignment: `BUS-002` (Route B)
- **Scenario**: `User B` attempts to send an explicit HTTP request targeting `BUS-001`.
- **Backend Result**: `HTTP 403 Forbidden` carrying JSON body:
  ```json
  {
    "error": {
      "code": "VEHICLE_ACCESS_DENIED",
      "message": "You are not authorized to access this vehicle."
    }
  }
  ```

---

## 9. REST API Specifications & History Contract

Detailed endpoint definitions are maintained in `docs/API_CONTRACT.md`. Summary contracts:

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | None | Authenticates credentials; returns JWT access token. |
| `GET` | `/api/v1/me/assignment` | JWT | Resolves user's active assignment (`route` and `vehicle`). |
| `GET` | `/api/v1/me/vehicle` | JWT | Returns assigned vehicle metadata and computed status (`ACTIVE`, `OFFLINE`, `UNKNOWN`). |
| `GET` | `/api/v1/me/vehicle/location` | JWT | Returns assigned vehicle's current GPS location, speed, `recorded_at`, and `last_seen_at`. |
| `GET` | `/api/v1/me/vehicle/history` | JWT | Returns historical telemetry data points with range and pagination options. |
| `GET` | `/api/v1/health` | None | System health check endpoint. |

### 9.1 History Query Contract (`GET /api/v1/me/vehicle/history`)
- **Query Parameters**:
  - `from`: ISO 8601 TIMESTAMPTZ string (Optional, e.g., `2026-09-05T00:00:00Z`)
  - `to`: ISO 8601 TIMESTAMPTZ string (Optional, e.g., `2026-09-05T23:59:59Z`)
  - `limit`: Integer (Optional, Default: `50`, Max: `200`)
  - `cursor`: UUID string for keyset pagination (Optional)
- **Validation Rules**:
  - `from` must be less than or equal to `to`.
  - `limit` is clamped to maximum `200` server-side.
- **Sorting**: Deterministic ordering by `recorded_at DESC, id DESC`.

---

## 10. Standard API Error Format

All API errors return a uniform JSON error payload across all endpoints:

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable explanation of the error."
  }
}
```

### Common Error Codes
- `INVALID_CREDENTIALS` (HTTP 401): Password or email incorrect.
- `UNAUTHORIZED` (HTTP 401): Missing or expired JWT token.
- `VEHICLE_ACCESS_DENIED` (HTTP 403): User not authorized for target vehicle.
- `NO_ACTIVE_ASSIGNMENT` (HTTP 404): Authenticated user has no active assignment.
- `ASSIGNMENT_INTEGRITY_VIOLATION` (HTTP 400): Vehicle does not belong to target route.
- `VALIDATION_ERROR` (HTTP 422): Request payload or parameters malformed.

*Security Constraint*: Server stack traces, raw SQL exceptions, passwords, or secrets MUST NEVER be exposed in API error responses.

---

## 11. Frontend Architecture (Flutter) & Map Rendering

### 11.1 Google Maps & Visualization Boundary
- **Clarification**: Google Maps in Flutter is **ONLY a visualization layer**.
- **No Mobile Device GPS**: The Flutter mobile device's onboard GPS is NOT used as the vehicle location source. Continuous phone location tracking is explicitly prohibited.
- **Authoritative Flow**: Vehicle Hardware / Simulator $\rightarrow$ MQTT $\rightarrow$ FastAPI $\rightarrow$ PostgreSQL $\rightarrow$ REST API $\rightarrow$ Flutter App $\rightarrow$ Google Maps Marker.

### 11.2 Route Polyline vs. Vehicle Marker
- **Route Geometry**: Drawn using ordered `RouteStop` points fetched from `GET /api/v1/me/assignment`. Stops are ordered by `sequence ASC` and converted into a Google Maps `Polyline`.
- **Vehicle Marker**: Positioned using coordinates returned by `GET /api/v1/me/vehicle/location` (`current_latitude`, `current_longitude`).

### 11.3 Flutter Directory Structure
```text
flutter_app/
└── lib/
    ├── main.dart
    ├── app/
    │   ├── app.dart
    │   └── router.dart
    ├── core/
    │   ├── config/api_config.dart
    │   ├── network/api_client.dart
    │   ├── storage/token_storage.dart
    │   └── errors/app_exception.dart
    └── features/
        ├── auth/
        │   ├── data/
        │   ├── models/
        │   └── presentation/
        └── tracking/
            ├── data/
            ├── models/
            └── presentation/
```

---

## 12. Environment, Secrets & Credential Management

### 12.1 Security & Configuration Invariants
- **No Committed Credentials**: Real passwords, private keys, or API tokens MUST NEVER be committed to Git repositories.
- **`.gitignore` Enforcement**: `.env` and `.env.local` files are strictly excluded via `.gitignore`.
- **Template Configuration**: Environment variable requirements are documented via `.env.example`.

### 12.2 `.env.example` Specification
```env
# Database Credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_db_password_here
POSTGRES_DB=gps_tracker
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_db_password_here@db:5432/gps_tracker

# JWT Authentication
JWT_SECRET_KEY=your_random_64_character_hex_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# MQTT Configuration
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883
MQTT_CLIENT_ID=fastapi_gps_consumer

# Business Rule Thresholds
ONLINE_THRESHOLD_SECONDS=60

# Flutter / Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 12.3 AI Safety & Database Handling Rules
If database credentials are provided by the user, the AI implementation assistant must:
1. Access credentials exclusively via environment variables or configuration files.
2. Run migrations and database creations only when credentials have appropriate privileges.
3. NEVER hardcode credentials in code or print credentials in execution logs.
4. NEVER delete, drop, or purge existing database tables without explicit user confirmation.

---

## 13. AI Implementation & Clarification Rule

When an AI coding agent works on this codebase, it MUST adhere to the following decision framework:

### Rule Statement
For routine implementation that is already explicitly specified in this documentation, proceed without asking questions. However, **ask the user before making an ambiguous, destructive, security-sensitive, or architecture-changing decision**.

#### Explicit Trigger Scenarios Requiring User Confirmation:
- Dropping or resetting existing database tables.
- Modifying database schemas after Alembic migrations exist.
- Altering authentication mechanisms (e.g., changing JWT algorithm or flow).
- Changing published API contracts or response DTO schemas.
- Adding third-party cloud services or external message queues (e.g., Redis, Kafka).
- Modifying directory structures or layered boundaries.

#### Mandated Question Format:
When requesting clarification, the AI MUST format its question using the following template:

```text
QUESTION:
[Clear description of the decision requiring clarification]

RECOMMENDED:
[Recommended approach]

WHY:
[Technical justification for the recommendation]

ALTERNATIVE:
[Alternative approach if applicable]
```

---

## 14. Development vs. Production Deployment

### 14.1 Local Development Environment (Docker Compose)
`docker-compose.yml` provides a local developer environment:
- FastAPI runs with `uvicorn app.main:app --reload` for instant code updates.
- Mosquitto runs on default port `1883`.
- PostgreSQL runs on port `5432`.
- `gps_simulator` runs as a background telemetry container.

### 14.2 Production Deployment Guidelines
- **Disable Hot-Reload**: Remove `--reload` flag; execute Uvicorn with multiple Gunicorn worker processes (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
- **Secrets Management**: Secrets injected via cloud secret managers (e.g., AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets).
- **TLS Enclosure**: Enforce HTTPS for API endpoints and MQTTS (TLS encrypted MQTT) on port `8883`.
- **Health & Monitoring**: Enable container health checks and structured JSON logging.

---

## 15. Debugging & Data Flow Traceability

### 15.1 HTTP Request Call Trace
```text
Flutter Screen (TrackingScreen)
  └─► Controller (TrackingController)
        └─► Repository (TrackingRepository)
              └─► API Client (ApiClient)
                    └─► FastAPI Router (api/v1/me.py)
                          └─► Service (VehicleService)
                                └─► Repository (VehicleRepository)
                                      └─► PostgreSQL DB
```

### 15.2 GPS Telemetry Ingestion Call Trace
```text
GPS Device / Simulator
  └─► MQTT Broker (Mosquitto)
        └─► MQTT Client Adapter (mqtt/client.py)
              └─► Telemetry Handler (mqtt/handlers.py)
                    └─► Service (GpsService.process_telemetry)
                          ├─► Out-of-order check (recorded_at vs latest_recorded_at)
                          └─► DB Repository (GpsRepository.insert_point & VehicleRepository.update_location)
                                └─► PostgreSQL Transaction Commit
```

---

## 16. Testing Strategy & Test Matrix

### 16.1 Backend Test Suite (`pytest`)
- **Authentication**: Valid login (`200 OK` + JWT token), invalid password (`401`), inactive user (`401`).
- **Assignment**: Active assignment resolution, inactive assignment rejection (`404`), assignment integrity rule rejection (`User A → Route A → Vehicle B` returns `400`).
- **Authorization**: `User A` accesses `BUS-001` (`200 OK`); `User B` attempts access to `BUS-001` (`403 Forbidden`).
- **GPS Ingestion**: Valid payload creates `gps_points` row and updates `vehicles` location.
- **Validation**: Latitude out of bounds ($>90$), longitude out of bounds ($>180$), negative speed, unknown `vehicle_code` logged and rejected.
- **Out-of-Order Telemetry**: Telemetry with older `recorded_at` appends to `gps_points` history but does NOT update `vehicles` latest position.
- **Vehicle Status**: Evaluates `ACTIVE`, `OFFLINE`, and `UNKNOWN` statuses against threshold.
- **History Pagination**: Validates query limits, `from`/`to` date filters, and keyset cursor ordering.

### 16.2 Flutter Test Suite
- **Unit Tests**: API DTO parsing, auth controller state transitions, token storage read/write.
- **Widget Tests**: Login screen form validation, loading spinner rendering, error snackbar trigger, tracking screen map state.

---

## 17. Documentation & Traceability Architecture

The project maintains complementary documentation artifacts in the `docs/` directory:
- `docs/API_CONTRACT.md`: Complete OpenAPI endpoint contracts, request/response JSON schemas, and example payloads.
- `docs/TRACEABILITY.md`: Matrix mapping requirements to backend services, database tables, Flutter screens, and Pytest suites.
- `docs/INTERVIEW_GUIDE.md`: Developer guide explaining design choices, trade-offs, and technical Q&A.

---

## 18. Definition of Done Checklist

- [ ] Project repository structure created (`backend/`, `flutter_app/`, `docs/`).
- [ ] Environment variable configuration (`.env.example`) and `.gitignore` established.
- [ ] PostgreSQL database schema & Alembic migrations created.
- [ ] Database seed script (`scripts/seed.py`) implementing User A/B test data.
- [ ] JWT authentication (`POST /api/v1/auth/login`) implemented.
- [ ] Active assignment resolution & integrity checks implemented.
- [ ] Server-side authorization enforced on `/api/v1/me/*` endpoints (`403 Forbidden` verified).
- [ ] Async MQTT consumer implemented for `vehicles/{vehicle_code}/gps`.
- [ ] Telemetry out-of-order engine & atomic DB transaction implemented.
- [ ] Authoritative vehicle status engine (`ACTIVE`, `OFFLINE`, `UNKNOWN`) implemented.
- [ ] History API with pagination (`GET /api/v1/me/vehicle/history`) implemented.
- [ ] Flutter app featuring Login Screen, Secure Token Storage, and Tracking Screen created.
- [ ] Google Maps integration rendering route polyline and vehicle marker completed.
- [ ] Automated Pytest suite covering auth, authorization, out-of-order GPS, and history passing.
- [ ] Local multi-container `docker-compose.yml` verified operational.
- [ ] Supplementary technical documentation (`docs/API_CONTRACT.md`, `docs/TRACEABILITY.md`, `docs/INTERVIEW_GUIDE.md`) completed.
