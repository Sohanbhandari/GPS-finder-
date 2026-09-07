# GPS Vehicle Tracking System - Backend Documentation

Production-grade, security-focused **FastAPI** backend for real-time GPS vehicle tracking with PostgreSQL, Alembic, Mosquitto MQTT, and Docker Compose integration.

---

## 1. Architecture & Layered Pattern

The backend follows a strict **Router-Service-Repository** design pattern:

```text
app/
├── api/          # Routers (HTTP parsing, JWT security dependencies, DTO validation)
├── core/         # Configuration (Pydantic Settings), logging, & exceptions
├── db/           # Async SQLAlchemy session engine & database seed script
├── models/       # Declarative ORM entities (User, Route, Stop, Vehicle, Assignment, GPSPoint)
├── mqtt/         # Background async MQTT consumer task
├── repositories/ # Data access abstraction (AsyncSession queries)
├── schemas/      # Pydantic DTO request/response schemas
└── services/     # Business logic, security scoping, telemetry validation, status engine
```

---

## 2. Security & Server-Side Authorization Boundary

- **Authentication**: Bcrypt password hashing + signed JWT Access Tokens (`POST /api/v1/auth/login`).
- **Vehicle Scoping Boundary**: Vehicle access is derived exclusively on the server side via `/api/v1/me/assignment` and `/api/v1/me/vehicle`.
- **Cross-User Access Denial**: Unassigned or mismatched vehicle requests return `403 Forbidden` (`VEHICLE_ACCESS_DENIED`).

---

## 3. Database Invariants & Migrations

### Single Active Assignment Invariant
PostgreSQL Partial Unique Index ensures at most one active assignment per user:
```sql
CREATE UNIQUE INDEX idx_unique_active_user ON assignments(user_id) WHERE is_active = TRUE;
```

### Keyset Pagination Composite Index
Optimizes $O(\log N)$ historical query performance:
```sql
CREATE INDEX idx_gps_points_keyset ON gps_points(vehicle_id, recorded_at DESC, id DESC);
```

### Database Commands:
```bash
# Apply migrations
alembic upgrade head

# Seed initial development state (User A, User B, Routes, Vehicles, Assignments)
python -m app.db.seed
```

---

## 4. MQTT Telemetry Ingestion & Stale Packet Engine

- **Topic**: `vehicles/{vehicle_code}/gps`
- **Validation**: Rejects invalid coordinates (`lat` outside `[-90, 90]`, `lon` outside `[-180, 180]`, negative speed).
- **History**: Appends **EVERY** valid packet to `gps_points`.
- **Stale Protection**: Updates current position in `vehicles` table **ONLY IF** `incoming.recorded_at >= vehicle.latest_recorded_at`.

---

## 5. Setup & Execution Options

### Local Virtual Environment Execution
```bash
# 1. Initialize environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows (source .venv/bin/activate on Linux/Mac)
pip install -r requirements.txt

# 2. Run migrations & seed
alembic upgrade head
python -m app.db.seed

# 3. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose Execution
```bash
docker-compose up --build -d
```

---

## 6. Automated Testing

Run full Pytest suite covering auth, database constraints, telemetry ingestion, out-of-order protection, and API contracts:
```bash
python -m pytest -v
```

---

## 7. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `DB Connection Refused` | PostgreSQL container/service is down. | Verify `docker-compose ps` or check `POSTGRES_HOST` / `DATABASE_URL` settings. |
| `MQTT Connection Error` | Mosquitto broker not running on port 1883. | Ensure Mosquitto container is running (`docker-compose logs mosquitto`). |
| `401 TOKEN_EXPIRED` | JWT token timestamp exceeded 60 minutes. | Re-authenticate via `POST /api/v1/auth/login` to obtain fresh token. |
