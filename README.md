# Tasker - Async Task Management Service

A production-ready asynchronous task management service built with FastAPI, Celery, PostgreSQL, and Redis. This service allows you to submit tasks for background execution and retrieve their results later.

## Features

- **Async Task Execution**: Submit tasks and get results later via UUID
- **Multiple Task Types**: Sum numbers, query ChatGPT, fetch weather data
- **Persistent Storage**: PostgreSQL with SQLAlchemy for task persistence
- **Caching**: Redis-based caching to reduce database load
- **Message Queue**: Celery with Redis broker for task distribution
- **Scalability**: Horizontally scalable worker architecture
- **Observability**: Prometheus metrics and structured JSON logging
- **Production Ready**: Docker Compose deployment, health checks, security best practices

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   API Client    │────▶│   FastAPI API   │────▶│   Redis Cache   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │◀────│  Redis Broker   │────▶│  Celery Workers │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  External APIs  │
                                                │ (OpenAI, Weather)│
                                                └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) OpenAI API key for ChatGPT task
- (Optional) OpenWeatherMap API key for weather task

### 1. Clone and Setup

```bash
cd Tasker
cp .env.example .env
# Edit .env and add your API keys if you want to use ChatGPT/Weather tasks
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 3. Run Database Migrations

```bash
docker-compose run --rm migrations
```

### 4. Access Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Prometheus | http://localhost:9090 |
| Flower (Celery Monitor) | http://localhost:5555 |

## API Endpoints

### POST /run-task

Submit a task for asynchronous execution.

**Request:**
```json
{
    "task_name": "sum",
    "task_parameters": {"a": 5, "b": 3}
}
```

**Response:**
```json
{
    "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Task submitted successfully"
}
```

### GET /get-task-output

Retrieve the output of a completed task.

**Request:**
```
GET /get-task-output?task_uuid=550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
    "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "task_name": "sum",
    "status": "completed",
    "task_output": {
        "operation": "sum",
        "a": 5,
        "b": 3,
        "result": 8
    },
    "error_message": null,
    "created_at": "2026-01-04T10:30:00Z",
    "completed_at": "2026-01-04T10:30:01Z"
}
```

### GET /tasks/{uuid}/status

Get the current status of a task.

### GET /health

Health check endpoint for load balancers.

### GET /metrics

Prometheus metrics endpoint.

## Supported Tasks

### 1. Sum Task

Sum two numbers.

```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "sum",
    "task_parameters": {"a": 10, "b": 20}
  }'
```

### 2. ChatGPT Task

Query OpenAI's ChatGPT API.

```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "chatgpt",
    "task_parameters": {
      "prompt": "Explain Python in one sentence",
      "model": "gpt-3.5-turbo",
      "max_tokens": 100
    }
  }'
```

**Parameters:**
- `prompt` (required): The question or prompt to send
- `model` (optional): OpenAI model to use (default: gpt-3.5-turbo)
- `max_tokens` (optional): Maximum response tokens (default: 1000)
- `temperature` (optional): Sampling temperature (default: 0.7)

### 3. Weather Task

Fetch current weather data from OpenWeatherMap.

```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "weather",
    "task_parameters": {
      "city": "London",
      "units": "metric"
    }
  }'
```

**Parameters:**
- `city` (required): City name to fetch weather for
- `units` (optional): Temperature units - metric, imperial, or kelvin (default: metric)

## Example Workflow

```bash
# 1. Submit a task
RESPONSE=$(curl -s -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": 100, "b": 200}}')

# Extract UUID
UUID=$(echo $RESPONSE | jq -r '.task_uuid')
echo "Task UUID: $UUID"

# 2. Check status (may be pending or running)
curl -s "http://localhost:8000/tasks/$UUID/status" | jq

# 3. Get result (when completed)
curl -s "http://localhost:8000/get-task-output?task_uuid=$UUID" | jq
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production/testing) | development |
| `DATABASE_URL` | PostgreSQL connection URL | postgresql+asyncpg://tasker:tasker@localhost:5432/tasker |
| `REDIS_URL` | Redis URL for caching | redis://localhost:6379/0 |
| `CELERY_BROKER_URL` | Celery broker URL | redis://localhost:6379/1 |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | redis://localhost:6379/2 |
| `OPENAI_API_KEY` | OpenAI API key for ChatGPT task | (empty) |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | (empty) |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_JSON` | Output logs as JSON | true |
| `CACHE_TTL_SECONDS` | Cache TTL in seconds | 3600 |

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start worker (in another terminal)
celery -A app.workers.worker worker --loglevel=info
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_api.py::TestRunTaskEndpoint -v
```

