"""
Typed Pydantic models for SQL Arena OpenEnv environment.

These models define the contract between the agent and environment:
- SQLArenaAction: What the agent sends (a SQL query)
- SQLArenaObservation: What the agent receives (schema, results, feedback)
- SQLArenaState: Internal environment state tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class SQLArenaAction(BaseModel):
    """
    Action model — the agent submits a SQL query.
    
    This is what the agent sends to the environment each step.
    The environment will execute this query against the SQLite database
    and return results + feedback.
    """
    sql_query: str = Field(
        ...,
        description="SQL query to execute against the database",
        examples=[
            "SELECT name, salary FROM employees WHERE salary > 50000",
            "SELECT department, COUNT(*) FROM employees GROUP BY department",
        ]
    )


class SQLArenaObservation(BaseModel):
    """
    Observation model — what the agent sees after each step.
    
    Contains the database schema, the question to answer,
    results from the last query, error messages, and feedback
    with partial credit information.
    """
    # Always present
    schema_description: str = Field(
        ...,
        description="Human-readable database schema (CREATE TABLE statements)"
    )
    question: str = Field(
        ...,
        description="Natural language question the agent must answer with SQL"
    )
    difficulty: str = Field(
        ...,
        description="Task difficulty level: basic_select, join_aggregate, or complex_analysis"
    )
    task_id: str = Field(
        ...,
        description="Unique identifier for this specific problem"
    )
    attempts_remaining: int = Field(
        ...,
        description="Number of query attempts the agent has left"
    )
    
    # Present after step() calls
    query_result: Optional[str] = Field(
        None,
        description="Formatted result table from the last executed query"
    )
    error_message: Optional[str] = Field(
        None,
        description="SQL error message if the query failed to execute"
    )
    feedback: Optional[str] = Field(
        None,
        description="Detailed feedback on query correctness with partial credit breakdown"
    )
    
    # Hints to help the agent
    expected_columns: Optional[List[str]] = Field(
        None,
        description="Expected column names in the correct result (hint)"
    )


class SQLArenaState(BaseModel):
    """
    Internal state model — tracks the episode progress.
    
    This is returned by the state() endpoint and contains
    all information about the current episode.
    """
    task_id: str = Field(..., description="Current task identifier")
    difficulty: str = Field(..., description="Current difficulty level")
    current_step: int = Field(0, description="Number of steps taken so far")
    max_steps: int = Field(5, description="Maximum steps allowed for this task")
    best_score: float = Field(0.0, description="Best score achieved so far in this episode")
    total_reward: float = Field(0.0, description="Sum of all rewards received")
    rewards_history: List[float] = Field(
        default_factory=list,
        description="List of rewards received at each step"
    )
    done: bool = Field(False, description="Whether the episode has ended")
    last_action_error: Optional[str] = Field(
        None,
        description="Error from the last action, if any"
    )