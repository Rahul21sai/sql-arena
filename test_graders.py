from src.sql_arena.database import DatabaseManager
from src.sql_arena.tasks import get_task
from src.sql_arena.graders import grade_result

# Get a task
task = get_task("basic_select", "easy_001")

# Setup database
db = DatabaseManager()
db.create_database(task.setup_sql)

# Test 1: Perfect query
print("=== Test 1: Perfect Query ===")
success, result, error = db.execute_query(task.expected_sql)
score, feedback = grade_result(task, success, result, error)
print(f"Score: {score}")
print(feedback)

# Test 2: Wrong query
print("\n=== Test 2: Wrong Query ===")
success2, result2, error2 = db.execute_query("SELECT * FROM employees")
score2, feedback2 = grade_result(task, success2, result2, error2)
print(f"Score: {score2}")
print(feedback2)

# Test 3: Broken query
print("\n=== Test 3: Broken Query ===")
success3, result3, error3 = db.execute_query("INVALID SQL")
score3, feedback3 = grade_result(task, success3, result3, error3)
print(f"Score: {score3}")
print(feedback3)

# Verify scores are different
print(f"\nScores: {score}, {score2}, {score3}")
assert score > score2 > score3, "Scores should decrease!"
print("All grader tests passed!")

db.close()