### Project Structure

```
tasker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Settings and configuration
│   ├── api/
│   │   ├── routes.py           # API endpoints
│   │   └── schemas.py          # Pydantic models
│   ├── core/
│   │   ├── celery_app.py       # Celery configuration
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── cache.py            # Redis cache layer
│   │   ├── metrics.py          # Prometheus metrics
│   │   └── logging.py          # Structured logging
│   ├── models/
│   │   └── task.py             # SQLAlchemy models
│   ├── tasks/
│   │   ├── base.py             # Base task class
│   │   ├── sum_task.py         # Sum task
│   │   ├── chatgpt_task.py     # ChatGPT task
│   │   └── weather_task.py     # Weather task
│   └── workers/
│       └── worker.py           # Celery worker entry
├── tests/
│   ├── conftest.py             # Test fixtures
│   ├── test_api.py             # API tests
│   ├── test_tasks.py           # Task tests
│   └── test_cache.py           # Cache tests
├── alembic/                    # Database migrations
├── prometheus/
│   └── prometheus.yml          # Prometheus config
├── Dockerfile
├── Dockerfile.worker
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Scaling

### Horizontal Scaling

Scale workers to handle more tasks:

```bash
# Scale to 4 worker replicas
docker-compose up -d --scale worker=4
```

### Queue-based Task Routing

Tasks are routed to different queues based on type:
- `default` queue: Sum tasks (fast, CPU-bound)
- `external_api` queue: ChatGPT and Weather tasks (I/O-bound, external API calls)

You can run dedicated workers for each queue:

```bash
# Worker for default queue
celery -A app.workers.worker worker -Q default --concurrency=4

# Worker for external API queue
celery -A app.workers.worker worker -Q external_api --concurrency=2
```

## Observability

### Metrics

Prometheus metrics are available at `/metrics`:

- `tasker_tasks_submitted_total` - Total tasks submitted by task name
- `tasker_task_executions_total` - Task executions by name and status
- `tasker_task_execution_duration_seconds` - Task execution duration histogram
- `tasker_cache_hits_total` - Cache hit count
- `tasker_cache_misses_total` - Cache miss count
- `tasker_external_api_requests_total` - External API requests by name and status

### Logging

Structured JSON logs with request correlation:

```json
{
    "timestamp": "2026-01-04T10:30:00Z",
    "level": "info",
    "app": "Tasker",
    "env": "production",
    "request_id": "abc-123",
    "event": "task_submitted",
    "task_name": "sum",
    "task_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Monitoring

- **Prometheus**: http://localhost:9090 - Metrics collection and querying
- **Flower**: http://localhost:5555 - Celery task monitoring

## Design Decisions

### Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| API Framework | FastAPI | Async support, automatic OpenAPI docs, type hints |
| Task Queue | Celery | Mature, battle-tested, excellent Python integration |
| Message Broker | Redis | Dual-purpose as broker + cache, reduces infrastructure |
| Database | PostgreSQL | JSONB support, reliable, excellent for structured data |
| ORM | SQLAlchemy 2.0 | Type-safe, async support, industry standard |
| Logging | structlog | Structured JSON logs, context binding, async-safe |
| Metrics | Prometheus | Industry standard, excellent ecosystem |

### Architecture Principles

1. **Decoupling**: API and workers are separate services communicating via message broker
2. **Persistence**: All task data stored in PostgreSQL for durability
3. **Caching**: Completed task outputs cached in Redis to reduce DB load
4. **Scalability**: Stateless workers can be scaled horizontally
5. **Observability**: Comprehensive metrics and structured logging

### Security Considerations

- Non-root Docker containers
- Input validation with Pydantic
- SQL injection prevention via ORM
- API keys stored in environment variables
- Health checks for service monitoring

## Troubleshooting

### Common Issues

**Tasks stuck in pending state:**
- Check if workers are running: `docker-compose ps`
- Check worker logs: `docker-compose logs worker`
- Verify Redis connection: `docker-compose logs redis`

**Database connection errors:**
- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Run migrations: `docker-compose run --rm migrations`

**API returning 500 errors:**
- Check API logs: `docker-compose logs api`
- Verify all dependencies are running

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart api

# Stop all services
docker-compose down

# Clean up volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

## License

MIT License
