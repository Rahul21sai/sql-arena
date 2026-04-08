"""
Core SQL Arena Environment.
Implements the OpenEnv step()/reset()/state() interface.
"""

from typing import Optional, Dict, Any, List
from .models import SQLArenaAction, SQLArenaObservation, SQLArenaState
from .database import DatabaseManager
from .tasks import SQLTask, get_task, list_tasks, TASK_BY_ID
from .graders import grade_result, generate_hint


class StepResult:
    """Result of a single environment step."""

    def __init__(
        self,
        observation: SQLArenaObservation,
        reward: float,
        done: bool,
        info: Optional[Dict[str, Any]] = None,
    ):
        self.observation = observation
        self.reward = reward
        self.done = done
        self.info = info or {}


class SQLArenaEnvironment:
    """
    SQL Arena: An interactive SQL query challenge environment.

    The agent receives a database schema and a natural language question,
    then iteratively writes SQL queries. The environment provides
    execution results, feedback, and partial credit scoring.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.current_task: Optional[SQLTask] = None
        self._state: Optional[SQLArenaState] = None
        self._last_observation: Optional[SQLArenaObservation] = None

    def reset(
        self,
        difficulty: str = "basic_select",
        task_id: Optional[str] = None,
    ) -> StepResult:
        """
        Reset the environment with a new task.

        Args:
            difficulty: 'basic_select', 'join_aggregate', or 'complex_analysis'
            task_id: Optional specific task ID

        Returns:
            StepResult with initial observation
        """
        # Get the task
        self.current_task = get_task(difficulty, task_id)
        task = self.current_task

        # Setup database
        self.db.create_database(task.setup_sql)

        # Initialize state
        self._state = SQLArenaState(
            task_id=task.task_id,
            difficulty=task.difficulty,
            current_step=0,
            max_steps=task.max_steps,
            best_score=0.0,
            total_reward=0.0,
            rewards_history=[],
            done=False,
            last_action_error=None,
        )

        # Create initial observation
        self._last_observation = SQLArenaObservation(
            schema_description=task.schema_description,
            question=task.question,
            query_result=None,
            error_message=None,
            feedback="Welcome to SQL Arena! Write a SQL query to answer the question above.",
            expected_columns=task.expected_columns,
            attempts_remaining=task.max_steps,
            difficulty=task.difficulty,
            task_id=task.task_id,
        )

        return StepResult(
            observation=self._last_observation,
            reward=0.0,
            done=False,
            info={"task_title": task.title},
        )

    def step(self, action: SQLArenaAction) -> StepResult:
        """
        Execute the agent's SQL query and return feedback.

        Args:
            action: SQLArenaAction containing the SQL query

        Returns:
            StepResult with observation, reward, and done flag
        """
        if self._state is None or self.current_task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        task = self.current_task
        state = self._state

        # Increment step counter
        state.current_step += 1

        # Execute the query
        success, result, error = self.db.execute_query(action.sql_query)

        # Grade the result
        score, feedback = grade_result(task, success, result, error)

        # Track best score
        state.best_score = max(state.best_score, score)

        # Calculate step reward
        if len(state.rewards_history) == 0:
            reward = score
        else:
            prev_best = max(state.rewards_history) if state.rewards_history else 0.0
            improvement = max(0, score - prev_best)
            reward = score * 0.5 + improvement * 0.5

        reward = round(min(max(reward, 0.0), 1.0), 4)
        state.rewards_history.append(reward)
        state.total_reward += reward

        # Add progressive hints
        hint = generate_hint(task, state.current_step, score)
        if hint and score < 1.0:
            feedback += f"\n\n{hint}"

        # Check if done
        attempts_remaining = task.max_steps - state.current_step
        is_perfect = score >= 1.0
        is_out_of_steps = attempts_remaining <= 0

        state.done = is_perfect or is_out_of_steps
        state.last_action_error = error

        # Format query result for observation
        query_result_str = None
        if success and result:
            query_result_str = self.db.format_result(result)

        # Build observation
        self._last_observation = SQLArenaObservation(
            schema_description=task.schema_description,
            question=task.question,
            query_result=query_result_str,
            error_message=error,
            feedback=feedback,
            expected_columns=task.expected_columns,
            attempts_remaining=attempts_remaining,
            difficulty=task.difficulty,
            task_id=task.task_id,
        )

        return StepResult(
            observation=self._last_observation,
            reward=reward,
            done=state.done,
            info={
                "score": score,
                "best_score": state.best_score,
                "step": state.current_step,
                "is_perfect": is_perfect,
            },
        )

    def state(self) -> SQLArenaState:
        """Return the current environment state."""
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._state

    def close(self) -> None:
        """Clean up resources."""
        self.db.close()
        self.current_task = None
        self._state = None
        self._last_observation = None

    def get_available_tasks(self) -> Dict:
        """Return all available tasks."""
        return list_tasks()