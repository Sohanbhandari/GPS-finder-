# GPS Telemetry Simulator

The GPS Telemetry Simulator generates reproducible, real-time telemetry updates for `BUS-001` (Route A) and `BUS-002` (Route B) and publishes them to the MQTT broker on topic `vehicles/{vehicle_code}/gps`.

---

## Command-Line Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--host` | string | `localhost` | MQTT broker hostname |
| `--port` | int | `1883` | MQTT broker port |
| `--interval` | float | `2.0` | Seconds delay between coordinate updates |
| `--speed` | float | `30.0` | Simulated vehicle speed in km/h |
| `--loops` | int | `1` | Number of loop cycles through route waypoints |
| `--inject-out-of-order` | flag | `false` | Injects stale historical packets to test out-of-order engine |
| `--dry-run` | flag | `false` | Prints telemetry payloads to stdout without connecting to broker |

---

## Usage Examples

### 1. Run Simulator (Connected to Mosquitto MQTT Broker)
```bash
python simulator/gps_simulator.py --interval 1.5 --loops 2
```

### 2. Run In Out-of-Order Engine Testing Mode
```bash
python simulator/gps_simulator.py --inject-out-of-order
```

### 3. Dry-Run Mode (No MQTT Broker Required)
```bash
python simulator/gps_simulator.py --dry-run --interval 0.5
```
