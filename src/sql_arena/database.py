"""
SQLite Database Manager for SQL Arena.

Creates in-memory SQLite databases for each task.
Executes agent queries safely and formats results.

Key design decisions:
- In-memory databases (fast, no disk I/O, no cleanup needed)
- Each reset() creates a fresh database
- Query execution is sandboxed (read-only would be ideal but SQLite
  in-memory is ephemeral anyway)
"""

import sqlite3
from typing import Tuple, Optional, Any, Dict


class DatabaseManager:
    """
    Manages SQLite in-memory databases for SQL challenges.
    
    Each task gets its own fresh database with schema and sample data.
    The agent's queries are executed against this database.
    """

    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None

    def create_database(self, setup_sql: str) -> None:
        """
        Create a new in-memory database with the given schema and data.
        
        Args:
            setup_sql: SQL string containing CREATE TABLE and INSERT statements
        """
        # Close any existing connection
        self.close()
        
        # Create fresh in-memory database
        self.conn = sqlite3.connect(":memory:")
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Run the setup SQL (creates tables and inserts data)
        self.conn.executescript(setup_sql)
        self.conn.commit()

    def execute_query(self, sql: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Execute a SQL query and return results.
        
        This is the main method called when the agent submits a query.
        It catches all exceptions to prevent crashes.
        
        Args:
            sql: The SQL query string to execute
            
        Returns:
            Tuple of (success, result_dict, error_message):
            - success: True if query executed without error
            - result_dict: {"columns": [...], "rows": [...]} if successful
            - error_message: Error string if failed, None if success
        """
        if not self.conn:
            return False, None, "No database connection. Call create_database() first."

        try:
            cursor = self.conn.execute(sql)
            
            # Get column names from cursor description
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = []
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            result = {
                "columns": columns,
                "rows": rows,
            }
            
            return True, result, None
            
        except sqlite3.Error as e:
            return False, None, f"SQL Error: {str(e)}"
        except Exception as e:
            return False, None, f"Execution Error: {str(e)}"

    def format_result(self, result: Dict, max_rows: int = 20) -> str:
        """
        Format query result as a human-readable table string.
        
        This formatted string is shown to the agent in the observation
        so it can see what its query returned.
        
        Args:
            result: Dict with "columns" and "rows" keys
            max_rows: Maximum number of rows to display
            
        Returns:
            Formatted table string
        """
        if not result or not result.get("columns"):
            return "(empty result set)"

        columns = result["columns"]
        rows = result["rows"]

        if not rows:
            return f"Columns: {', '.join(columns)}\n(0 rows returned)"

        # Calculate column widths (at least as wide as header)
        col_widths = [len(str(c)) for c in columns]
        for row in rows[:max_rows]:
            for i, val in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(val)))

        # Build formatted table
        # Header
        header = " | ".join(
            str(c).ljust(w) for c, w in zip(columns, col_widths)
        )
        separator = "-+-".join("-" * w for w in col_widths)

        # Data rows
        formatted_rows = []
        for row in rows[:max_rows]:
            formatted_row = " | ".join(
                str(v).ljust(w) for v, w in zip(row, col_widths)
            )
            formatted_rows.append(formatted_row)

        # Assemble
        table_str = f"{header}\n{separator}\n" + "\n".join(formatted_rows)

        # Truncation notice
        if len(rows) > max_rows:
            table_str += f"\n... ({len(rows) - max_rows} more rows not shown)"

        # Row count
        table_str += f"\n\n({len(rows)} row{'s' if len(rows) != 1 else ''} returned)"

        return table_str

    def close(self) -> None:
        """Close the database connection and free resources."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass  # Ignore errors on close
            self.conn = None