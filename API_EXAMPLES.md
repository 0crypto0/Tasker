# Tasker API Examples

This document provides curl command examples for all Tasker API endpoints with sample responses.

## Table of Contents

- [Health Check](#health-check)
- [Sum Task](#sum-task)
- [Weather Task](#weather-task)
- [ChatGPT Task](#chatgpt-task)
- [Get Task Status](#get-task-status)

---

## Health Check

Check if the API is running and healthy.

### Request

```bash
curl -s http://127.0.0.1:8000/health | jq .
```

### Response

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Sum Task

Calculate the sum of two numbers.

### Submit Task

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": 5, "b": 3}}'
```

### Submit Response

```json
{
  "task_uuid": "8edec69d-9219-4ae0-afa9-b73e003d28a6",
  "message": "Task submitted successfully"
}
```

### Get Task Output

```bash
curl "http://127.0.0.1:8000/get-task-output?task_uuid=8edec69d-9219-4ae0-afa9-b73e003d28a6"
```

### Task Output Response

```json
{
  "task_uuid": "8edec69d-9219-4ae0-afa9-b73e003d28a6",
  "task_name": "sum",
  "status": "completed",
  "task_output": {
    "a": 5,
    "b": 3,
    "result": 8,
    "operation": "sum"
  },
  "error_message": null,
  "created_at": "2026-01-04T12:06:52.502689",
  "completed_at": "2026-01-04T12:06:52.643634"
}
```

### Additional Examples

**Sum with floats:**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": 10.5, "b": 4.3}}'
```

**Sum with negative numbers:**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": -10, "b": 25}}'
```

---

## Weather Task

Fetch current weather data for a city using the Open-Meteo API (no API key required).

### Submit Task (Metric Units)

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "London", "units": "metric"}}'
```

### Submit Response

```json
{
  "task_uuid": "bdc4fcec-e3b7-4a8e-89ea-905bd74e13b4",
  "message": "Task submitted successfully"
}
```

### Get Task Output

```bash
curl "http://127.0.0.1:8000/get-task-output?task_uuid=bdc4fcec-e3b7-4a8e-89ea-905bd74e13b4"
```

### Task Output Response

```json
{
  "task_uuid": "bdc4fcec-e3b7-4a8e-89ea-905bd74e13b4",
  "task_name": "weather",
  "status": "completed",
  "task_output": {
    "city": "London",
    "wind": {
      "speed": 9.5,
      "direction": 259
    },
    "clouds": 0,
    "country": "GB",
    "weather": {
      "icon": "☀️",
      "main": "Clear",
      "description": "Clear sky"
    },
    "humidity": 72,
    "pressure": 1013.9,
    "timezone": "Europe/London",
    "visibility": null,
    "coordinates": {
      "latitude": 51.50853,
      "longitude": -0.12574
    },
    "temperature": {
      "max": null,
      "min": null,
      "units": "metric",
      "current": 0.0,
      "feels_like": -4.1
    }
  },
  "error_message": null,
  "created_at": "2026-01-04T12:07:05.159630",
  "completed_at": "2026-01-04T12:07:05.898285"
}
```

### Additional Examples

**Weather with Imperial Units (Fahrenheit):**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "New York", "units": "imperial"}}'
```

**Weather with Kelvin Units:**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "Tokyo", "units": "kelvin"}}'
```

**Weather for Different Cities:**

```bash
# Paris
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "Paris"}}'

# Sydney
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "Sydney"}}'

# Berlin
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "Berlin"}}'
```

---

## ChatGPT Task

Query OpenAI's ChatGPT API (requires `OPENAI_API_KEY` environment variable).

### Submit Task

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "chatgpt", "task_parameters": {"prompt": "What is 2+2?"}}'
```

### Submit Response

```json
{
  "task_uuid": "1833c9bb-ac7f-4a48-9d7f-31cfc8b9bf94",
  "message": "Task submitted successfully"
}
```

### Get Task Output

```bash
curl "http://127.0.0.1:8000/get-task-output?task_uuid=1833c9bb-ac7f-4a48-9d7f-31cfc8b9bf94"
```

### Task Output Response

```json
{
  "task_uuid": "1833c9bb-ac7f-4a48-9d7f-31cfc8b9bf94",
  "task_name": "chatgpt",
  "status": "completed",
  "task_output": {
    "model": "gpt-3.5-turbo",
    "usage": {
      "total_tokens": 21,
      "prompt_tokens": 14,
      "completion_tokens": 7
    },
    "prompt": "What is 2+2?",
    "response": "2 + 2 = 4"
  },
  "error_message": null,
  "created_at": "2026-01-04T12:07:20.791994",
  "completed_at": "2026-01-04T12:07:22.150392"
}
```

### Additional Examples

**ChatGPT with Custom Parameters:**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "chatgpt",
    "task_parameters": {
      "prompt": "Explain quantum computing in simple terms",
      "max_tokens": 500,
      "temperature": 0.7
    }
  }'
```

**ChatGPT for Code Generation:**

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "chatgpt",
    "task_parameters": {
      "prompt": "Write a Python function to calculate factorial"
    }
  }'
```

---

## Get Task Status

Get just the status of a task (without the full output).

### Request

```bash
curl "http://127.0.0.1:8000/tasks/{task_uuid}/status"
```

### Example

```bash
curl "http://127.0.0.1:8000/tasks/bdc4fcec-e3b7-4a8e-89ea-905bd74e13b4/status"
```

### Response

```json
{
  "task_uuid": "bdc4fcec-e3b7-4a8e-89ea-905bd74e13b4",
  "status": "completed"
}
```

### Possible Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task is queued but not yet started |
| `running` | Task is currently being processed |
| `completed` | Task finished successfully |
| `failed` | Task failed with an error |

---

## Error Responses

### Invalid Task Name

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "invalid", "task_parameters": {}}'
```

**Response (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "task_name"],
      "msg": "Input should be 'sum', 'chatgpt' or 'weather'",
      "input": "invalid",
      "ctx": {
        "expected": "'sum', 'chatgpt' or 'weather'"
      }
    }
  ]
}
```

### Missing Required Parameter

```bash
curl -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": 5}}'
```

**Response (400 Bad Request):**

```json
{
  "detail": "Parameter 'b' is required for sum task"
}
```

### Task Not Found

```bash
curl "http://127.0.0.1:8000/get-task-output?task_uuid=00000000-0000-0000-0000-000000000000"
```

**Response (404 Not Found):**

```json
{
  "detail": "Task not found"
}
```

### Invalid UUID Format

```bash
curl "http://127.0.0.1:8000/get-task-output?task_uuid=not-a-valid-uuid"
```

**Response (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["query", "task_uuid"],
      "msg": "Input should be a valid UUID",
      "input": "not-a-valid-uuid"
    }
  ]
}
```

