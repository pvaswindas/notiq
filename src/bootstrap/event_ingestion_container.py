from dataclasses import dataclass

from src.application.use_cases.process_event_use_case import ProcessEventUseCase
from src.infrastructure.queue.celery_queue import CeleryEventQueue
from src.infrastructure.repositories.in_memory_channel_repository import InMemoryChannelRepository


@dataclass(slots=True)
class EventIngestionContainer:
    process_event_use_case: ProcessEventUseCase
    event_queue: CeleryEventQueue


class EventIngestionContainerFactory:
    def build(self) -> EventIngestionContainer:
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
