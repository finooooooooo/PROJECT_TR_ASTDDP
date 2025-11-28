import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from auth import auth_bp, login_required, admin_required
from db import get_db_cursor
import services
import openpyxl
from io import BytesIO
from flask import send_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key' # Change in production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register Auth Blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# --- ADMIN ROUTES ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = services.get_dashboard_stats()

    # Get Chart Data (Last 7 days sales)
    # Simple query for chart
    chart_labels = []
    chart_data = []

    with get_db_cursor() as cur:
        cur.execute("""
            SELECT DATE(created_at) as date, SUM(total_amount) as total
            FROM orders
            WHERE status = 'paid'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """)
        results = cur.fetchall()

        # Sort back to ascending for chart
        results.reverse()
        for row in results:
            chart_labels.append(row['date'].strftime('%Y-%m-%d'))
            chart_data.append(int(row['total']))

    return render_template('admin/dashboard.html', stats=stats, chart_labels=chart_labels, chart_data=chart_data)

@app.route('/admin/products', methods=('GET', 'POST'))
@admin_required
def admin_products():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        is_managed = 'is_inventory_managed' in request.form
        stock = request.form['stock'] if is_managed else 0

        image = request.files.get('image')
        image_url = 'https://placehold.co/400x300?text=No+Image' # Default

        if image and image.filename:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            image_url = f"/static/uploads/{filename}"

        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO products (name, price, category, image_url, is_inventory_managed, stock)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (name, price, category, image_url, is_managed, stock)
            )
        flash('Product created successfully.')
        return redirect(url_for('admin_products'))

    products = services.get_products()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/delete/<int:id>', methods=('POST',))
@admin_required
def delete_product(id):
    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (id,))
    flash('Product deleted.')
    return redirect(url_for('admin_products'))

@app.route('/admin/sales')
@admin_required
def admin_sales():
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = cur.fetchall()
    return render_template('admin/sales.html', orders=orders)

@app.route('/admin/sales/void/<int:id>', methods=('POST',))
@admin_required
def void_transaction(id):
    try:
        services.void_order(id)
        flash('Order voided successfully.')
    except Exception as e:
        flash(f'Error: {str(e)}')
    return redirect(url_for('admin_sales'))

@app.route('/admin/sales/export')
@admin_required
def export_sales():
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = cur.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    headers = ['ID', 'Transaction Code', 'Date', 'Total', 'Tax', 'Payment', 'Status']
    ws.append(headers)

    for o in orders:
        ws.append([
            o['id'],
            o['transaction_code'],
            o['created_at'],
            o['total_amount'],
            o['tax_amount'],
            o['payment_method'],
            o['status']
        ])

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    return send_file(
        out,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='sales_report.xlsx',
        as_attachment=True
    )

# --- POS ROUTES ---

@app.route('/pos')
@login_required
def pos_index():
    return render_template('pos/index.html')

@app.route('/api/products')
@login_required
def api_products():
    products = services.get_products()
    return jsonify(products)

@app.route('/api/order', methods=('POST',))
@login_required
def api_create_order():
    data = request.json
    try:
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')

        if not items:
            return jsonify({'error': 'Cart is empty'}), 400

        result = services.create_order(items, payment_method)
        return jsonify({'status': 'success', 'data': result})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Order Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
