import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
import aiomqtt

# Configure Simulator Console Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gps_simulator")

# -------------------------------------------------------------------
# Route Waypoints Definition (Matching Development Seed Data)
# -------------------------------------------------------------------

ROUTE_A_STOPS: List[Tuple[str, float, float]] = [
    ("Central Station", 27.700769, 85.300140),
    ("Library Gate", 27.702500, 85.303100),
    ("Engineering Complex", 27.705000, 85.306000),
    ("Science Hub", 27.708000, 85.304000),
    ("Student Union", 27.706000, 85.301000),
    ("North Gate Terminal", 27.703000, 85.299000),
]

ROUTE_B_STOPS: List[Tuple[str, float, float]] = [
    ("South Station", 27.680000, 85.310000),
    ("Commercial Park", 27.683000, 85.314000),
    ("Tech Park Tower", 27.687000, 85.318000),
    ("Civic Center", 27.691000, 85.315000),
    ("South Plaza", 27.688000, 85.311000),
    ("Terminal B", 27.684000, 85.308000),
]


def interpolate_points(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float, steps: int = 5
) -> List[Tuple[float, float]]:
    """
    Generates linearly interpolated coordinate points between two waypoints.
    """
    points = []
    for i in range(steps):
        alpha = i / float(steps)
        lat = start_lat + alpha * (end_lat - start_lat)
        lon = start_lon + alpha * (end_lon - start_lon)
        points.append((round(lat, 6), round(lon, 6)))
    return points


def generate_route_coordinates(stops: List[Tuple[str, float, float]]) -> List[Tuple[float, float]]:
    """
    Generates a continuous array of GPS coordinates connecting sequential route stops.
    """
    coordinates = []
    for i in range(len(stops) - 1):
        s_name, s_lat, s_lon = stops[i]
        e_name, e_lat, e_lon = stops[i + 1]
        segment_points = interpolate_points(s_lat, s_lon, e_lat, e_lon, steps=5)
        coordinates.extend(segment_points)
    # Append final stop
    coordinates.append((stops[-1][1], stops[-1][2]))
    return coordinates


async def simulate_vehicle(
    vehicle_code: str,
    coordinates: List[Tuple[float, float]],
    client: Optional[aiomqtt.Client],
    interval: float,
    speed: float,
    loops: int,
    inject_out_of_order: bool,
    dry_run: bool,
) -> None:
    """
    Simulates real-time telemetry publishing for a vehicle along its route.
    If loops == 0, runs indefinitely.
    """
    topic = f"vehicles/{vehicle_code}/gps"
    logger.info(f"Starting simulation for vehicle '{vehicle_code}' on topic '{topic}' ({len(coordinates)} waypoints)...")

    current_loop = 0
    while loops == 0 or current_loop < loops:
        current_loop += 1
        loop_str = f"{current_loop}" if loops == 0 else f"{current_loop}/{loops}"
        logger.info(f"[{vehicle_code}] Beginning route cycle {loop_str}")

        for idx, (lat, lon) in enumerate(coordinates):
            now = datetime.now(timezone.utc)
            payload = {
                "latitude": lat,
                "longitude": lon,
                "speed": round(speed, 1),
                "timestamp": now.isoformat(),
            }
            payload_json = json.dumps(payload)

            if dry_run or client is None:
                logger.info(f"[DRY-RUN] Topic: {topic} | Payload: {payload_json}")
            else:
                await client.publish(topic, payload_json)
                logger.info(f"[PUBLISHED] Topic: {topic} | Lat: {lat}, Lon: {lon}, Speed: {speed} km/h")

            # Out-of-order packet injection test
            if inject_out_of_order and idx == 3:
                stale_time = now - timedelta(minutes=15)
                stale_payload = {
                    "latitude": round(lat - 0.005, 6),
                    "longitude": round(lon - 0.005, 6),
                    "speed": 5.0,
                    "timestamp": stale_time.isoformat(),
                }
                stale_json = json.dumps(stale_payload)
                if dry_run or client is None:
                    logger.info(f"[DRY-RUN STALE PACKET] Topic: {topic} | Payload: {stale_json}")
                else:
                    await client.publish(topic, stale_json)
                    logger.info(f"[PUBLISHED STALE PACKET] Injected older packet (timestamp: {stale_time.isoformat()})")

            await asyncio.sleep(interval)

    logger.info(f"Simulation completed for vehicle '{vehicle_code}'.")


async def main() -> None:
    default_host = os.getenv("MQTT_BROKER_HOST", "localhost")
    default_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    default_interval = float(os.getenv("SIMULATOR_INTERVAL", "2.0"))
    default_loops = int(os.getenv("SIMULATOR_LOOPS", "1"))

    parser = argparse.ArgumentParser(description="Deterministic GPS Telemetry Simulator")
    parser.add_argument("--host", type=str, default=default_host, help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=default_port, help="MQTT broker port")
    parser.add_argument("--interval", type=float, default=default_interval, help="Seconds between telemetry updates")
    parser.add_argument("--speed", type=float, default=30.0, help="Simulated speed in km/h")
    parser.add_argument("--loops", type=int, default=default_loops, help="Number of route loop iterations (0 for infinite)")
    parser.add_argument(
        "--inject-out-of-order",
        action="store_true",
        help="Inject stale historical packet to test out-of-order engine",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print telemetry without connecting to MQTT broker")
    args = parser.parse_args()

    coords_a = generate_route_coordinates(ROUTE_A_STOPS)
    coords_b = generate_route_coordinates(ROUTE_B_STOPS)

    if args.dry_run:
        logger.info("Running simulator in DRY-RUN mode (MQTT broker connection skipped)...")
        task_a = simulate_vehicle("BUS-001", coords_a, None, args.interval, args.speed, args.loops, args.inject_out_of_order, True)
        task_b = simulate_vehicle("BUS-002", coords_b, None, args.interval, args.speed, args.loops, args.inject_out_of_order, True)
        await asyncio.gather(task_a, task_b)
    else:
        logger.info(f"Connecting simulator to MQTT broker at {args.host}:{args.port}...")
        try:
            async with aiomqtt.Client(hostname=args.host, port=args.port, identifier="gps_simulator") as client:

                logger.info("Successfully connected to MQTT broker.")
                task_a = simulate_vehicle("BUS-001", coords_a, client, args.interval, args.speed, args.loops, args.inject_out_of_order, False)
                task_b = simulate_vehicle("BUS-002", coords_b, client, args.interval, args.speed, args.loops, args.inject_out_of_order, False)
                await asyncio.gather(task_a, task_b)
        except Exception as err:
            logger.error(f"Failed to connect to MQTT broker ({err}). Use --dry-run to test simulation without a running broker.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

