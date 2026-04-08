"""Final validation for submission."""
import requests

URL = "https://rahul2124-sql-arena.hf.space"

print("=" * 50)
print("SQL Arena - Final Validation")
print("=" * 50)

# Test 1: Reset endpoint
print("\n[1] Testing /reset...")
try:
    r = requests.post(f"{URL}/reset", json={}, timeout=30)
    print(f"    Status: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 2: Step endpoint
print("\n[2] Testing /step...")
try:
    r = requests.post(f"{URL}/step", json={"sql_query": "SELECT * FROM employees"}, timeout=30)
    data = r.json()
    print(f"    Status: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
    print(f"    Reward: {data.get('reward', 'N/A')}")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 3: State endpoint
print("\n[3] Testing /state...")
try:
    r = requests.get(f"{URL}/state", timeout=30)
    print(f"    Status: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 4: Tasks endpoint
print("\n[4] Testing /tasks...")
try:
    r = requests.get(f"{URL}/tasks", timeout=30)
    tasks = r.json()["tasks"]
    total = sum(len(v) for v in tasks.values())
    print(f"    Status: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
    print(f"    Tasks: {total} across {len(tasks)} difficulties")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 5: Scores vary
print("\n[5] Testing grader produces varying scores...")
try:
    requests.post(f"{URL}/reset", json={"task_id": "easy_001"}, timeout=30)
    r1 = requests.post(f"{URL}/step", json={
        "sql_query": "SELECT name, salary FROM employees WHERE is_active = 1 AND salary > 80000 ORDER BY salary DESC"
    }, timeout=30)
    score1 = r1.json().get("info", {}).get("score", 0)

    requests.post(f"{URL}/reset", json={"task_id": "easy_001"}, timeout=30)
    r2 = requests.post(f"{URL}/step", json={"sql_query": "INVALID SQL"}, timeout=30)
    score2 = r2.json().get("info", {}).get("score", 0)

    if score1 != score2:
        print(f"    PASS: Scores vary (correct={score1:.2f}, wrong={score2:.2f})")
    else:
        print(f"    FAIL: Same score")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 6: All 3 difficulties
print("\n[6] Testing all 3 difficulty levels...")
for diff in ["basic_select", "join_aggregate", "complex_analysis"]:
    try:
        r = requests.post(f"{URL}/reset", json={"difficulty": diff}, timeout=30)
        print(f"    {diff}: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"    {diff}: FAIL - {e}")

print("\n" + "=" * 50)
print("VALIDATION COMPLETE!")
print(f"Submit this URL: {URL}")
print("=" * 50)