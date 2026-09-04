import sqlite3

DB_PATH = "../db/lesson.db"

def task_1(conn):
    # task1 join each order to its line items and products, then total the order.
    rows = conn.execute(
        """
        SELECT
            o.order_id,
            SUM(p.price * l.quantity) AS total_price
        FROM orders o
        JOIN line_items l
            ON o.order_id = l.order_id
        JOIN products p
            ON l.product_id = p.product_id
        GROUP BY o.order_id
        ORDER BY o.order_id
        LIMIT 5
        """
    ).fetchall()

    print("\nTask 1: First 5 order totals")
    for order_id, total_price in rows:
        print(order_id, round(total_price, 2))

def task_2(conn):
    # task2 subquery gets one total per order first.
    rows = conn.execute(
        """
        SELECT
            c.customer_name,
            AVG(order_totals.total_price) AS average_total_price
        FROM customers c
        LEFT JOIN (
            SELECT
                o.customer_id AS customer_id_b,
                SUM(p.price * l.quantity) AS total_price
            FROM orders o
            JOIN line_items l
                ON o.order_id = l.order_id
            JOIN products p
                ON l.product_id = p.product_id
            GROUP BY o.order_id, o.customer_id
        ) AS order_totals
            ON c.customer_id = order_totals.customer_id_b
        GROUP BY c.customer_id, c.customer_name
        ORDER BY c.customer_name
        """
    ).fetchall()

    print("\nTask 2: Average order price by customer")
    for customer_name, average_total_price in rows:
        if average_total_price is None:
            print(customer_name, None)
        else:
            print(customer_name, round(average_total_price, 2))


def task_3(conn):
    # task3 IDs needed before starting the insert transaction.
    customer = conn.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE customer_name = ?
        """,
        ("Perez and Sons",),
    ).fetchone()

    employee = conn.execute(
        """
        SELECT employee_id
        FROM employees
        WHERE first_name = ?
          AND last_name = ?
        """,
        ("Miranda", "Harris"),
    ).fetchone()

    products = conn.execute(
        """
        SELECT product_id
        FROM products
        ORDER BY price, product_id
        LIMIT 5
        """
    ).fetchall()

    if customer is None:
        raise RuntimeError("Perez and Sons was not found.")

    if employee is None:
        raise RuntimeError("Miranda Harris was not found.")

    if len(products) != 5:
        raise RuntimeError("Five products were not found.")

    try:
        # order and all five line items should succeed or fail together.
        conn.execute("BEGIN")

        order_id = conn.execute(
            """
            INSERT INTO orders (customer_id, employee_id)
            VALUES (?, ?)
            RETURNING order_id
            """,
            (customer[0], employee[0]),
        ).fetchone()[0]

        for (product_id,) in products:
            conn.execute(
                """
                INSERT INTO line_items (
                    order_id,
                    product_id,
                    quantity
                )
                VALUES (?, ?, ?)
                """,
                (order_id, product_id, 10),
            )

        conn.commit()

    except (sqlite3.Error, RuntimeError):
        # don't leave a half-finished order in the database.
        conn.rollback()
        raise

    rows = conn.execute(
        """
        SELECT
            l.line_item_id,
            l.quantity,
            p.product_name
        FROM line_items l
        JOIN products p
            ON l.product_id = p.product_id
        WHERE l.order_id = ?
        ORDER BY l.line_item_id
        """,
        (order_id,),
    ).fetchall()

    print("\nTask 3: New Perez and Sons order")
    print(f"order_id: {order_id}")

    for line_item_id, quantity, product_name in rows:
        print(line_item_id, quantity, product_name)

def task_4(conn):
    # task 4 having filters the employee groups after the order counts are calculated.
    rows = conn.execute(
        """
        SELECT
            e.employee_id,
            e.first_name,
            e.last_name,
            COUNT(o.order_id) AS order_count
        FROM employees e
        JOIN orders o
            ON e.employee_id = o.employee_id
        GROUP BY
            e.employee_id,
            e.first_name,
            e.last_name
        HAVING COUNT(o.order_id) > 5
        ORDER BY order_count DESC, e.employee_id
        """
    ).fetchall()

    print("\nTask 4: Employees with more than 5 orders")
    for employee_id, first_name, last_name, order_count in rows:
        print(employee_id, first_name, last_name, order_count)

def main():
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = 1")

        task_1(conn)
        task_2(conn)
        task_3(conn)
        task_4(conn)

    except (sqlite3.Error, RuntimeError) as error:
        if conn is not None:
            conn.rollback()
        print(f"Error: {error}")

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()

