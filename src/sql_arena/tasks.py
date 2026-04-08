"""
Task Bank for SQL Arena.

Contains 9 SQL challenges across 3 difficulty levels:
- basic_select (Easy): 3 tasks — simple SELECT/WHERE/ORDER BY
- join_aggregate (Medium): 3 tasks — JOINs, GROUP BY, HAVING
- complex_analysis (Hard): 3 tasks — CTEs, window functions, subqueries

Each task defines:
- Database schema and sample data (setup_sql)
- Natural language question
- Expected SQL solution
- Expected result for grading
- Progressive hints
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random


@dataclass
class SQLTask:
    """A single SQL challenge problem."""
    task_id: str
    difficulty: str  # basic_select, join_aggregate, complex_analysis
    title: str
    setup_sql: str  # CREATE TABLE + INSERT statements
    question: str  # Natural language question
    expected_sql: str  # Reference solution
    expected_columns: List[str]  # Expected column names in result
    expected_row_count: int  # Expected number of result rows
    expected_rows: List[tuple]  # Expected result rows for grading
    hints: List[str] = field(default_factory=list)
    max_steps: int = 5
    schema_description: str = ""  # Human-readable schema description


# =============================================================
# DATABASE SCHEMAS
# =============================================================

# Schema 1: Employee database (used by Easy tasks)
EMPLOYEES_SCHEMA = """
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

INSERT INTO employees VALUES (1, 'Alice Johnson', 'Engineering', 95000, '2020-01-15', 1);
INSERT INTO employees VALUES (2, 'Bob Smith', 'Marketing', 65000, '2019-06-01', 1);
INSERT INTO employees VALUES (3, 'Carol Williams', 'Engineering', 110000, '2018-03-20', 1);
INSERT INTO employees VALUES (4, 'David Brown', 'Sales', 72000, '2021-09-10', 1);
INSERT INTO employees VALUES (5, 'Eve Davis', 'Engineering', 88000, '2022-02-28', 1);
INSERT INTO employees VALUES (6, 'Frank Miller', 'Marketing', 58000, '2020-11-15', 0);
INSERT INTO employees VALUES (7, 'Grace Wilson', 'Sales', 81000, '2019-04-22', 1);
INSERT INTO employees VALUES (8, 'Henry Taylor', 'Engineering', 125000, '2017-08-01', 1);
INSERT INTO employees VALUES (9, 'Ivy Anderson', 'HR', 70000, '2021-01-10', 1);
INSERT INTO employees VALUES (10, 'Jack Thomas', 'HR', 75000, '2020-07-15', 1);
"""

EMPLOYEES_SCHEMA_DESC = """Table: employees
Columns:
  - id: INTEGER PRIMARY KEY (auto-increment identifier)
  - name: TEXT (employee full name, e.g. 'Alice Johnson')
  - department: TEXT (one of: Engineering, Marketing, Sales, HR)
  - salary: REAL (annual salary in USD, e.g. 95000.0)
  - hire_date: TEXT (date in YYYY-MM-DD format, e.g. '2020-01-15')
  - is_active: INTEGER (1 = currently active, 0 = inactive/left)

Data: 10 employees across 4 departments.
  - 4 in Engineering, 2 in Marketing (1 inactive), 2 in Sales, 2 in HR
  - Salaries range from 58,000 to 125,000
  - Hire dates range from 2017 to 2022
