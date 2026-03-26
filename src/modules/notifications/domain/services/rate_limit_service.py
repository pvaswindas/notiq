from datetime import datetime, timedelta, timezone


class RateLimitService:
    """
    Purpose:
    - Provide domain-level fixed-window rate limiting policy.

    Responsibilities:
    - Enforce a per-workspace event budget in a rolling window.

    Constraints:
    - No I/O or infrastructure dependencies.
    """

    def __init__(self, max_events_per_minute: int = 120) -> None:
        self._max_events_per_minute = max_events_per_minute
        self._state: dict[str, tuple[datetime, int]] = {}

    def allow_workspace(self, workspace_id: str) -> bool:
        now = datetime.now(timezone.utc)
        window_start, count = self._state.get(workspace_id, (now, 0))

        if now - window_start >= timedelta(minutes=1):
            window_start = now
            count = 0

        if count >= self._max_events_per_minute:
            self._state[workspace_id] = (window_start, count)
            return False

        self._state[workspace_id] = (window_start, count + 1)
        return True
