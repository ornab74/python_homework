import sqlite3
import pandas as pd

DB_PATH = "../db/lesson.db"
OUTPUT_FILE = "order_summary.csv"

def main():
    conn = None

    try:
        # Opening the lesson database so I can pull the order/product data.
        conn = sqlite3.connect(DB_PATH)

        # Joining these tables gives me the product info and quantity together.
        query = """
            SELECT
                line_items.line_item_id,
                line_items.quantity,
                products.product_id,
                products.product_name,
                products.price
            FROM line_items
            JOIN products
                ON line_items.product_id = products.product_id
        """

        # Loading the SQL results straight into Pandas.
        df = pd.read_sql_query(query, conn)

        print("\n--- Original DataFrame ---")
        print(df.head())

        # Quantity times price gives me the total for each line item.
        df["total"] = df["quantity"] * df["price"]

        print("\n--- DataFrame With Total ---")
        print(df.head())

        # Grouping by product so I can get order counts and total sales.
        summary_df = (
            df.groupby("product_id")
            .agg({
                "line_item_id": "count",
                "total": "sum",
                "product_name": "first"
            })
            .reset_index()
            .sort_values(by="product_name")
        )

        print("\n--- Order Summary ---")
        print(summary_df.head())

        # Saving the finished summary to CSV.
        summary_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSaved summary to {OUTPUT_FILE}")

    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        print(f"Error: {e}")

    finally:
        # Making sure I don't leave the database connection hanging open.
        if conn:
            conn.close()

if __name__ == "__main__":
    main()