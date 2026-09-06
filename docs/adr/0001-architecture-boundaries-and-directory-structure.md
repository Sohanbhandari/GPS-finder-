# Architecture Decision Record (ADR) 0001: Architecture Boundaries & Directory Structure

- **Status**: Accepted
- **Date**: 2026-09-06
- **Context**: System setup and architectural alignment for GPS Vehicle Tracking System.

## 1. System Component Boundaries

| Component | Responsibility | Boundary Rule |
| :--- | :--- | :--- |
| **FastAPI Backend** | Security boundary, authentication (JWT), active assignment resolution, telemetry ingestion, vehicle status calculation, out-of-order state updates, and history API. | **Source of Business Truth**: Clients NEVER calculate status or enforce authorization rules. |
| **PostgreSQL** | Relational data store for `users`, `routes`, `route_stops`, `vehicles`, `assignments`, and `gps_points`. | **State Persistence**: PostgreSQL is the single source of persistent truth. |
| **Mosquitto MQTT** | High-throughput inbound transport for vehicle telemetry (`vehicles/{vehicle_code}/gps`). | **Telemetry Transport Only**: No persistent domain state stored in MQTT. |
| **Flutter App** | Presentation layer (Login Screen, Tracking Screen, Route Polyline, Vehicle Location Marker). | **Presentation Client Only**: Mobile device GPS is NEVER used for telemetry. |
| **Google Maps** | Rendering polylines and vehicle location markers in the Flutter UI. | **Visualization Only**: Does not calculate route progress or vehicle status. |

## 2. Directory Structure Standardization

To resolve naming inconsistencies between `README.md` and `DOCUMENTATION-INDEX.md`, the workspace directory structure is locked as:

```text
GPS-finder-/
├── backend/                  # FastAPI Application Core
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── mqtt/
│   ├── migrations/           # Alembic Database Migrations
│   ├── tests/                # Pytest Suite
│   ├── scripts/              # DB Seed Scripts
│   ├── simulator/            # Telemetry Simulator
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Flutter Mobile Client Application
│   ├── lib/
│   │   ├── app/
│   │   ├── core/
│   │   └── features/
│   │       ├── auth/
│   │       └── tracking/
│   └── pubspec.yaml
├── docs/                     # Architecture & API Specifications
│   ├── adr/                  # Architecture Decision Records
│   ├── API_CONTRACT.md
│   ├── TRACEABILITY.md
│   └── INTERVIEW_GUIDE.md
├── docker-compose.yml        # Local Development Stack
├── .env.example              # Environment Variable Template
├── PHASE_CHECKLIST.md        # Master Phase Checklist
├── DOCUMENTATION-INDEX.md    # Master Technical Documentation
└── README.md                 # System Overview
```

## 3. Key Technical Decisions Locked

1. **Timestamp Explicit Differentiation**:
   - `recorded_at`: UTC timestamp generated at vehicle source / simulator.
   - `received_at`: UTC timestamp generated at FastAPI server ingestion.
2. **Out-of-Order Telemetry Policy**:
   - `gps_points`: Immutable append-only history for all valid incoming points.
   - `vehicles`: Current location updated ONLY if incoming `recorded_at >= vehicles.latest_recorded_at`.
3. **Vehicle Status Calculation**:
   - Status (`ACTIVE`, `OFFLINE`, `UNKNOWN`) is dynamically computed by FastAPI using `last_seen_at` and `ONLINE_THRESHOLD_SECONDS` (default: 60s).
