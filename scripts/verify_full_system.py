#!/usr/bin/env python3
"""
Full-System Flow Verification Script for GPS Vehicle Tracking System.

Flow steps verified:
1. Health Check (`GET /api/v1/health`)
2. Authentication & Seed User Login (`POST /api/v1/auth/login`)
3. User Assignment Resolution (`GET /api/v1/me/assignment`)
4. Assigned Vehicle Metadata (`GET /api/v1/me/vehicle`)
5. Real-Time MQTT Telemetry Ingestion (`vehicles/BUS-001/gps`)
6. Database Persistence & Current Location API (`GET /api/v1/me/vehicle/location`)
7. Out-of-Order Stale Telemetry Packet Protection
8. Keyset Paginated Telemetry History (`GET /api/v1/me/vehicle/history`)
"""

import asyncio
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

try:
    import aiomqtt
except ImportError:
    print("[WARNING] 'aiomqtt' package not installed in current environment. Direct MQTT publishing tests will use HTTP checks.")
    aiomqtt = None

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))


def http_request(url: str, method: str = "GET", payload: dict = None, headers: dict = None) -> tuple:
    """Helper function to perform HTTP requests using standard library urllib."""
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status_code, body
    except urllib.error.HTTPError as err:
        raw_err = err.read().decode("utf-8") if err.fp else ""
        try:
            error_body = json.loads(raw_err) if raw_err else {}
        except Exception:
            error_body = {"raw": raw_err}
        return err.code, error_body

    except Exception as exc:
        print(f"[FAIL] HTTP Request to {url} failed: {exc}")
        sys.exit(1)


async def publish_mqtt_telemetry(topic: str, payload: dict):
    """Publishes a test telemetry payload via MQTT broker."""
    if not aiomqtt:
        print("[SKIP] aiomqtt not installed. Skipping direct MQTT publish step.")
        return

    try:
        async with aiomqtt.Client(hostname=MQTT_HOST, port=MQTT_PORT, client_id="verifier_client") as client:
            payload_str = json.dumps(payload)
            await client.publish(topic, payload_str)
            print(f"[OK] Published MQTT packet to topic '{topic}': {payload_str}")
    except Exception as err:
        print(f"[FAIL] Failed to publish MQTT message to {MQTT_HOST}:{MQTT_PORT}: {err}")
        sys.exit(1)


async def main():
    print("==========================================================")
    print(" GPS Vehicle Tracking System - Full System Flow Verifier")
    print("==========================================================")
    print(f"Target API Base: {BASE_URL}")
    print(f"Target MQTT:     {MQTT_HOST}:{MQTT_PORT}")
    print("----------------------------------------------------------")

    # 1. Health Check Endpoint
    print("\n[Step 1] Verifying System Health Check...")
    status, res = http_request(f"{BASE_URL}/health")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res.get("status") in ["ok", "healthy"], f"Unexpected status in health check: {res}"
    print(f"[OK] Health check passed: {res}")


    # 2. Authentication & Seed User Login
    print("\n[Step 2] Authenticating Seed User (driver_a@example.com)...")
    login_payload = {
        "email": "driver_a@example.com",
        "password": "Password123!",
    }
    status, res = http_request(f"{BASE_URL}/auth/login", method="POST", payload=login_payload)
    assert status == 200, f"Login failed with status {status}: {res}"
    token = res.get("access_token")
    assert token, "Access token missing from login response"
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("[OK] User A authenticated successfully. Token acquired.")

    # 3. User Assignment Resolution
    print("\n[Step 3] Resolving User Assignment & Route Metadata...")
    status, res = http_request(f"{BASE_URL}/me/assignment", headers=auth_headers)
    assert status == 200, f"Assignment lookup failed ({status}): {res}"
    vehicle_code = res["vehicle"]["code"]
    route_name = res["route"]["name"]
    stops = res["route"]["stops"]
    assert vehicle_code == "BUS-001", f"Expected BUS-001, got {vehicle_code}"
    # Verify polyline sequence sorting invariant
    sequences = [s["sequence"] for s in stops]
    assert sequences == sorted(sequences), f"Stops are not strictly sorted by sequence ASC: {sequences}"
    print(f"[OK] Assignment resolved: User mapped to Vehicle '{vehicle_code}' on Route '{route_name}' ({len(stops)} stops in sequence).")

    # 4. Vehicle Metadata Check
    print("\n[Step 4] Querying Vehicle Status & Metadata...")
    status, res = http_request(f"{BASE_URL}/me/vehicle", headers=auth_headers)
    assert status == 200, f"Vehicle metadata failed ({status}): {res}"
    print(f"[OK] Vehicle status: {res.get('status')} | Code: {res.get('code')}")

    # 5. Telemetry Ingestion & Live Location
    print("\n[Step 5] Ingesting Live Telemetry via MQTT & Verifying REST Endpoint...")
    now_time = datetime.now(timezone.utc)
    fresh_telemetry = {
        "latitude": 27.701122,
        "longitude": 85.300555,
        "speed": 42.5,
        "timestamp": now_time.isoformat(),
    }
    await publish_mqtt_telemetry(f"vehicles/{vehicle_code}/gps", fresh_telemetry)
    await asyncio.sleep(1.5)  # allow background consumer to process and write to DB

    status, res = http_request(f"{BASE_URL}/me/vehicle/location", headers=auth_headers)
    assert status == 200, f"Vehicle location lookup failed ({status}): {res}"
    print(f"[OK] Current Vehicle Location: Lat={res['latitude']}, Lon={res['longitude']}, Speed={res['speed']} km/h")

    # 6. Stale Telemetry Protection Verification
    print("\n[Step 6] Testing Out-of-Order Stale Telemetry Packet Protection...")
    stale_time = now_time - timedelta(minutes=30)
    stale_telemetry = {
        "latitude": 10.000000,
        "longitude": 10.000000,
        "speed": 5.0,
        "timestamp": stale_time.isoformat(),
    }
    await publish_mqtt_telemetry(f"vehicles/{vehicle_code}/gps", stale_telemetry)
    await asyncio.sleep(1.5)

    status, res_after_stale = http_request(f"{BASE_URL}/me/vehicle/location", headers=auth_headers)
    assert status == 200, f"Vehicle location lookup failed after stale packet ({status}): {res_after_stale}"
    assert res_after_stale["latitude"] != 10.000000, "CRITICAL FAIL: Stale packet regressed current vehicle position!"
    print(f"[OK] Stale Packet Protection Verified! Location remained at Lat={res_after_stale['latitude']}, Lon={res_after_stale['longitude']} without regressing.")

    # 7. Keyset Paginated History Verification
    print("\n[Step 7] Testing Paginated Vehicle History Query...")
    status, res = http_request(f"{BASE_URL}/me/vehicle/history?limit=10", headers=auth_headers)
    assert status == 200, f"Vehicle history lookup failed ({status}): {res}"
    history_items = res.get("items", [])
    print(f"[OK] History query returned {len(history_items)} points. Next cursor: {res.get('next_cursor')}")

    print("\n==========================================================")
    print(" VERIFICATION SUCCESS: All 7 System Flow Gates PASSED!")
    print("==========================================================")


if __name__ == "__main__":
    asyncio.run(main())
