import sqlite3

DB_PATH = "../db/magazines.db"

def create_tables(conn):
    try:
        # Starting with publishers since magazines will reference them.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS publishers (
                publisher_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Each magazine belongs to one publisher.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS magazines (
                magazine_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                publisher_id INTEGER NOT NULL,
                FOREIGN KEY (publisher_id)
                    REFERENCES publishers(publisher_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                subscriber_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                UNIQUE (name, address)
            )
        """)

        # This table handles the many-to-many relationship.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY,
                subscriber_id INTEGER NOT NULL,
                magazine_id INTEGER NOT NULL,
                expiration_date TEXT NOT NULL,
                UNIQUE (subscriber_id, magazine_id),
                FOREIGN KEY (subscriber_id)
                    REFERENCES subscribers(subscriber_id),
                FOREIGN KEY (magazine_id)
                    REFERENCES magazines(magazine_id)
            )
        """)

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def add_publisher(conn, name):
    try:
        # Checking first so rerunning the script doesn't duplicate anything.
        cursor = conn.execute(
            "SELECT publisher_id FROM publishers WHERE name = ?",
            (name,)
        )

        if cursor.fetchone() is None:
            conn.execute(
                "INSERT INTO publishers (name) VALUES (?)",
                (name,)
            )

    except sqlite3.Error as e:
        print(f"Error adding publisher: {e}")


def add_magazine(conn, name, publisher_name):
    try:
        # If the magazine is already there, I'm done.
        if conn.execute(
            "SELECT magazine_id FROM magazines WHERE name = ?",
            (name,)
        ).fetchone():
            return

        # I need the publisher ID for the foreign key.
        publisher = conn.execute(
            "SELECT publisher_id FROM publishers WHERE name = ?",
            (publisher_name,)
        ).fetchone()

        if publisher is None:
            print(f"Publisher not found: {publisher_name}")
            return

        conn.execute(
            "INSERT INTO magazines (name, publisher_id) VALUES (?, ?)",
            (name, publisher[0])
        )

    except sqlite3.Error as e:
        print(f"Error adding magazine: {e}")

def add_subscriber(conn, name, address):
    try:
        # Name alone isn't enough, so I'm checking name and address together.
        existing = conn.execute(
            """
            SELECT subscriber_id
            FROM subscribers
            WHERE name = ? AND address = ?
            """,
            (name, address)
        ).fetchone()

        if existing is None:
            conn.execute(
                "INSERT INTO subscribers (name, address) VALUES (?, ?)",
                (name, address)
            )

    except sqlite3.Error as e:
        print(f"Error adding subscriber: {e}")

def add_subscription(conn, subscriber_name, subscriber_address,
                     magazine_name, expiration_date):
    try:
        # Finding both IDs before I create the subscription.
        subscriber = conn.execute(
            """
            SELECT subscriber_id
            FROM subscribers
            WHERE name = ? AND address = ?
            """,
            (subscriber_name, subscriber_address)
        ).fetchone()

        magazine = conn.execute(
            "SELECT magazine_id FROM magazines WHERE name = ?",
            (magazine_name,)
        ).fetchone()

        if subscriber is None or magazine is None:
            return

        # Again, making this safe to run more than once.
        existing = conn.execute(
            """
            SELECT subscription_id
            FROM subscriptions
            WHERE subscriber_id = ? AND magazine_id = ?
            """,
            (subscriber[0], magazine[0])
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO subscriptions (
                    subscriber_id, magazine_id, expiration_date
                )
                VALUES (?, ?, ?)
                """,
                (subscriber[0], magazine[0], expiration_date)
            )

    except sqlite3.Error as e:
        print(f"Error adding subscription: {e}")

def run_queries(conn):
    try:
        # First query: everybody subscribed.
        print("\n--- All Subscribers ---")
        for row in conn.execute("SELECT * FROM subscribers"):
            print(row)

        # Second query: magazines alphabetically.
        print("\n--- Magazines Sorted By Name ---")
        for row in conn.execute(
            "SELECT * FROM magazines ORDER BY name"
        ):
            print(row)

        # Final query uses the JOIN to connect magazines back to publishers.
        print("\n--- Magazines Published By Condé Nast ---")
        for row in conn.execute(
            """
            SELECT magazines.name, publishers.name
            FROM magazines
            JOIN publishers
                ON magazines.publisher_id = publishers.publisher_id
            WHERE publishers.name = ?
            ORDER BY magazines.name
            """,
            ("Condé Nast",)
        ):
            print(row)

    except sqlite3.Error as e:
        print(f"Error running queries: {e}")

def main():
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)

        # SQLite doesn't enforce foreign keys unless I turn this on.
        conn.execute("PRAGMA foreign_keys = 1")

        create_tables(conn)

        add_publisher(conn, "Condé Nast")
        add_publisher(conn, "Hearst")
        add_publisher(conn, "National Geographic Partners")

        add_magazine(conn, "Vogue", "Condé Nast")
        add_magazine(conn, "GQ", "Condé Nast")
        add_magazine(conn, "Cosmopolitan", "Hearst")
        add_magazine(conn, "National Geographic",
                     "National Geographic Partners")

        add_subscriber(conn, "Alice Johnson", "100 Main Street")
        add_subscriber(conn, "Bob Smith", "200 Oak Avenue")
        add_subscriber(conn, "Charlie Brown", "300 Pine Road")

        add_subscription(
            conn, "Alice Johnson", "100 Main Street",
            "Vogue", "2027-05-01"
        )
        add_subscription(
            conn, "Alice Johnson", "100 Main Street",
            "National Geographic", "2027-08-01"
        )
        add_subscription(
            conn, "Bob Smith", "200 Oak Avenue",
            "GQ", "2027-06-15"
        )
        add_subscription(
            conn, "Charlie Brown", "300 Pine Road",
            "Cosmopolitan", "2027-09-30"
        )

        # Nothing is permanently saved until I commit it.
        conn.commit()

        run_queries(conn)

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        # Closing it whether the script succeeds or something blows up.
        if conn:
            conn.close()

if __name__ == "__main__":
    main()