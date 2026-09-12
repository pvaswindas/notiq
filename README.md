# Notiq

**Notiq** is a multi-tenant notification infrastructure platform designed to ingest application events and manage asynchronous delivery across external notification providers (such as Telegram and Email).

It centralizes event routing, deduplication, rate limiting, retries, and dead-letter queue management, preventing product services from rebuilding custom notification pipelines.

---

## Tech Stack

- **Core & Runtime**: Python 3.10+ (Docker: 3.12-slim)
- **Web Framework**: FastAPI, Uvicorn
- **Database & Persistence**: PostgreSQL 16+, SQLAlchemy 2.0 (AsyncIO), asyncpg, Alembic
- **Cache & Rate Limiting**: Redis 7+, `redis-py`
- **Validation & Settings**: Pydantic v2, Pydantic-Settings
- **HTTP Client**: HTTPX
- **Authentication**: PyJWT, Bcrypt
- **Testing**: pytest, pytest-asyncio, Factory Boy

---

## Architecture Overview

Notiq is structured as a **Modular Monolith** using **Hexagonal Architecture (Ports and Adapters)**:

- `src/modules/notifications/domain`: Domain entities (`DeliveryJob`, `Channel`, `Workspace`, `DeadLetterJob`), value objects, and idempotency services.
- `src/modules/notifications/application`: Primary use cases (`SendNotificationUseCase`, `ProcessDeliveryJobUseCase`), DTOs, and safety services.
- `src/modules/notifications/ports`: Interface contracts for repositories, senders, and registries.
- `src/adapters`: Inbound HTTP controllers (notifications, workspaces, channels, admin RBAC, API keys, DLQ) and outbound provider integrations (Telegram, Email).
- `src/infrastructure`: PostgreSQL persistence adapters (using `FOR UPDATE SKIP LOCKED` for worker claiming) and Redis rate limiters.
- `src/bootstrap`: Application composition root (`ContainerFactory`), FastAPI app setup (`ApplicationFactory`), and worker runner.

---

## Quick-Start Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional for containerized run)

---

### Local Development Setup

1. **Clone the repository and set up a virtual environment**:
   ```bash
   git clone <repository-url>
   cd notiq
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the API Server**:
   ```bash
   python3 -m src.run
   ```

6. **Start the Background Notification Worker** (in a separate terminal window):
   ```bash
   python3 -m src.run_worker
   ```

---

### Running with Docker Compose

To launch the full environment (API, Worker, PostgreSQL, and Redis):

```bash
docker compose up --build
```

---

### Running Automated Tests

Run the test suite using Docker Compose:

```bash
# Run unit and integration tests inside isolated test containers
make test
```

Or run pytest directly locally:

```bash
pytest
```

---

### Quick Verification Example

Send a test notification event via cURL:

```bash
curl -X POST http://127.0.0.1:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-1",
    "event_id": "evt-1001",
    "event_name": "order.created",
    "payload": { "order_id": "ORD-42", "amount": 99.00 }
  }'
```

Inspect metric counters:

```bash
curl http://127.0.0.1:8000/metrics
```