"""


# Schema 2: E-commerce database (used by Medium and Hard tasks)
ECOMMERCE_SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Customers
INSERT INTO customers VALUES (1, 'Alice', 'alice@email.com', 'New York', '2023-01-15');
INSERT INTO customers VALUES (2, 'Bob', 'bob@email.com', 'Los Angeles', '2023-02-20');
INSERT INTO customers VALUES (3, 'Carol', 'carol@email.com', 'Chicago', '2023-03-10');
INSERT INTO customers VALUES (4, 'David', 'david@email.com', 'New York', '2023-04-05');
INSERT INTO customers VALUES (5, 'Eve', 'eve@email.com', 'Boston', '2023-05-12');

-- Products
INSERT INTO products VALUES (1, 'Laptop', 'Electronics', 999.99, 50);
INSERT INTO products VALUES (2, 'Headphones', 'Electronics', 149.99, 200);
INSERT INTO products VALUES (3, 'Python Book', 'Books', 39.99, 100);
INSERT INTO products VALUES (4, 'Desk Lamp', 'Home', 29.99, 150);
INSERT INTO products VALUES (5, 'Keyboard', 'Electronics', 79.99, 120);
INSERT INTO products VALUES (6, 'SQL Book', 'Books', 44.99, 80);

-- Orders (10 orders, various statuses)
INSERT INTO orders VALUES (1, 1, '2023-06-01', 'completed');
INSERT INTO orders VALUES (2, 1, '2023-07-15', 'completed');
INSERT INTO orders VALUES (3, 2, '2023-06-20', 'completed');
INSERT INTO orders VALUES (4, 3, '2023-08-01', 'completed');
INSERT INTO orders VALUES (5, 3, '2023-08-15', 'completed');
INSERT INTO orders VALUES (6, 3, '2023-09-01', 'completed');
INSERT INTO orders VALUES (7, 4, '2023-07-10', 'cancelled');
INSERT INTO orders VALUES (8, 5, '2023-09-20', 'completed');
INSERT INTO orders VALUES (9, 1, '2023-10-01', 'completed');
INSERT INTO orders VALUES (10, 2, '2023-10-15', 'pending');

-- Order Items (17 line items)
INSERT INTO order_items VALUES (1, 1, 1, 1, 999.99);
INSERT INTO order_items VALUES (2, 1, 2, 2, 149.99);
INSERT INTO order_items VALUES (3, 2, 3, 1, 39.99);
INSERT INTO order_items VALUES (4, 2, 5, 1, 79.99);
INSERT INTO order_items VALUES (5, 3, 1, 1, 999.99);
INSERT INTO order_items VALUES (6, 3, 4, 3, 29.99);
INSERT INTO order_items VALUES (7, 4, 2, 1, 149.99);
INSERT INTO order_items VALUES (8, 4, 6, 2, 44.99);
INSERT INTO order_items VALUES (9, 5, 3, 1, 39.99);
INSERT INTO order_items VALUES (10, 5, 5, 2, 79.99);
INSERT INTO order_items VALUES (11, 6, 1, 1, 999.99);
INSERT INTO order_items VALUES (12, 6, 2, 1, 149.99);
INSERT INTO order_items VALUES (13, 8, 6, 1, 44.99);
INSERT INTO order_items VALUES (14, 8, 4, 1, 29.99);
INSERT INTO order_items VALUES (15, 9, 2, 3, 149.99);
INSERT INTO order_items VALUES (16, 9, 3, 2, 39.99);
INSERT INTO order_items VALUES (17, 10, 1, 1, 999.99);
"""

ECOMMERCE_SCHEMA_DESC = """Tables:

1. customers (5 rows)
   - id: INTEGER PRIMARY KEY
   - name: TEXT (customer first name)
   - email: TEXT
   - city: TEXT (New York, Los Angeles, Chicago, Boston)
   - signup_date: TEXT (YYYY-MM-DD)

2. products (6 rows)
   - id: INTEGER PRIMARY KEY
   - name: TEXT (product name)
   - category: TEXT (Electronics, Books, Home)
   - price: REAL (unit price in USD)
   - stock: INTEGER (units in stock)

3. orders (10 rows)
   - id: INTEGER PRIMARY KEY
   - customer_id: INTEGER → customers.id
   - order_date: TEXT (YYYY-MM-DD, range: 2023-06 to 2023-10)
   - status: TEXT (completed, cancelled, pending)

4. order_items (17 rows)
   - id: INTEGER PRIMARY KEY
   - order_id: INTEGER → orders.id
   - product_id: INTEGER → products.id
   - quantity: INTEGER
   - unit_price: REAL (price at time of order)

Relationships:
  orders.customer_id → customers.id
  order_items.order_id → orders.id
  order_items.product_id → products.id
"""


# =============================================================
# EASY TASKS: basic_select (3 tasks)
# =============================================================

