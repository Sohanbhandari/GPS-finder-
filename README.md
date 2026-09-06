# GPS Vehicle Tracking System

A production-grade, secure **GPS Vehicle Tracking System** backend built with **FastAPI**, **PostgreSQL**, **Alembic**, and **MQTT (Mosquitto)**.

The system enforces server-side authorization boundaries, single active user assignments, out-of-order telemetry stale packet protection, keyset pagination, and clean REST API contracts for mobile presentation clients (Flutter).

---

## Technical Architecture

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
                                ┌────────────┴──────────────┐
                                │ GPS Simulator / Hardware  │
                                └───────────────────────────┘
```

---

## Key Features

1. **Security & Server-Side Authorization Boundary**:
   - Authentication via bcrypt hashed passwords and signed JWT access tokens (`POST /api/v1/auth/login`).
   - Strict server-side vehicle scoping: Endpoints ignore client parameter tampering. Users can only access vehicles mapped to their active assignment (`GET /api/v1/me/assignment`, `GET /api/v1/me/vehicle`).
   - Cross-user vehicle access attempts return `HTTP 403 Forbidden` (`VEHICLE_ACCESS_DENIED`).

2. **Single Active Assignment & Integrity Invariant**:
   - PostgreSQL Partial Unique Index (`CREATE UNIQUE INDEX idx_unique_active_user ON assignments(user_id) WHERE is_active = TRUE;`) guarantees at most one active assignment per user while preserving full assignment history.
   - Assignment Integrity Invariant (`vehicle.route_id == assignment.route_id`) validated in the service layer.

3. **MQTT Telemetry & Out-of-Order Engine**:
   - Background async MQTT consumer subscribing to `vehicles/{vehicle_code}/gps`.
   - Structural bounds validation (`-90 <= lat <= 90`, `-180 <= lon <= 180`, `speed >= 0`).
   - Every valid packet is appended to `gps_points` history.
   - **Stale Packet Protection**: Current vehicle location state is updated **ONLY IF** `incoming recorded_at >= latest_recorded_at`. Out-of-order packets cannot move current vehicle location backwards on the map.

4. **Vehicle Status Engine**:
   - Dynamic vehicle online status calculation:
     - `ACTIVE`: Telemetry received within `ONLINE_THRESHOLD_SECONDS` (default: 60s).
     - `OFFLINE`: Telemetry older than `ONLINE_THRESHOLD_SECONDS`.
     - `UNKNOWN`: No telemetry ever recorded for the vehicle.

5. **Polyline Sequence & Keyset Pagination**:
   - Route stops in `/api/v1/me/assignment` are strictly sorted by `sequence ASC` for direct polyline rendering.
   - History queries (`/api/v1/me/vehicle/history`) support range filtering (`from`, `to`) and $O(\log N)$ composite keyset pagination (`recorded_at DESC, id DESC`).

---

## Directory Structure

```text
GPS-finder-/
├── .env.example                # Environment variable configuration template
├── README.md                   # Project documentation
├── docker/
│   └── mosquitto.conf          # Development MQTT broker configuration
├── docs/
│   └── API_CONTRACT.md         # Master REST API Specification
└── backend/
    ├── alembic.ini             # Alembic migration configuration
    ├── alembic/                # Async database migrations & revisions
    │   ├── env.py
    │   └── versions/
    │       └── 0001_initial_schema.py
    ├── app/
    │   ├── main.py             # FastAPI entrypoint & lifecycle manager
    │   ├── api/                # API routers & security dependencies
    │   │   ├── deps.py
    │   │   └── v1/
    │   ├── core/               # Configuration, logging, & exceptions
    │   ├── db/                 # Database engine, session, & seed script
    │   ├── models/             # SQLAlchemy ORM data models
    │   ├── mqtt/               # MQTT consumer background task
    │   ├── repositories/       # Data access repositories
    │   ├── schemas/            # Pydantic DTO models
    │   └── services/           # Business & security services
    ├── scripts/
    │   └── seed.py             # Seed execution script
    └── tests/                  # Pytest unit & integration test suite
```

---

## Setup & Local Development

### 1. Environment Configuration
Copy `.env.example` to `.env` inside `backend/`:
```bash
cp .env.example backend/.env
```

### 2. Install Dependencies
Initialize virtual environment and install requirements:
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows (or source .venv/bin/activate on Unix)
pip install -r requirements.txt
```

### 3. Run Database Migrations
Run Alembic async migrations to create tables and indexes:
```bash
cd backend
alembic upgrade head
```

### 4. Seed Development Data
Populate deterministic seed data (`User A` $\rightarrow$ `BUS-001`, `User B` $\rightarrow$ `BUS-002`, route stops, initial coordinates):
```bash
cd backend
python -m app.db.seed
```

### 5. Run FastAPI Application
Start the Uvicorn dev server:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive API Docs: `http://localhost:8000/api/v1/docs`
- OpenAPI JSON Schema: `http://localhost:8000/api/v1/openapi.json`

---

## Automated Testing

Run the full Pytest suite (26 tests covering database constraints, seed data, auth, assignment rules, telemetry ingestion, out-of-order engine, and API contracts):
```bash
cd backend
python -m pytest -v
```

---

## REST API Summary

For full details, headers, status codes, and payload examples, refer to [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | None | System health check (`status`, `version`, `timestamp`). |
| `POST` | `/api/v1/auth/login` | None | Authenticates credentials; returns JWT bearer token. |
| `GET` | `/api/v1/me/assignment` | JWT | Resolves user's active assignment (`route` and `vehicle`). |
| `GET` | `/api/v1/me/vehicle` | JWT | Returns assigned vehicle metadata & status (`ACTIVE`, `OFFLINE`, `UNKNOWN`). |
| `GET` | `/api/v1/me/vehicle/location` | JWT | Returns assigned vehicle's current location, speed, `recorded_at`, `last_seen_at`. |
| `GET` | `/api/v1/me/vehicle/history` | JWT | Returns paginated telemetry history with range & keyset cursor options. |
