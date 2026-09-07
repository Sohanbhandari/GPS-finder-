# Master Requirement Traceability Matrix

This document proves complete 100% traceability from every functional, architectural, and security requirement to its exact implementation in the **Backend (Python/FastAPI)**, **Database (PostgreSQL/Alembic)**, **REST API Contract**, **Mobile Client (Flutter)**, and **Automated Verification Test Suite (Pytest)**.

---

## 1. Authentication & Security Boundary Requirements

| Req ID | Description | Backend Implementation | Database Component | REST API Endpoint | Flutter Component | Pytest / Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-AUTH-001** | **JWT Authentication & Bcrypt Hashing**<br>User authentication via Bcrypt password verification and signed HS256 JWT access tokens. | [`AuthService.authenticate_user`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/auth_service.py)<br>[`AuthService.create_access_token`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/auth_service.py) | `users` table (`password_hash`, `email`) | `POST /api/v1/auth/login` | [`AuthController.login`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/auth_controller.dart)<br>[`LoginScreen`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/screens/login_screen.dart) | `test_auth.py::test_login_success`<br>`test_auth.py::test_login_invalid_password` |
| **REQ-AUTH-002** | **Server-Side Authorization Boundary**<br>Scoping vehicle access strictly via JWT token context (`/me/assignment`). Ignore client parameter tampering. | [`get_current_user`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/api/deps.py)<br>[`AssignmentService.get_active_assignment_for_user`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/assignment_service.py) | `assignments` table | `GET /api/v1/me/assignment`<br>`GET /api/v1/me/vehicle`<br>`GET /api/v1/me/vehicle/location` | [`ApiService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/api_service.dart) (attaches Bearer Token) | `test_assignment_auth.py::test_cross_user_vehicle_access_denial`<br>`test_assignment_auth.py::test_unauthorized_missing_token` |
| **REQ-AUTH-003** | **401 Unauthorized Eviction Flow**<br>Automatic token invalidation and redirection to login on token expiration or 401 response. | [`get_current_user`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/api/deps.py) (raises `401 TOKEN_EXPIRED`) | N/A | All protected endpoints | [`TrackingController(onUnauthorized)`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/main.dart)<br>[`StorageService`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/storage_service.dart) | `test_assignment_auth.py::test_unauthorized_missing_token` |

---

## 2. Database & Data Integrity Requirements

| Req ID | Description | Backend Implementation | Database Component | REST API Endpoint | Flutter Component | Pytest / Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-DATA-001** | **Single Active Assignment Invariant**<br>Guarantees at most one active assignment per user in PostgreSQL while preserving history. | [`AssignmentService`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/assignment_service.py) | `CREATE UNIQUE INDEX idx_unique_active_user ON assignments(user_id) WHERE is_active = TRUE;` | `GET /api/v1/me/assignment` | [`TrackingController.loadUserAssignment`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/tracking_controller.dart) | `test_database_schema.py::test_single_active_assignment_constraint` |
| **REQ-DATA-002** | **Assignment Integrity Invariant**<br>Ensures assigned vehicle belongs to assigned route (`vehicle.route_id == assignment.route_id`). | [`AssignmentService._validate_integrity`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/assignment_service.py) | `assignments(vehicle_id, route_id)` FK constraints | `GET /api/v1/me/assignment` (returns `400 ASSIGNMENT_INTEGRITY_VIOLATION`) | [`TrackingState`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/models/tracking_state.dart) | `test_assignment_auth.py::test_assignment_integrity_violation` |
| **REQ-DATA-003** | **Deterministic Development Seeding**<br>Creates reproducible test state: User A $\rightarrow$ BUS-001, User B $\rightarrow$ BUS-002, routes & stops. | [`app.db.seed`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/db/seed.py)<br>[`scripts/seed.py`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/scripts/seed.py) | Seed script inserting into `users`, `routes`, `stops`, `vehicles`, `assignments` | All endpoints | Mock data initialization | `test_database_schema.py::test_seed_database_execution` |

---

## 3. MQTT Telemetry Ingestion & Real-Time Engine

| Req ID | Description | Backend Implementation | Database Component | REST API Endpoint / Transport | Flutter Component | Pytest / Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-MQTT-001** | **Async MQTT Telemetry Transport**<br>Background MQTT consumer subscribing to `vehicles/{vehicle_code}/gps`. | [`MQTTConsumerManager`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/mqtt/consumer.py)<br>[`TelemetryIngestionService`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/telemetry_ingestion_service.py) | Ingests into `gps_points` table | Mosquitto MQTT Topic `vehicles/+/gps` | N/A (Backend Ingestion) | `test_mqtt_telemetry.py::test_ingest_valid_telemetry_packet` |
| **REQ-MQTT-002** | **Structural Telemetry Bounds Validation**<br>Validates `-90<=lat<=90`, `-180<=lon<=180`, `speed>=0`. | [`TelemetryPayload`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/schemas/telemetry.py) (Pydantic Schema) | Rejects out-of-bounds rows | Topic `vehicles/+/gps` | N/A | `test_mqtt_telemetry.py::test_telemetry_schema_out_of_bounds_latitude`<br>`test_mqtt_telemetry.py::test_telemetry_schema_negative_speed` |
| **REQ-MQTT-003** | **Out-of-Order Stale Packet Protection**<br>Updates current vehicle position ONLY IF `incoming recorded_at >= latest_recorded_at`. Always appends to history. | [`TelemetryIngestionService.ingest_telemetry`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/telemetry_ingestion_service.py) | Updates `vehicles.latest_recorded_at`; inserts into `gps_points` | `GET /api/v1/me/vehicle/location` | [`TrackingController.pollVehicleLocation`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/controllers/tracking_controller.dart) | `test_mqtt_telemetry.py::test_out_of_order_stale_packet_protection`<br>`test_e2e_integration.py::test_e2e_stale_packet_protection_via_api` |
| **REQ-MQTT-004** | **Dynamic Vehicle Status Calculation**<br>Computes `ACTIVE` (telemetry <=60s), `OFFLINE` (>60s), or `UNKNOWN` (no telemetry). | [`VehicleService._compute_status`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/vehicle_service.py) | Computes from `vehicles.last_seen_at` | `GET /api/v1/me/vehicle`<br>`GET /api/v1/me/vehicle/location` | [`StatusBadge`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/screens/widgets/status_badge.dart) | `test_mqtt_telemetry.py::test_vehicle_status_engine_calculation` |

---

## 4. REST API & Mobile Presentation Requirements

| Req ID | Description | Backend Implementation | Database Component | REST API Endpoint | Flutter Component | Pytest / Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-REST-001** | **Keyset Paginated Telemetry History**<br>$O(\log N)$ cursor pagination on `recorded_at DESC, id DESC` with `from` and `to` range filtering. | [`GPSPointRepository.get_history_keyset`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/repositories/gps_point_repository.py) | `CREATE INDEX idx_gps_points_keyset ON gps_points(vehicle_id, recorded_at DESC, id DESC);` | `GET /api/v1/me/vehicle/history` | [`ApiService.getVehicleHistory`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/services/api_service.dart) | `test_e2e_integration.py::test_e2e_history_filtering_and_keyset_pagination`<br>`test_api_contract.py::test_me_vehicle_history_contract_and_validation` |
| **REQ-REST-002** | **Polyline Sequence Sorting**<br>Route stops sorted strictly by `sequence ASC` for direct polyline rendering on map. | [`RouteRepository.get_by_id_with_stops`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/repositories/route_repository.py) | `stops.sequence` column & index | `GET /api/v1/me/assignment` | [`VehicleMapView`](file:///c:/Users/Asus/Downloads/GPS-finder-/frontend/lib/screens/widgets/vehicle_map_view.dart) (Polyline generation) | `test_api_contract.py::test_me_assignment_route_stops_sequence_order` |
| **REQ-REST-003** | **Interactive OpenAPI Specification**<br>Auto-generated OpenAPI JSON schema and interactive Swagger UI. | [`create_app`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/main.py) | N/A | `GET /api/v1/openapi.json`<br>`GET /api/v1/docs` | N/A | `test_api_contract.py::test_openapi_json_schema_generation` |

---

## 5. Deployment & System Verification Requirements

| Req ID | Description | Backend / Infrastructure | Docker Container | Verification Tool / Script | Pytest / Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-DEPL-001** | **Clean Docker Compose Deployment**<br>Multi-container setup with PostgreSQL, Mosquitto, FastAPI, and Simulator. | [`docker-compose.yml`](file:///c:/Users/Asus/Downloads/GPS-finder-/docker-compose.yml) | `gps_postgres`<br>`gps_mosquitto`<br>`gps_backend`<br>`gps_simulator` | `docker-compose up --build -d` | [`scripts/verify_full_system.py`](file:///c:/Users/Asus/Downloads/GPS-finder-/scripts/verify_full_system.py) |
| **REQ-DEPL-002** | **Zero-Sleep Startup Health Ordering**<br>Boot dependency ordering via container health checks and connection wait loop in `entrypoint.sh`. | [`backend/entrypoint.sh`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/entrypoint.sh) | `depends_on: condition: service_healthy` | Container startup logs | End-to-end full system flow gates |
