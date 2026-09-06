import asyncio
import re
from typing import Optional
import aiomqtt

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.services.telemetry_ingestion_service import TelemetryIngestionService

# Regex matching topic pattern: vehicles/{vehicle_code}/gps
TOPIC_REGEX = re.compile(r"^vehicles/([^/]+)/gps$")


class MqttConsumerManager:
    """
    Asynchronous MQTT consumer manager subscribing to vehicle telemetry topics
    and dispatching incoming payloads to TelemetryIngestionService.
    """
    def __init__(self):
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.client_id = settings.MQTT_CLIENT_ID
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def _consume_loop(self) -> None:
        """
        Main asynchronous consumer loop connecting to MQTT broker and processing messages.
        """
        logger.info(f"Connecting MQTT Consumer to broker {self.host}:{self.port} (Client ID: {self.client_id})...")
        while self._running:
            try:
                async with aiomqtt.Client(
                    hostname=self.host,
                    port=self.port,
                    client_id=self.client_id,
                ) as client:
                    logger.info("Successfully connected to MQTT broker. Subscribing to topic 'vehicles/+/gps'...")
                    await client.subscribe("vehicles/+/gps")

                    async for message in client.messages:
                        if not self._running:
                            break

                        topic_str = str(message.topic)
                        match = TOPIC_REGEX.match(topic_str)
                        if not match:
                            logger.warning(f"MQTT message received on unexpected topic format: '{topic_str}'")
                            continue

                        vehicle_code = match.group(1)
                        payload_bytes = message.payload

                        async with AsyncSessionLocal() as session:
                            try:
                                ingestion_service = TelemetryIngestionService(session)
                                await ingestion_service.process_payload(vehicle_code, payload_bytes)
                            except Exception as err:
                                logger.error(f"Error processing telemetry for vehicle '{vehicle_code}': {err}")

            except aiomqtt.MqttError as err:
                if not self._running:
                    break
                logger.warning(f"MQTT broker connection error: {err}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as err:
                if not self._running:
                    break
                logger.error(f"Unexpected exception in MQTT consumer loop: {err}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    def start(self) -> None:
        """
        Starts the MQTT consumer background task.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("MQTT Consumer background task launched.")

    async def stop(self) -> None:
        """
        Stops the MQTT consumer background task gracefully.
        """
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MQTT Consumer background task stopped.")


mqtt_consumer_manager = MqttConsumerManager()
