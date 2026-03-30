from dataclasses import dataclass

from src.application.use_cases.process_event_use_case import ProcessEventUseCase
from src.infrastructure.queue.celery_queue import CeleryEventQueue
from src.infrastructure.repositories.in_memory_channel_repository import InMemoryChannelRepository


@dataclass(slots=True)
class EventIngestionContainer:
    """Dependency bundle for the legacy `/events` ingestion runtime path.

    Architectural role:
    - Keeps compatibility-path object graph explicit and testable.
    """

    process_event_use_case: ProcessEventUseCase
    event_queue: CeleryEventQueue


class EventIngestionContainerFactory:
    """Composition root for legacy event-ingestion dependencies."""

    def build(self) -> EventIngestionContainer:
        """Create a fully wired container for legacy event ingestion.

        Returns:
            EventIngestionContainer: Use case and queue adapter wiring.

        Important:
        - Uses in-memory channel repository placeholder by default.
        - Intended for compatibility flow; primary feature work should target
          modular notifications container wiring.
        """

        channel_repository = InMemoryChannelRepository(channels=[])
        event_queue = CeleryEventQueue()
        process_event_use_case = ProcessEventUseCase(
            channel_repository=channel_repository,
            event_queue=event_queue,
        )

        return EventIngestionContainer(
            process_event_use_case=process_event_use_case,
            event_queue=event_queue,
        )
