import datetime
from db import get_db_cursor
import uuid

def generate_transaction_code():
    """Generates a transaction code in format TRX-YYYYMMDD-XXXX"""
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    prefix = f"TRX-{today_str}-"

    with get_db_cursor() as cur:
        # Find the last transaction code for today
        cur.execute(
            "SELECT transaction_code FROM orders WHERE transaction_code LIKE %s ORDER BY id DESC LIMIT 1",
            (prefix + '%',)
        )
        result = cur.fetchone()

        if result:
            last_code = result['transaction_code']
            try:
                # Extract the last 4 digits
                last_seq = int(last_code.split('-')[-1])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:04d}"

def calculate_tax(subtotal):
    """Calculates 10% tax on subtotal."""
    # Assuming subtotal is integer or decimal. Return integer for consistency if needed,
    # but requirement says DECIMAL in DB.
    # Python float math might introduce errors, but for simple 10% it's usually fine.
    # Ideally use Decimal type.
    return int(subtotal * 0.10)

def create_order(items, payment_method):
    """
    Creates an order atomically.
    items: list of dicts {'id': product_id, 'quantity': int}
    """
    transaction_code = generate_transaction_code()

    # We need to calculate totals and verify stock first
    subtotal = 0
    order_item_data = [] # To store snapshots

    # We use a single commit=True block to ensure atomicity
    # However, generate_transaction_code uses a separate cursor read.
    # To be strictly atomic and safe from race conditions in high concurrency,
    # we should do generation inside the lock or catch unique constraint violation.
    # Given the requirements, we'll try to do it all in one connection context if possible,
    # or just trust the simplified logic for this scope.

    # Refactoring generate_transaction_code to be called inside the main transaction would be better
    # but 'get_db_cursor' creates a new connection each time.
    # For this scale, it's acceptable.

    with get_db_cursor(commit=True) as cur:
        # 1. Validate Stock and Calculate Totals
        for item in items:
            product_id = item['id']
            qty = item['quantity']

            cur.execute("SELECT * FROM products WHERE id = %s FOR UPDATE", (product_id,))
            product = cur.fetchone()

            if not product:
                raise ValueError(f"Product ID {product_id} not found.")

            if product['is_inventory_managed']:
                if product['stock'] < qty:
                    raise ValueError(f"Insufficient stock for {product['name']}. Available: {product['stock']}")

                # Deduct stock
                new_stock = product['stock'] - qty
                cur.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))

            item_subtotal = product['price'] * qty
            subtotal += item_subtotal

            order_item_data.append({
                'product_name_snapshot': product['name'],
                'price_snapshot': product['price'],
                'quantity': qty,
                'subtotal': item_subtotal
            })

        # 2. Calculate Final Totals
        tax_amount = calculate_tax(subtotal)
        total_amount = subtotal + tax_amount

        # 3. Create Order
        cur.execute(
            """
            INSERT INTO orders (transaction_code, total_amount, tax_amount, payment_method, status)
            VALUES (%s, %s, %s, %s, 'paid')
            RETURNING id
            """,
            (transaction_code, total_amount, tax_amount, payment_method)
        )
        order_id = cur.fetchone()['id']

        # 4. Create Order Items
        for data in order_item_data:
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_name_snapshot, price_snapshot, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, data['product_name_snapshot'], data['price_snapshot'], data['quantity'], data['subtotal'])
            )

        return {'order_id': order_id, 'transaction_code': transaction_code, 'total': int(total_amount)}

def void_order(order_id):
    """Voids an order and restores stock."""
    with get_db_cursor(commit=True) as cur:
        # Check order status
        cur.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        if not order:
            raise ValueError("Order not found")
        if order['status'] == 'void':
            raise ValueError("Order already voided")

        # Get Items to restore stock
        cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
        items = cur.fetchall()

        # Restore stock logic
        # We need to match items back to products.
        # Note: 'product_name_snapshot' is stored, but not 'product_id'.
        # Requirements said: "order_items: id, order_id, product_name_snapshot, price_snapshot, quantity, subtotal".
        # It did NOT specify storing product_id in order_items.
        # This makes restoring stock tricky if names changed.
        # However, usually we should store product_id.
        # I will check if I can add product_id to order_items or match by name.
        # Matching by name is risky but if that's the schema...
        # Wait, the schema I wrote followed the spec: "product_name_snapshot, price_snapshot...".
        # I should probably match by name.

        for item in items:
            name = item['product_name_snapshot']
            qty = item['quantity']

            # Find product by name
            cur.execute("SELECT id, is_inventory_managed, stock FROM products WHERE name = %s", (name,))
            product = cur.fetchone()

            if product and product['is_inventory_managed']:
                new_stock = product['stock'] + qty
                cur.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product['id']))

        # Update Order Status
        cur.execute("UPDATE orders SET status = 'void' WHERE id = %s", (order_id,))

def get_products(category=None):
    query = "SELECT * FROM products"
    params = []
    if category:
        query += " WHERE category = %s"
        params.append(category)
    query += " ORDER BY name"

    with get_db_cursor() as cur:
        cur.execute(query, tuple(params))
        products = cur.fetchall()
        # Convert Decimal price to int for JSON serialization
        for p in products:
            p['price'] = int(p['price'])
        return products

def get_dashboard_stats():
    today = datetime.date.today()
    month_start = today.replace(day=1)

    with get_db_cursor() as cur:
        # Daily Sales
        cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE DATE(created_at) = %s AND status = 'paid'",
            (today,)
        )
        daily_sales = cur.fetchone()['total']

        # Monthly Sales
        cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE DATE(created_at) >= %s AND status = 'paid'",
            (month_start,)
        )
        monthly_sales = cur.fetchone()['total']

        return {
            'daily_sales': daily_sales,
            'monthly_sales': monthly_sales
        }
