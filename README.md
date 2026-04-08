---
title: SQL Arena
emoji: 🏟️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# SQL Arena - OpenEnv Environment

An interactive SQL query challenge environment where AI agents learn to write SQL
by iteratively querying databases and receiving execution feedback with partial credit scoring.

## Real-World Utility

Text-to-SQL is one of the most valuable capabilities for AI agents:
- Used by data analysts, business users, and developers daily
- Evaluates reasoning, schema understanding, and query composition
- Directly applicable to production AI assistants and copilots

## Tasks

| Task | Difficulty | Description | Max Steps |
|------|-----------|-------------|-----------|
| basic_select | Easy | SELECT, WHERE, ORDER BY | 5 |
| join_aggregate | Medium | JOINs, GROUP BY, HAVING | 7 |
| complex_analysis | Hard | CTEs, window functions | 10 |

Each difficulty has 3 unique problems with deterministic grading.

## Action Space

The agent sends a SQL query each step:

{"sql_query": "SELECT name, salary FROM employees WHERE salary > 80000"}

## Observation Space

The agent receives back:

- schema_description: Database schema text
- question: Natural language question to answer
- query_result: Result table from last query
- error_message: Error if query failed
- feedback: Scoring feedback with hints
- expected_columns: Expected column names
- attempts_remaining: Steps left
- difficulty: Task difficulty level
- task_id: Problem identifier

## Reward Function (0.0 to 1.0)

| Component | Weight | Description |
|-----------|--------|-------------|
| Execution | 0.10 | Query runs without error |
| Columns | 0.20 | Correct column names |
| Row Count | 0.20 | Correct number of rows |
| Values | 0.50 | Correct data values |

## Setup

pip install -r requirements.txt

## Run Server

uvicorn src.sql_arena.server:app --host 0.0.0.0 --port 7860

## Run Inference

set HF_TOKEN=your_token
python inference.py

## Docker

docker build -t sql-arena .
docker run -p 7860:7860 sql-arena

## Run Tests

pytest tests/ -v

## Project Structure

sql_arena/
- openenv.yaml (Environment metadata)
- Dockerfile (Container deployment)
- inference.py (Baseline inference script)
- src/sql_arena/
  - models.py (Typed Pydantic models)
  - environment.py (Core environment logic)
  - tasks.py (9 SQL challenges)
  - graders.py (Partial credit scoring)
  - database.py (SQLite management)
  - server.py (FastAPI server)
- tests/
  - test_env.py (Test suite)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /reset | Start new episode |
| POST | /step | Submit SQL query |
| GET | /state | Get current state |
| GET | /tasks | List available tasks |
| WS | /ws | WebSocket sessions |

## License

MIT