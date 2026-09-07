# System Architecture Specification

## 1. High-Level Technical Topology

The **GPS Vehicle Tracking System** follows a decoupled, security-focused architecture designed around clean separation of concerns, asynchronous telemetry transport, and server-side authorization enforcement.

```mermaid
graph TD
    subgraph Mobile Presentation Layer
        Flutter[Flutter Mobile App\nLogin Screen / Map Tracking View]
    end

    subgraph Security & API Layer
        FastAPI[FastAPI Backend\nRouters -> Services -> Repositories]
    end

    subgraph Data & Telemetry Layer
        DB[(PostgreSQL Database\nUsers / Assignments / Routes / History)]
        MQTT[Mosquitto MQTT Broker\nTopic: vehicles/{vehicle_code}/gps]
    end

    subgraph Hardware & Simulation Layer
        Sim[Deterministic GPS Simulator\nVehicle Telemetry Publisher]
    end

    Flutter -->|HTTPS + Bearer JWT| FastAPI
    FastAPI -->|Async SQLAlchemy / asyncpg| DB
    FastAPI -->|aiomqtt Background Consumer| MQTT
    Sim -->|Publish Telemetry Packets| MQTT
```

---

## 2. Architectural Invariants & Security Boundaries

### 2.1 Server-Side Authorization Boundary
- **Principle**: Mobile clients **MUST NEVER** be trusted to specify vehicle IDs or user scopes via request body or URL parameters.
- **Implementation**: The backend exposes context-aware endpoints (`/api/v1/me/assignment`, `/api/v1/me/vehicle`, `/api/v1/me/vehicle/location`, `/api/v1/me/vehicle/history`).
- **Enforcement**: The API extracts the authenticated user ID strictly from the verified JWT access token payload (`sub` claim). The service layer ([`AssignmentService`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/assignment_service.py) & [`VehicleService`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/services/vehicle_service.py)) queries the database for the user's single active assignment. If no active assignment exists, access is denied (`404 NO_ACTIVE_ASSIGNMENT`). If a user attempts to query a vehicle outside their assigned route, `403 VEHICLE_ACCESS_DENIED` is returned.

### 2.2 Telemetry Ingest vs. Presentation Separation
- **Mobile Devices are Visualization Only**: Mobile devices running the Flutter application are consumers of vehicle location state and **NEVER** serve as the telemetry source.
- **MQTT Transport**: Inbound vehicle GPS data enters exclusively through the Mosquitto MQTT broker on topic `vehicles/{vehicle_code}/gps`.

---

## 3. Backend Layered Software Pattern

The FastAPI backend adheres strictly to the **Router-Service-Repository** architectural pattern:

```text
┌──────────────────────────────────────────────────────────┐
│                      FastAPI Router                      │
│ Parses Request / Validates JWT / Returns Pydantic DTO    │
└────────────────────────────┬─────────────────────────────┘
                             │ Dependency Injection
                             ▼
┌──────────────────────────────────────────────────────────┐
│                      Service Layer                       │
│ Implements Business Invariants & Security Scoping Rules  │
└────────────────────────────┬─────────────────────────────┘
                             │ Async Method Calls
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     Repository Layer                     │
│ Handles Pure Database Operations via SQLAlchemy Async    │
└──────────────────────────────────────────────────────────┘
```

1. **API Routers (`app/api/v1/`)**:
   - Handles HTTP routing, request deserialization via Pydantic schemas, and security dependency injection (`get_current_user`).
   - Routers contain **zero business logic**.

2. **Service Layer (`app/services/`)**:
   - Encapsulates domain logic, assignment validation rules, telemetry ingestion logic, stale packet protection checks, and status calculations.

3. **Repository Layer (`app/repositories/`)**:
   - Performs pure asynchronous database operations using SQLAlchemy Async Sessions (`AsyncSession`).

4. **Models (`app/models/`)**:
   - Declarative SQLAlchemy models representing database entities (`User`, `Route`, `Stop`, `Vehicle`, `Assignment`, `GPSPoint`).

---

## 4. Application Lifespan & Background Task Management

The FastAPI application uses an async lifespan context manager ([`app/main.py`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/main.py)) to manage background services:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch async MQTT telemetry consumer task
    mqtt_consumer_manager.start()
    yield
    # Shutdown: Gracefully stop MQTT consumer connection
    await mqtt_consumer_manager.stop()
```

- **[`MQTTConsumerManager`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/mqtt/consumer.py)** spawns an `asyncio.Task` that maintains a persistent connection to Mosquitto, subscribes to wildcard topic `vehicles/+/gps`, parses incoming JSON payloads, and delegates ingestion to `TelemetryIngestionService`.

---

## 5. Standardized Error Handling

All domain errors raise [`AppException`](file:///c:/Users/Asus/Downloads/GPS-finder-/backend/app/core/exceptions.py), which is caught by a global FastAPI exception handler returning standardized JSON payloads:

```json
{
  "error": {
    "code": "VEHICLE_ACCESS_DENIED",
    "message": "User does not have permission to access vehicle 'BUS-002'."
  }
}
```

### Standardized Error Codes:
| Error Code | Status | Cause |
| :--- | :--- | :--- |
| `INVALID_CREDENTIALS` | `401 Unauthorized` | Invalid email or password during login. |
| `TOKEN_EXPIRED` | `401 Unauthorized` | JWT token timestamp has expired. |
| `INVALID_TOKEN` | `401 Unauthorized` | JWT token signature verification failed. |
| `NO_ACTIVE_ASSIGNMENT` | `404 Not Found` | Authenticated user has no active assignment. |
| `VEHICLE_ACCESS_DENIED` | `403 Forbidden` | User attempted to query a vehicle outside their active assignment. |
| `ASSIGNMENT_INTEGRITY_VIOLATION` | `400 Bad Request` | Vehicle route does not match assigned route. |
| `INVALID_TELEMETRY_PACKET` | `422 Unprocessable` | MQTT telemetry payload failed bounds validation. |
