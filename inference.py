"""
Inference Script - SQL Arena OpenEnv Environment
Baseline agent that uses an LLM to solve SQL challenges.
"""

import os
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.sql_arena.environment import SQLArenaEnvironment
from src.sql_arena.models import SQLArenaAction

# =====================================================
# Configuration
# =====================================================

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

BENCHMARK = "sql_arena"
TEMPERATURE = 0.3
MAX_TOKENS = 500

TASKS = [
    {"difficulty": "basic_select", "task_id": "easy_001", "name": "basic_select", "max_steps": 5},
    {"difficulty": "join_aggregate", "task_id": "medium_001", "name": "join_aggregate", "max_steps": 7},
    {"difficulty": "complex_analysis", "task_id": "hard_001", "name": "complex_analysis", "max_steps": 10},
]


# =====================================================
# Logging (MANDATORY format)
# =====================================================

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_short = action.replace('\n', ' ').strip()[:100]
    print(
        f"[STEP] step={step} action={action_short} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# =====================================================
# LLM Agent
# =====================================================

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert SQL query writer. You are interacting with a SQL challenge environment.

    Each turn you receive: database schema, a question, previous query results, and feedback.
    Your goal: Write a SQL query that correctly answers the question.

    Rules:
    - Output ONLY the SQL query, nothing else
    - No explanations, no markdown, no code fences
    - Use standard SQLite syntax
    - Be precise with column names and table names
    - If your previous query had errors, fix them based on the feedback
""").strip()


def build_user_prompt(observation: dict, step: int, history: List[str]) -> str:
    parts = []
    parts.append(f"=== SQL Challenge (Step {step}) ===")
    parts.append(f"\nDifficulty: {observation.get('difficulty', 'unknown')}")
    parts.append(f"\n--- Database Schema ---\n{observation.get('schema_description', '')}")
    parts.append(f"\n--- Question ---\n{observation.get('question', '')}")

    if observation.get('expected_columns'):
        parts.append(f"\n--- Expected Columns ---\n{observation['expected_columns']}")
    if observation.get('query_result'):
        parts.append(f"\n--- Previous Query Result ---\n{observation['query_result']}")
    if observation.get('error_message'):
        parts.append(f"\n--- Error ---\n{observation['error_message']}")
    if observation.get('feedback'):
        parts.append(f"\n--- Feedback ---\n{observation['feedback']}")

    parts.append(f"\nAttempts remaining: {observation.get('attempts_remaining', 0)}")

    if history:
        parts.append("\n--- Previous Attempts ---")
        for h in history[-3:]:
            parts.append(h)

    parts.append("\nWrite your SQL query now:")
    return "\n".join(parts)


def get_sql_from_llm(client: OpenAI, observation: dict, step: int, history: List[str]) -> str:
    user_prompt = build_user_prompt(observation, step, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        raw = (completion.choices[0].message.content or "").strip()
        sql = raw
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()
        return sql if sql else "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] LLM request failed: {exc}", flush=True)
        return "SELECT 1"


# =====================================================
# Main Inference Loop
# =====================================================

def run_task(client: OpenAI, env: SQLArenaEnvironment, task_config: dict) -> float:
    difficulty = task_config["difficulty"]
    task_id = task_config["task_id"]
    task_name = task_config["name"]
    max_steps = task_config["max_steps"]

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    best_score = 0.0

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = env.reset(difficulty=difficulty, task_id=task_id)
        obs_dict = result.observation.model_dump()

        for step in range(1, max_steps + 1):
            if result.done:
                break

            sql_query = get_sql_from_llm(client, obs_dict, step, history)

            action = SQLArenaAction(sql_query=sql_query)
            result = env.step(action)

            obs_dict = result.observation.model_dump()
            reward = result.reward
            done = result.done
            error = obs_dict.get("error_message")

            rewards.append(reward)
            steps_taken = step
            best_score = max(best_score, result.info.get("score", 0.0))

            log_step(step=step, action=sql_query, reward=reward, done=done, error=error)

            history.append(
                f"Step {step}: {sql_query[:80]}... -> reward={reward:.2f}"
            )

            if done:
                break

        final_score = min(max(best_score, 0.0), 1.0)
        success = final_score >= 0.5

    except Exception as e:
        print(f"[DEBUG] Task {task_name} error: {e}", flush=True)
        final_score = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

    return final_score


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = SQLArenaEnvironment()

    all_scores = []

    for task_config in TASKS:
        print(f"\n{'='*60}", flush=True)
        print(f"Running task: {task_config['name']} ({task_config['difficulty']})", flush=True)
        print(f"{'='*60}", flush=True)

        score = run_task(client, env, task_config)
        all_scores.append(score)
        print(f"\nTask {task_config['name']} final score: {score:.2f}\n", flush=True)

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for tc, sc in zip(TASKS, all_scores):
        print(f"  {tc['name']:20s}: {sc:.2f}", flush=True)
    print(f"  {'Average':20s}: {avg_score:.2f}", flush=True)

    env.close()


if __name__ == "__main__":
    main()