import psycopg2
from werkzeug.security import generate_password_hash
from db import get_db_cursor, DB_CONFIG

def init_db():
    print("Initializing Database...")

    # Read schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()

    try:
        # We need to connect to the DB to create tables
        # Since get_db_cursor handles connection open/close, we use it.
        # But for schema creation, we might need a raw connection if we want to drop/create
        # However, our db.py assumes 'kasir_db' exists. The prompt implies tables creation.

        with get_db_cursor(commit=True) as cur:
            cur.execute(schema_sql)
            print("Tables created.")

            # Seed Users
            users = [
                ('admin', generate_password_hash('admin123'), 'admin'),
                ('cashier', generate_password_hash('cashier123'), 'cashier')
            ]

            for username, pwd, role in users:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
                    (username, pwd, role)
                )
            print("Users seeded.")

            # Seed Products
            # Check if products exist to avoid duplicate seeding if run multiple times
            cur.execute("SELECT count(*) as count FROM products")
            count = cur.fetchone()['count']

            if count == 0:
                products = [
                    ('Espresso', 25000, 'Coffee', 'https://placehold.co/400x300?text=Espresso', False, 0),
                    ('Cappuccino', 30000, 'Coffee', 'https://placehold.co/400x300?text=Cappuccino', True, 50),
                    ('Latte', 32000, 'Coffee', 'https://placehold.co/400x300?text=Latte', True, 40),
                    ('Croissant', 15000, 'Pastry', 'https://placehold.co/400x300?text=Croissant', True, 20),
                    ('Ice Tea', 10000, 'Beverage', 'https://placehold.co/400x300?text=Ice+Tea', False, 0),
                    ('Mineral Water', 5000, 'Beverage', 'https://placehold.co/400x300?text=Water', True, 100)
                ]

                for name, price, cat, img, managed, stock in products:
                    cur.execute(
                        """
                        INSERT INTO products (name, price, category, image_url, is_inventory_managed, stock)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (name, price, cat, img, managed, stock)
                    )
                print("Products seeded.")
            else:
                print("Products already exist, skipping seed.")

    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("Ensure PostgreSQL is running and credentials in db.py are correct.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    init_db()
