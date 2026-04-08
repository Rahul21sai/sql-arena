"""
FastAPI server for SQL Arena - OpenEnv compatible.
Exposes /reset, /step, /state endpoints via HTTP and WebSocket.
"""

import json
import uuid
import asyncio
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .environment import SQLArenaEnvironment, StepResult
from .models import SQLArenaAction, SQLArenaObservation, SQLArenaState


# =====================================================
# Request / Response Models
# =====================================================

class ResetRequest(BaseModel):
    difficulty: str = "basic_select"
    task_id: Optional[str] = None


class StepRequest(BaseModel):
    sql_query: str


class ResetResponse(BaseModel):
    observation: SQLArenaObservation
    reward: float
    done: bool
    info: dict = {}


class StepResponse(BaseModel):
    observation: SQLArenaObservation
    reward: float
    done: bool
    info: dict = {}


class StateResponse(BaseModel):
    state: SQLArenaState


class TaskListResponse(BaseModel):
    tasks: Dict


# =====================================================
# Session Manager
# =====================================================

class SessionManager:
    """Manages multiple concurrent environment instances."""

    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, SQLArenaEnvironment] = {}
        self.max_sessions = max_sessions
        self._lock = asyncio.Lock()

    async def create_session(self):
        async with self._lock:
            if len(self.sessions) >= self.max_sessions:
                oldest_key = next(iter(self.sessions))
                self.sessions[oldest_key].close()
                del self.sessions[oldest_key]
            session_id = str(uuid.uuid4())
            env = SQLArenaEnvironment()
            self.sessions[session_id] = env
            return session_id, env

    async def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    async def remove_session(self, session_id: str):
        async with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]

    async def cleanup_all(self):
        async with self._lock:
            for env in self.sessions.values():
                env.close()
            self.sessions.clear()


# =====================================================
# App Setup
# =====================================================

session_manager = SessionManager()
_default_env = SQLArenaEnvironment()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await session_manager.cleanup_all()
    _default_env.close()


app = FastAPI(
    title="SQL Arena - OpenEnv Environment",
    description="Interactive SQL query challenge environment for AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# HTTP Endpoints
# =====================================================

@app.get("/")
async def root():
    return {
        "name": "SQL Arena",
        "version": "1.0.0",
        "description": "Interactive SQL query challenge environment",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/ws"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/reset", response_model=ResetResponse)
async def reset(request: ResetRequest = ResetRequest()):
    try:
        result = _default_env.reset(
            difficulty=request.difficulty,
            task_id=request.task_id,
        )
        return ResetResponse(
            observation=result.observation,
            reward=result.reward,
            done=result.done,
            info=result.info,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    try:
        action = SQLArenaAction(sql_query=request.sql_query)
        result = _default_env.step(action)
        return StepResponse(
            observation=result.observation,
            reward=result.reward,
            done=result.done,
            info=result.info,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=StateResponse)
async def state():
    try:
        return StateResponse(state=_default_env.state())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks", response_model=TaskListResponse)
async def tasks():
    return TaskListResponse(tasks=_default_env.get_available_tasks())


# =====================================================
# WebSocket Endpoint
# =====================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id, env = await session_manager.create_session()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            method = message.get("method", "")
            params = message.get("params", {})
            msg_id = message.get("id", None)

            try:
                if method == "reset":
                    result = env.reset(
                        difficulty=params.get("difficulty", "basic_select"),
                        task_id=params.get("task_id"),
                    )
                    response = {
                        "id": msg_id,
                        "result": {
                            "observation": result.observation.model_dump(),
                            "reward": result.reward,
                            "done": result.done,
                            "info": result.info,
                        },
                    }
                elif method == "step":
                    action = SQLArenaAction(sql_query=params.get("sql_query", ""))
                    result = env.step(action)
                    response = {
                        "id": msg_id,
                        "result": {
                            "observation": result.observation.model_dump(),
                            "reward": result.reward,
                            "done": result.done,
                            "info": result.info,
                        },
                    }
                elif method == "state":
                    env_state = env.state()
                    response = {
                        "id": msg_id,
                        "result": {"state": env_state.model_dump()},
                    }
                elif method == "close":
                    response = {"id": msg_id, "result": {"status": "closed"}}
                    await websocket.send_text(json.dumps(response))
                    break
                else:
                    response = {"id": msg_id, "error": f"Unknown method: {method}"}

                await websocket.send_text(json.dumps(response))

            except Exception as e:
                error_response = {"id": msg_id, "error": str(e)}
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        pass
    finally:
        await session_manager.remove_session(session_id)


# =====================================================
# Entry point
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)