"""
Пакет transport хранит конкретные реализации ResponsePublisher.
Сейчас есть RabbitMQ (FastStream). Легко добавить Kafka, RedisStreams...
"""
from tigro.transport.rabbit_bus import RabbitPublisher  # noqa: F401

__all__ = ("RabbitPublisher",)
