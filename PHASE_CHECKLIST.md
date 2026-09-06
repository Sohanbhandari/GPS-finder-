# GPS Vehicle Tracking System - Phase Implementation Checklist

This checklist tracks the implementation progress across all system phases. Completed items are marked `[x]`, in-progress items `[-]`, and pending items `[ ]`.

---

## Phase 1: Repository Audit + Architecture Lock
- [x] Inspect existing workspace, configuration, documentation, and current code structure.
- [x] Compare existing repository state with `DOCUMENTATION-INDEX.md` (Master Application Document).
- [x] Identify missing components, naming conflicts, and directory structure requirements.
- [x] Confirm architectural boundaries (FastAPI security boundary, PostgreSQL state, MQTT transport, Flutter presentation, Google Maps visualization).
- [x] Create Architecture Decision Record (`docs/adr/0001-architecture-boundaries-and-directory-structure.md`).
- [x] Create Master Phase Checklist (`PHASE_CHECKLIST.md`).

---

## Phase 2: Environment & Container Configuration
- [ ] Create `.env.example` with database, JWT, MQTT, and Google Maps key templates.
- [ ] Configure `docker-compose.yml` for local stack (PostgreSQL, Mosquitto MQTT broker, FastAPI backend, Telemetry Simulator).
- [ ] Create Dockerfile for FastAPI backend application.

---

## Phase 3: PostgreSQL Database Schema & Alembic Migrations
- [ ] Initialize Alembic migration framework in `backend/migrations`.
- [ ] Define SQLAlchemy models for `users`, `routes`, `route_stops`, `vehicles`, `assignments`, and `gps_points`.
- [ ] Create database tables with constraints and indexes (`idx_unique_active_user`, composite indexes).
- [ ] Create seed script (`scripts/seed.py`) with test data for User A and User B.

---

## Phase 4: Backend Core & Authentication System
- [ ] Configure FastAPI core settings, security utilities (passlib bcrypt), and JWT token management.
- [ ] Implement `POST /api/v1/auth/login` returning signed JWT access token.
- [ ] Implement HTTP Bearer authentication dependency and user identity resolution.

---

## Phase 5: Assignment Resolution & Server-Side Authorization Engine
- [ ] Implement active assignment resolution service (`GET /api/v1/me/assignment`).
- [ ] Enforce assignment integrity rule (`vehicle.route_id == assignment.route_id`).
- [ ] Enforce server-side authorization on `/api/v1/me/*` endpoints (return `403 Forbidden` for unauthorized vehicle access).

---

## Phase 6: MQTT Telemetry Consumer & Out-of-Order Engine
- [ ] Implement async MQTT client manager subscribing to `vehicles/{vehicle_code}/gps`.
- [ ] Implement telemetry payload validation and schema parsing.
- [ ] Implement out-of-order telemetry guard engine and atomic DB transaction logic.
- [ ] Implement denormalized location state updates on `vehicles` table.

---

## Phase 7: Vehicle Status Engine & REST Telemetry APIs
- [ ] Implement authoritative vehicle status calculation (`ACTIVE`, `OFFLINE`, `UNKNOWN`) based on `ONLINE_THRESHOLD_SECONDS`.
- [ ] Implement `GET /api/v1/me/vehicle` and `GET /api/v1/me/vehicle/location`.
- [ ] Implement telemetry history API with filtering and keyset pagination (`GET /api/v1/me/vehicle/history`).

---

## Phase 8: Telemetry Simulator Implementation
- [ ] Create `simulator/gps_simulator.py` supporting linear route progression and out-of-order packet injection for testing.

---

## Phase 9: Frontend Architecture & Flutter Setup
- [ ] Initialize Flutter project structure (`frontend/`) following Clean Architecture (`core/`, `features/auth`, `features/tracking`).
- [ ] Implement HTTP client, secure token storage, and API error handling.

---

## Phase 10: Flutter Auth & Tracking UI Integration
- [ ] Implement Login Screen UI, state management, and JWT storage.
- [ ] Implement Tracking Screen UI rendering assigned route info, vehicle status badge, live speed, and updated timestamp.
- [ ] Implement Google Maps integration rendering route polyline and vehicle marker.

---

## Phase 11: End-to-End Verification & Automated Testing
- [ ] Run backend Pytest suite covering auth, active assignments, authorization, out-of-order telemetry, and history pagination.
- [ ] Run Flutter unit and widget tests.
- [ ] Verify full end-to-end telemetry flow from simulator $\rightarrow$ MQTT $\rightarrow$ FastAPI $\rightarrow$ PostgreSQL $\rightarrow$ Flutter UI.
