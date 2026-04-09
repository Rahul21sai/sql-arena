"""Tests for SQL Arena environment."""

import pytest
from src.sql_arena.environment import SQLArenaEnvironment
from src.sql_arena.models import SQLArenaAction
from src.sql_arena.tasks import list_tasks, TASK_BY_ID


class TestEnvironmentBasics:

    def setup_method(self):
        self.env = SQLArenaEnvironment()

    def teardown_method(self):
        self.env.close()

    def test_reset_returns_observation(self):
        result = self.env.reset(difficulty="basic_select", task_id="easy_001")
        assert result.observation is not None
        assert result.reward == 0.0
        assert result.done is False

    def test_step_with_correct_query(self):
        self.env.reset(difficulty="basic_select", task_id="easy_001")
        task = self.env.current_task
        action = SQLArenaAction(sql_query=task.expected_sql)
        result = self.env.step(action)
        assert result.reward > 0.0
        assert result.info.get("score", 0) >= 0.8

    def test_step_with_invalid_query(self):
        self.env.reset(difficulty="basic_select", task_id="easy_001")
        action = SQLArenaAction(sql_query="INVALID SQL QUERY")
        result = self.env.step(action)
        assert result.reward == 0.01  # Clamped to strictly > 0
        assert result.observation.error_message is not None

    def test_state_tracking(self):
        self.env.reset(difficulty="basic_select", task_id="easy_001")
        state = self.env.state()
        assert state.current_step == 0

        self.env.step(SQLArenaAction(sql_query="SELECT 1"))
        state = self.env.state()
        assert state.current_step == 1

    def test_episode_terminates(self):
        self.env.reset(difficulty="basic_select", task_id="easy_001")
        task = self.env.current_task
        for _ in range(task.max_steps + 1):
            if self.env.state().done:
                break
            self.env.step(SQLArenaAction(sql_query="SELECT 1"))
        assert self.env.state().done is True


class TestAllDifficulties:

    def setup_method(self):
        self.env = SQLArenaEnvironment()

    def teardown_method(self):
        self.env.close()

    def test_easy(self):
        result = self.env.reset(difficulty="basic_select")
        assert result.observation.difficulty == "basic_select"

    def test_medium(self):
        result = self.env.reset(difficulty="join_aggregate")
        assert result.observation.difficulty == "join_aggregate"

    def test_hard(self):
        result = self.env.reset(difficulty="complex_analysis")
        assert result.observation.difficulty == "complex_analysis"


class TestGrading:

    def setup_method(self):
        self.env = SQLArenaEnvironment()

    def teardown_method(self):
        self.env.close()

    def test_scores_in_range(self):
        for task_id, task in TASK_BY_ID.items():
            self.env.reset(difficulty=task.difficulty, task_id=task_id)
            action = SQLArenaAction(sql_query=task.expected_sql)
            result = self.env.step(action)
            assert 0.0 <= result.reward <= 1.0
            assert 0.0 <= result.info.get("score", 0) <= 1.0
            self.env.reset(difficulty=task.difficulty, task_id=task_id)

    def test_varying_scores(self):
        scores = set()
        queries = [
            "SELECT name, salary FROM employees WHERE is_active = 1 AND salary > 80000 ORDER BY salary DESC",
            "SELECT * FROM employees",
            "INVALID",
            "SELECT name FROM employees",
        ]
        for q in queries:
            self.env.reset(difficulty="basic_select", task_id="easy_001")
            result = self.env.step(SQLArenaAction(sql_query=q))
            scores.add(round(result.info.get("score", 0), 2))
        assert len(scores) > 1, "Grader always returns the same score!"


class TestTaskRegistry:

    def test_list_tasks(self):
        tasks = list_tasks()
        assert "basic_select" in tasks
        assert "join_aggregate" in tasks
        assert "complex_analysis" in tasks

    def test_minimum_3_tasks(self):
        tasks = list_tasks()
        for difficulty, task_ids in tasks.items():
            assert len(task_ids) >= 3, f"{difficulty} has fewer than 3 tasks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])