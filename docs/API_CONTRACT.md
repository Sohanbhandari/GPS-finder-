# GPS Vehicle Tracking System - REST API Contract & Specification

> **Base URL**: `/api/v1`  
> **Protocol**: HTTPS  
> **Content-Type**: `application/json`  
> **Security Scheme**: HTTP Bearer (JWT)

---

## Standard Error Response Format

All API errors return a uniform JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable explanation of the error condition."
  }
}
```

### Standard Error Codes

| Error Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `INVALID_CREDENTIALS` | `401 Unauthorized` | Invalid email or password during login. |
| `UNAUTHORIZED` | `401 Unauthorized` | Missing, malformed, or expired JWT bearer token. |
| `VEHICLE_ACCESS_DENIED` | `403 Forbidden` | Authenticated user is not authorized to access requested vehicle. |
| `NO_ACTIVE_ASSIGNMENT` | `404 Not Found` | Authenticated user has no active route/vehicle assignment. |
| `ASSIGNMENT_INTEGRITY_VIOLATION` | `400 Bad Request` | Assigned vehicle does not belong to assigned route. |
| `VALIDATION_ERROR` | `422 Unprocessable Entity` | Query parameter or body schema validation failed (e.g. `from > to`). |
| `NOT_FOUND` | `404 Not Found` | Targeted resource was not found. |

---

## Endpoint Specifications

### 1. Health Check Endpoint

`GET /api/v1/health`

- **Authentication**: None (Public)
- **Response**: `200 OK`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-06T12:00:00Z"
}
```

---

### 2. User Login Endpoint

`POST /api/v1/auth/login`

- **Authentication**: None (Public)
- **Request Body**:
  ```json
  {
    "email": "driver.a@example.com",
    "password": "Password123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (`INVALID_CREDENTIALS`)

---

### 3. Active Assignment Endpoint

`GET /api/v1/me/assignment`

- **Authentication**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  {
    "id": "e67b2d5a-821b-4f9e-a612-42173f278910",
    "user_id": "9a12c483-3e11-421a-8255-091f9b1c2101",
    "is_active": true,
    "assigned_at": "2026-09-06T00:00:00Z",
    "updated_at": "2026-09-06T00:00:00Z",
    "route": {
      "id": "f81c9b21-410a-4281-912b-31289c091f22",
      "code": "ROUTE-A",
      "name": "North Campus Loop",
      "description": "Loop connecting Central Station and North Gate.",
      "stops": [
        {
          "id": "11111111-1111-1111-1111-111111111111",
          "sequence": 1,
          "name": "Central Station",
          "latitude": 27.700769,
          "longitude": 85.30014
        },
        {
          "id": "22222222-2222-2222-2222-222222222222",
          "sequence": 2,
          "name": "Library Gate",
          "latitude": 27.7025,
          "longitude": 85.3031
        }
      ]
    },
    "vehicle": {
      "id": "7b8219c0-512a-4f81-ba11-9281512c9182",
      "vehicle_code": "BUS-001",
      "route_id": "f81c9b21-410a-4281-912b-31289c091f22",
      "current_latitude": 27.700769,
      "current_longitude": 85.30014,
      "current_speed": 0.0,
      "latest_recorded_at": "2026-09-06T12:00:00Z",
      "last_seen_at": "2026-09-06T12:00:00Z"
    }
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (`UNAUTHORIZED`)
  - `404 Not Found` (`NO_ACTIVE_ASSIGNMENT`)
  - `400 Bad Request` (`ASSIGNMENT_INTEGRITY_VIOLATION`)

---

### 4. Assigned Vehicle Metadata Endpoint

`GET /api/v1/me/vehicle`

- **Authentication**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  {
    "id": "7b8219c0-512a-4f81-ba11-9281512c9182",
    "vehicle_code": "BUS-001",
    "route_id": "f81c9b21-410a-4281-912b-31289c091f22",
    "status": "ACTIVE",
    "current_latitude": 27.700769,
    "current_longitude": 85.30014,
    "current_speed": 0.0,
    "latest_recorded_at": "2026-09-06T12:00:00Z",
    "last_seen_at": "2026-09-06T12:00:00Z",
    "created_at": "2026-09-06T00:00:00Z"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (`UNAUTHORIZED`)
  - `404 Not Found` (`NO_ACTIVE_ASSIGNMENT`)

---

### 5. Assigned Vehicle Location Endpoint

`GET /api/v1/me/vehicle/location`

- **Authentication**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  {
    "vehicle_id": "7b8219c0-512a-4f81-ba11-9281512c9182",
    "vehicle_code": "BUS-001",
    "status": "ACTIVE",
    "latitude": 27.700769,
    "longitude": 85.30014,
    "speed": 0.0,
    "latest_recorded_at": "2026-09-06T12:00:00Z",
    "last_seen_at": "2026-09-06T12:00:00Z"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (`UNAUTHORIZED`)
  - `404 Not Found` (`NO_ACTIVE_ASSIGNMENT`)

---

### 6. Vehicle Telemetry History Endpoint

`GET /api/v1/me/vehicle/history`

- **Authentication**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `from` (Optional, string): ISO 8601 start timestamp (e.g., `2026-09-06T00:00:00Z`).
  - `to` (Optional, string): ISO 8601 end timestamp (e.g., `2026-09-06T23:59:59Z`).
  - `limit` (Optional, integer): Items per page (Default: `50`, Max: `200`).
  - `cursor` (Optional, string): UUID cursor for keyset pagination.
- **Sorting**: Deterministic `recorded_at DESC, id DESC`.
- **Response**: `200 OK`
  ```json
  {
    "items": [
      {
        "id": "33333333-3333-3333-3333-333333333333",
        "vehicle_id": "7b8219c0-512a-4f81-ba11-9281512c9182",
        "latitude": 27.700769,
        "longitude": 85.30014,
        "speed": 0.0,
        "recorded_at": "2026-09-06T12:00:00Z",
        "received_at": "2026-09-06T12:00:01Z"
      }
    ],
    "next_cursor": null,
    "has_more": false
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (`UNAUTHORIZED`)
  - `404 Not Found` (`NO_ACTIVE_ASSIGNMENT`)
  - `422 Unprocessable Entity` (`VALIDATION_ERROR`) if `from > to`.
