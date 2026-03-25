from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class QueuedDeliveryResultDTO:
    """
    Purpose:
    - Return enqueue summary from notification submission.

    Responsibilities:
    - Expose counts for observability and client feedback.

    Inputs:
    - enqueued_jobs: int
    - skipped_duplicates: int

    Outputs:
    - QueuedDeliveryResultDTO

    Constraints:
    - Counts must be non-negative.
    """

    enqueued_jobs: int
    skipped_duplicates: int
