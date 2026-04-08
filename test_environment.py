from src.sql_arena.environment import SQLArenaEnvironment
from src.sql_arena.models import SQLArenaAction

env = SQLArenaEnvironment()

# Test reset
print("=== Testing reset() ===")
result = env.reset(difficulty="basic_select", task_id="easy_001")
print(f"Question: {result.observation.question[:80]}...")
print(f"Difficulty: {result.observation.difficulty}")
print(f"Attempts: {result.observation.attempts_remaining}")
print(f"Done: {result.done}")

# Test step with good query
print("\n=== Testing step() with correct SQL ===")
action = SQLArenaAction(sql_query="SELECT name, salary FROM employees WHERE is_active = 1 AND salary > 80000 ORDER BY salary DESC")
result = env.step(action)
print(f"Reward: {result.reward}")
print(f"Score: {result.info.get('score', 0)}")
print(f"Done: {result.done}")
print(f"Query Result:\n{result.observation.query_result}")

# Test state
print("\n=== Testing state() ===")
state = env.state()
print(f"Step: {state.current_step}")
print(f"Best score: {state.best_score}")
print(f"Done: {state.done}")

# Test with bad query
print("\n=== Testing step() with bad SQL ===")
env.reset(difficulty="basic_select", task_id="easy_001")
bad_action = SQLArenaAction(sql_query="SELECT * FROM nonexistent_table")
result2 = env.step(bad_action)
print(f"Reward: {result2.reward}")
print(f"Error: {result2.observation.error_message}")

env.close()
print("\nEnvironment tests passed!")