---

## Polling for Task Completion

Since tasks are processed asynchronously, you may need to poll for completion:

```bash
#!/bin/bash

# Submit a task
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "weather", "task_parameters": {"city": "London"}}')

TASK_UUID=$(echo $RESPONSE | jq -r '.task_uuid')
echo "Task submitted: $TASK_UUID"

# Poll for completion
while true; do
  STATUS=$(curl -s "http://127.0.0.1:8000/tasks/$TASK_UUID/status" | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 1
done

# Get the final result
curl -s "http://127.0.0.1:8000/get-task-output?task_uuid=$TASK_UUID" | jq .
```

---

## Docker Usage

If running with Docker Compose, the API is available at the same endpoints:

```bash
# Start all services
docker-compose up -d

# Test the API
curl http://localhost:8000/health

# Submit a task
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "task_parameters": {"a": 10, "b": 20}}'
```

---

## Metrics Endpoint

Prometheus metrics are available at `/metrics`:

```bash
curl http://127.0.0.1:8000/metrics
```

This returns Prometheus-formatted metrics including:
- `tasker_tasks_submitted_total` - Total tasks submitted by type
- `tasker_tasks_by_status` - Current tasks by status
- `tasker_task_execution_duration_seconds` - Task execution times
- `tasker_external_api_requests_total` - External API calls

