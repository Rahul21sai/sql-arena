"""
Grading logic for SQL Arena.
Provides partial credit scoring (0.0 to 1.0) based on:
  - Query execution success (0.10)
  - Column correctness (0.20)
  - Row count correctness (0.20)
  - Value correctness (0.50)
"""

from typing import List, Tuple, Optional, Dict, Any
from .tasks import SQLTask


def normalize_value(val: Any) -> Any:
    """Normalize values for comparison."""
    if val is None:
        return None
    if isinstance(val, float):
        return round(val, 2)
    if isinstance(val, str):
        return val.strip().lower()
    return val


def normalize_row(row: tuple) -> tuple:
    """Normalize all values in a row."""
    return tuple(normalize_value(v) for v in row)


def grade_result(
    task: SQLTask,
    success: bool,
    result: Optional[Dict],
    error: Optional[str],
) -> Tuple[float, str]:
    """
    Grade a SQL query result against expected output.
    
    Returns:
        (score, feedback) where score is in [0.0, 1.0]
    
    Scoring breakdown:
        - 0.10: Query executes without error
        - 0.20: Correct column names
        - 0.20: Correct number of rows
        - 0.50: Correct values (proportional to matching rows)
    """
    feedback_parts = []
    score = 0.0

    # ---- Component 1: Execution Success (0.10) ----
    if not success:
        feedback_parts.append(f"X Query failed: {error}")
        feedback_parts.append("Hint: Fix the syntax error and try again.")
        return 0.0, "\n".join(feedback_parts)

    score += 0.10
    feedback_parts.append("OK: Query executed successfully (+0.10)")

    # ---- Component 2: Column Correctness (0.20) ----
    actual_columns = [c.lower().strip() for c in result.get("columns", [])]
    expected_columns = [c.lower().strip() for c in task.expected_columns]

    if actual_columns == expected_columns:
        score += 0.20
        feedback_parts.append(f"OK: Correct columns: {actual_columns} (+0.20)")
    else:
        # Partial credit for overlapping columns
        matching_cols = set(actual_columns) & set(expected_columns)
        if matching_cols:
            partial = 0.20 * (len(matching_cols) / len(expected_columns))
            score += partial
            feedback_parts.append(
                f"PARTIAL: Column match: got {actual_columns}, "
                f"expected {expected_columns} (+{partial:.2f})"
            )
            missing = set(expected_columns) - set(actual_columns)
            if missing:
                feedback_parts.append(f"Hint: Missing columns: {missing}")
        else:
            feedback_parts.append(
                f"WRONG: Columns: got {actual_columns}, expected {expected_columns}"
            )

    # ---- Component 3: Row Count (0.20) ----
    actual_rows = result.get("rows", [])
    expected_row_count = task.expected_row_count

    if len(actual_rows) == expected_row_count:
        score += 0.20
        feedback_parts.append(f"OK: Correct row count: {len(actual_rows)} (+0.20)")
    else:
        # Partial credit: closer counts get more credit
        if expected_row_count > 0:
            ratio = 1.0 - abs(len(actual_rows) - expected_row_count) / max(
                expected_row_count, len(actual_rows)
            )
            partial = max(0.0, 0.20 * ratio)
            score += partial
            feedback_parts.append(
                f"PARTIAL: Row count: got {len(actual_rows)}, "
                f"expected {expected_row_count} (+{partial:.2f})"
            )
        else:
            if len(actual_rows) == 0:
                score += 0.20
                feedback_parts.append("OK: Correct empty result set (+0.20)")
            else:
                feedback_parts.append(
                    f"WRONG: Expected empty result, got {len(actual_rows)} rows"
                )

    # ---- Component 4: Value Correctness (0.50) ----
    if task.expected_rows:
        normalized_expected = [normalize_row(r) for r in task.expected_rows]
        normalized_actual = [normalize_row(r) for r in actual_rows]

        # Try exact order match first
        exact_matches = 0
        for exp_row, act_row in zip(normalized_expected, normalized_actual):
            if exp_row == act_row:
                exact_matches += 1

        if (
            exact_matches == len(normalized_expected)
            and len(normalized_actual) == len(normalized_expected)
        ):
            score += 0.50
            feedback_parts.append("OK: All values correct with correct ordering (+0.50)")
        else:
            # Try unordered match (set-based)
            matched_rows = 0
            remaining_actual = list(normalized_actual)

            for exp_row in normalized_expected:
                for i, act_row in enumerate(remaining_actual):
                    if exp_row == act_row:
                        matched_rows += 1
                        remaining_actual.pop(i)
                        break

            if (
                matched_rows == len(normalized_expected)
                and len(normalized_actual) == len(normalized_expected)
            ):
                # All rows match but wrong order
                partial = 0.40
                score += partial
                feedback_parts.append(
                    f"PARTIAL: All values correct but wrong ordering (+{partial:.2f})"
                )
                feedback_parts.append("Hint: Check your ORDER BY clause")
            elif matched_rows > 0:
                # Some rows match
                partial = 0.50 * (matched_rows / len(normalized_expected))
                score += partial
                feedback_parts.append(
                    f"PARTIAL: {matched_rows}/{len(normalized_expected)} rows match (+{partial:.2f})"
                )
                if matched_rows < len(normalized_expected):
                    feedback_parts.append(
                        "Hint: Some values are incorrect. Check WHERE/JOIN conditions."
                    )
            else:
                feedback_parts.append("WRONG: No matching rows found")
                feedback_parts.append(
                    "Hint: Review your query logic - values don't match expected output."
                )

                # Tiny credit if some values appear somewhere
                all_expected_vals = set()
                for row in normalized_expected:
                    all_expected_vals.update(row)
                all_actual_vals = set()
                for row in normalized_actual:
                    all_actual_vals.update(row)

                overlap = all_expected_vals & all_actual_vals
                if overlap:
                    tiny_credit = 0.05
                    score += tiny_credit
                    feedback_parts.append(
                        f"  (Some expected values found in output: +{tiny_credit:.2f})"
                    )
    else:
        # Expected empty result
        if len(actual_rows) == 0:
            score += 0.50
            feedback_parts.append("OK: Correctly returned empty result (+0.50)")
        else:
            feedback_parts.append(
                f"WRONG: Expected empty result, got {len(actual_rows)} rows"
            )

    # ---- Final score ----
    score = round(min(max(score, 0.0), 1.0), 4)
    feedback_parts.append(f"\nTotal Score: {score:.2f}/1.00")

    return score, "\n".join(feedback_parts)


def generate_hint(task: SQLTask, step: int, current_score: float) -> Optional[str]:
    """Generate progressive hints based on step number and current score."""
    if current_score >= 0.8:
        return None  # No hint needed

    if step <= len(task.hints):
        return f"Hint {step}: {task.hints[step - 1]}"

    # Generic hints for later steps
    generic_hints = [
        f"Expected columns are: {task.expected_columns}",
        f"Expected {task.expected_row_count} rows in the result",
        "Check the schema description carefully for table and column names",
    ]

    hint_idx = min(step - len(task.hints) - 1, len(generic_hints) - 1)
    if hint_idx >= 0:
        return generic_hints[hint_idx]
    return None