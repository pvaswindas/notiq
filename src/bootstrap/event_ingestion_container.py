from dataclasses import dataclass

from src.application.use_cases.process_event_use_case import ProcessEventUseCase
from src.infrastructure.queue.in_memory_queue import InMemoryEventQueue
from src.infrastructure.repositories.in_memory_channel_repository import InMemoryChannelRepository


@dataclass(slots=True)
class EventIngestionContainer:
    process_event_use_case: ProcessEventUseCase
    event_queue: InMemoryEventQueue


class EventIngestionContainerFactory:
    def build(self) -> EventIngestionContainer:
        channel_repository = InMemoryChannelRepository(channels=[])
        event_queue = InMemoryEventQueue()
        process_event_use_case = ProcessEventUseCase(
            channel_repository=channel_repository,
            event_queue=event_queue,
        )

        return EventIngestionContainer(
            process_event_use_case=process_event_use_case,
            event_queue=event_queue,
        )