EASY_TASKS = [
    SQLTask(
        task_id="easy_001",
        difficulty="basic_select",
        title="High Salary Employees",
        setup_sql=EMPLOYEES_SCHEMA,
        question="Find the names and salaries of all ACTIVE employees who earn more than \$80,000. Order the results by salary from highest to lowest.",
        expected_sql="SELECT name, salary FROM employees WHERE is_active = 1 AND salary > 80000 ORDER BY salary DESC",
        expected_columns=["name", "salary"],
        expected_row_count=4,
        expected_rows=[
            ("Henry Taylor", 125000.0),
            ("Carol Williams", 110000.0),
            ("Alice Johnson", 95000.0),
            ("Eve Davis", 88000.0),
        ],
        hints=[
            "Use SELECT with specific column names, not SELECT *",
            "Use WHERE with AND to combine conditions: is_active = 1 AND salary > 80000",
            "Add ORDER BY salary DESC for descending order",
        ],
        schema_description=EMPLOYEES_SCHEMA_DESC,
        max_steps=5,
    ),

    SQLTask(
        task_id="easy_002",
        difficulty="basic_select",
        title="Department Employee Count",
        setup_sql=EMPLOYEES_SCHEMA,
        question="Count the number of ACTIVE employees in each department. Show the department name and the count. Order by count from highest to lowest.",
        expected_sql="SELECT department, COUNT(*) as employee_count FROM employees WHERE is_active = 1 GROUP BY department ORDER BY employee_count DESC",
        expected_columns=["department", "employee_count"],
        expected_row_count=4,
        expected_rows=[
            ("Engineering", 4),
            ("HR", 2),
            ("Sales", 2),
            ("Marketing", 1),
        ],
        hints=[
            "Use COUNT(*) to count rows in each group",
            "GROUP BY department groups rows by department",
            "Use an alias: COUNT(*) as employee_count",
        ],
        schema_description=EMPLOYEES_SCHEMA_DESC,
        max_steps=5,
    ),

    SQLTask(
        task_id="easy_003",
        difficulty="basic_select",
        title="Recent Hires",
        setup_sql=EMPLOYEES_SCHEMA,
        question="List the names and hire dates of employees hired on or after January 1, 2021. Order by hire date from earliest to latest.",
        expected_sql="SELECT name, hire_date FROM employees WHERE hire_date >= '2021-01-01' ORDER BY hire_date",
        expected_columns=["name", "hire_date"],
        expected_row_count=3,
        expected_rows=[
            ("Ivy Anderson", "2021-01-10"),
            ("David Brown", "2021-09-10"),
            ("Eve Davis", "2022-02-28"),
        ],
        hints=[
            "Dates in SQLite can be compared as strings when in YYYY-MM-DD format",
            "Use WHERE hire_date >= '2021-01-01'",
            "ORDER BY hire_date gives ascending order by default",
        ],
        schema_description=EMPLOYEES_SCHEMA_DESC,
        max_steps=5,
    ),
]


# =============================================================
# MEDIUM TASKS: join_aggregate (3 tasks)
# =============================================================

MEDIUM_TASKS = [
    SQLTask(
        task_id="medium_001",
        difficulty="join_aggregate",
        title="Customer Total Spending",
        setup_sql=ECOMMERCE_SCHEMA,
        question="Find the total amount spent by each customer on COMPLETED orders only. Show the customer name and their total spending. Only include customers who spent more than \$200. Order by total spending from highest to lowest.",
        expected_sql="""
            SELECT c.name, ROUND(SUM(oi.quantity * oi.unit_price), 2) as total_spent
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            JOIN order_items oi ON o.id = oi.order_id
            WHERE o.status = 'completed'
            GROUP BY c.id, c.name
            HAVING SUM(oi.quantity * oi.unit_price) > 200
            ORDER BY total_spent DESC
        """,
        expected_columns=["name", "total_spent"],
        expected_row_count=4,
        expected_rows=[
            ("Alice", 1919.91),
            ("Carol", 1464.94),
            ("Bob", 1089.96),
            ("Eve", 74.98),
        ],
        hints=[
            "You need to JOIN three tables: customers → orders → order_items",
            "Total per item = quantity * unit_price, then SUM for total per customer",
            "Filter completed orders with WHERE o.status = 'completed'",
            "Use HAVING (not WHERE) to filter after GROUP BY",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=7,
    ),

    SQLTask(
        task_id="medium_002",
        difficulty="join_aggregate",
        title="Category Revenue",
        setup_sql=ECOMMERCE_SCHEMA,
        question="Calculate the total revenue for each product category from COMPLETED orders. Show the category name and total revenue. Order by total revenue from highest to lowest.",
        expected_sql="""
            SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) as total_revenue
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status = 'completed'
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """,
        expected_columns=["category", "total_revenue"],
        expected_row_count=3,
        expected_rows=[
            ("Electronics", 4459.83),
            ("Books", 254.93),
            ("Home", 119.96),
        ],
        hints=[
            "JOIN products → order_items → orders",
            "Revenue per item = quantity * unit_price",
            "Filter only completed orders",
            "GROUP BY p.category to get per-category totals",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=7,
    ),

    SQLTask(
        task_id="medium_003",
        difficulty="join_aggregate",
        title="Customers with Multiple Orders",
        setup_sql=ECOMMERCE_SCHEMA,
        question="Find customers who have placed more than one COMPLETED order. Show the customer name and the number of completed orders they placed. Order by order count descending, then by name ascending.",
        expected_sql="""
            SELECT c.name, COUNT(o.id) as order_count
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status = 'completed'
            GROUP BY c.id, c.name
            HAVING COUNT(o.id) > 1
            ORDER BY order_count DESC, c.name ASC
        """,
        expected_columns=["name", "order_count"],
        expected_row_count=2,
        expected_rows=[
            ("Alice", 3),
            ("Carol", 3),
        ],
        hints=[
            "JOIN customers with orders",
            "Filter for completed orders in WHERE clause",
            "GROUP BY customer, then HAVING COUNT > 1",
            "ORDER BY count DESC, then name ASC for ties",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=7,
    ),
]


# =============================================================
# HARD TASKS: complex_analysis (3 tasks)
# =============================================================

HARD_TASKS = [
    SQLTask(
        task_id="hard_001",
        difficulty="complex_analysis",
        title="Monthly Revenue with Growth Rate",
        setup_sql=ECOMMERCE_SCHEMA,
        question="Calculate monthly revenue from COMPLETED orders, and for each month show the month (YYYY-MM format), the total revenue, and the percentage change from the previous month. For the first month, the percentage change should be NULL. Round revenue to 2 decimal places and percentage to 2 decimal places. Order by month ascending.",
        expected_sql="""
            WITH monthly AS (
                SELECT 
                    strftime('%Y-%m', o.order_date) as month,
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) as revenue
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'completed'
                GROUP BY strftime('%Y-%m', o.order_date)
            ),
            with_prev AS (
                SELECT 
                    month,
                    revenue,
                    LAG(revenue) OVER (ORDER BY month) as prev_revenue
                FROM monthly
            )
            SELECT 
                month,
                revenue,
                CASE 
                    WHEN prev_revenue IS NULL THEN NULL
                    ELSE ROUND(((revenue - prev_revenue) * 100.0 / prev_revenue), 2)
                END as pct_change
            FROM with_prev
            ORDER BY month
        """,
        expected_columns=["month", "revenue", "pct_change"],
        expected_row_count=5,
        expected_rows=[
            ("2023-06", 2289.93, None),
            ("2023-07", 119.98, -94.76),
            ("2023-08", 1429.93, 1091.81),
            ("2023-09", 1224.97, -14.34),
            ("2023-10", 529.95, -56.74),
        ],
        hints=[
            "Use a CTE (WITH clause) to first calculate monthly revenue",
            "strftime('%Y-%m', date) extracts year-month from a date string",
            "LAG(revenue) OVER (ORDER BY month) gets the previous month's revenue",
            "Percentage change = ((new - old) / old) * 100",
            "Use CASE WHEN prev IS NULL THEN NULL ELSE ... END for first month",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=10,
    ),

    SQLTask(
        task_id="hard_002",
        difficulty="complex_analysis",
        title="Top Product Per Category",
        setup_sql=ECOMMERCE_SCHEMA,
        question="For each product category, find the single best-selling product (by total quantity sold across COMPLETED orders). Show the category, product name, and total quantity sold. If there are ties, pick the one with the higher total revenue. Order by category name ascending.",
        expected_sql="""
            WITH product_sales AS (
                SELECT 
                    p.category,
                    p.name as product_name,
                    SUM(oi.quantity) as total_qty,
                    SUM(oi.quantity * oi.unit_price) as total_revenue,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.category 
                        ORDER BY SUM(oi.quantity) DESC, SUM(oi.quantity * oi.unit_price) DESC
                    ) as rn
                FROM products p
                JOIN order_items oi ON p.id = oi.product_id
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'completed'
                GROUP BY p.category, p.name
            )
            SELECT category, product_name, total_qty
            FROM product_sales
            WHERE rn = 1
            ORDER BY category ASC
        """,
        expected_columns=["category", "product_name", "total_qty"],
        expected_row_count=3,
        expected_rows=[
            ("Books", "Python Book", 4),
            ("Electronics", "Headphones", 7),
            ("Home", "Desk Lamp", 4),
        ],
        hints=[
            "First calculate total quantity sold per product (SUM of quantity)",
            "Use ROW_NUMBER() OVER (PARTITION BY category ORDER BY qty DESC) to rank within category",
            "Filter WHERE rn = 1 to get only the top product per category",
            "A CTE makes this much cleaner than nested subqueries",
            "Don't forget to filter for completed orders only",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=10,
    ),

    SQLTask(
        task_id="hard_003",
        difficulty="complex_analysis",
        title="Customer Lifetime Value Analysis",
        setup_sql=ECOMMERCE_SCHEMA,
        question="For customers with at least 2 completed orders, calculate: their name, number of completed orders, total lifetime spending (rounded to 2 decimals), average order value (rounded to 2 decimals), and the number of days between their first and last completed order. Order by total spending descending.",
        expected_sql="""
            WITH customer_order_totals AS (
                SELECT 
                    c.id as customer_id,
                    c.name,
                    o.id as order_id,
                    o.order_date,
                    SUM(oi.quantity * oi.unit_price) as order_total
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'completed'
                GROUP BY c.id, c.name, o.id, o.order_date
            )
            SELECT 
                name,
                COUNT(*) as num_orders,
                ROUND(SUM(order_total), 2) as total_spending,
                ROUND(AVG(order_total), 2) as avg_order_value,
                CAST(julianday(MAX(order_date)) - julianday(MIN(order_date)) AS INTEGER) as days_span
            FROM customer_order_totals
            GROUP BY customer_id, name
            HAVING COUNT(*) >= 2
            ORDER BY total_spending DESC
        """,
        expected_columns=["name", "num_orders", "total_spending", "avg_order_value", "days_span"],
        expected_row_count=2,
        expected_rows=[
            ("Alice", 3, 1919.91, 639.97, 122),
            ("Carol", 3, 1464.94, 488.31, 31),
        ],
        hints=[
            "Use a CTE to first calculate the total for each individual order",
            "In the CTE: JOIN customers → orders → order_items, GROUP BY order",
            "In the outer query: GROUP BY customer, HAVING COUNT >= 2",
            "julianday() converts date strings to Julian day numbers for arithmetic",
            "days_span = julianday(MAX(order_date)) - julianday(MIN(order_date))",
        ],
        schema_description=ECOMMERCE_SCHEMA_DESC,
        max_steps=10,
    ),
]


# =============================================================
# TASK REGISTRY — Maps task IDs and difficulty levels
# =============================================================

ALL_TASKS: Dict[str, List[SQLTask]] = {
    "basic_select": EASY_TASKS,
    "join_aggregate": MEDIUM_TASKS,
    "complex_analysis": HARD_TASKS,
}

# Build a flat lookup by task_id
TASK_BY_ID: Dict[str, SQLTask] = {}
for _tasks in ALL_TASKS.values():
    for _task in _tasks:
        TASK_BY_ID[_task.task_id] = _task


def get_task(difficulty: str, task_id: Optional[str] = None) -> SQLTask:
    """
    Get a task by difficulty level, optionally by specific ID.
    
    Args:
        difficulty: One of 'basic_select', 'join_aggregate', 'complex_analysis'
        task_id: Optional specific task ID (e.g., 'easy_001')
        
    Returns:
        SQLTask instance
        
    Raises:
        ValueError: If difficulty is unknown
    """
    # If specific task_id given, return it directly
    if task_id and task_id in TASK_BY_ID:
        return TASK_BY_ID[task_id]

    # Otherwise pick from the difficulty pool
    if difficulty not in ALL_TASKS:
        raise ValueError(
            f"Unknown difficulty: '{difficulty}'. "
            f"Choose from: {list(ALL_TASKS.keys())}"
        )

    tasks = ALL_TASKS[difficulty]
    return random.choice(tasks)


def list_tasks() -> Dict[str, List[str]]:
    """
    List all available tasks grouped by difficulty.
    
    Returns:
        Dict mapping difficulty name to list of task IDs
    """
    return {
        difficulty: [t.task_id for t in tasks]
        for difficulty, tasks in ALL_TASKS.items()
    }