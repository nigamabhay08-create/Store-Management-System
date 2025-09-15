from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database setup
def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            cost_price REAL NOT NULL DEFAULT 0,
            stock_quantity INTEGER NOT NULL,
            supplier TEXT,
            barcode TEXT,
            image_url TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sales table (now includes billing info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            subtotal REAL NOT NULL,
            tax_amount REAL NOT NULL DEFAULT 0,
            discount_amount REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Sale items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute('SELECT COUNT(*) FROM admin_users')
    if cursor.fetchone()[0] == 0:
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash, full_name, email)
            VALUES (?, ?, ?, ?)
        ''', ('admin', password_hash, 'Store Administrator', 'admin@store.com'))
    
    # Insert sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('MacBook Pro', 'Electronics', 1299.99, 1000.00, 5, 'Apple Inc', '123456789012', 'https://via.placeholder.com/300x300?text=Laptop'),
            ('Wireless Mouse', 'Electronics', 29.99, 15.00, 25, 'Logitech', '123456789013', '/static/images/mouse.jpg'),
            ('Premium Coffee', 'Food & Beverages', 15.99, 8.00, 50, 'Coffee World', '123456789014', '/static/images/coffee.jpg'),
            ('Notebook Set', 'Stationery', 5.99, 2.50, 100, 'Paper Plus', '123456789015', '/static/images/notebook.jpg'),
            ('Smartphone', 'Electronics', 699.99, 500.00, 15, 'Samsung', '123456789016', '/static/images/phone.jpg'),
            ('Water Bottle', 'Accessories', 12.99, 6.00, 40, 'Hydro Co', '123456789017', '/static/images/bottle.jpg')
        ]
        cursor.executemany('''
            INSERT INTO products (name, category, price, cost_price, stock_quantity, supplier, barcode, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)
    
    # Insert sample customers
    cursor.execute('SELECT COUNT(*) FROM customers')
    if cursor.fetchone()[0] == 0:
        sample_customers = [
            ('Abhishek Srivastav', 'abhi@email.com', '+1234567890', '123 Haider Ganj'),
            ('Arya sharma', 'arya@email.com', '+1234567891', '456 Rajajipuram'),
            ('Md Fahad', 'fahad@email.com', '+1234567892', 'Aishbagh')
        ]
        cursor.executemany('''
            INSERT INTO customers (name, email, phone, address)
            VALUES (?, ?, ?, ?)
        ''', sample_customers)
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    return 'user_id' in session

@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'})
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, full_name FROM admin_users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[1] == hash_password(password):
        session['user_id'] = user[0]
        session['username'] = username
        session['full_name'] = user[2]
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/products', methods=['GET'])
def get_products():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY name')
    products = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0], 'name': p[1], 'category': p[2], 'price': p[3], 
        'cost_price': p[4], 'stock_quantity': p[5], 'supplier': p[6],
        'barcode': p[7], 'image_url': p[8]
    } for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, category, price, cost_price, stock_quantity, supplier, barcode, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['category'], data['price'], data.get('cost_price', 0), 
          data['stock_quantity'], data.get('supplier', ''), data.get('barcode', ''), 
          data.get('image_url', '/static/images/default-product.jpg')))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Product added successfully'})

@app.route('/api/customers', methods=['GET'])
def get_customers():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers ORDER BY name')
    customers = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': c[0], 'name': c[1], 'email': c[2], 'phone': c[3], 'address': c[4]
    } for c in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (name, email, phone, address)
        VALUES (?, ?, ?, ?)
    ''', (data['name'], data.get('email', ''), data.get('phone', ''), data.get('address', '')))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Customer added successfully'})

@app.route('/api/sales/process', methods=['POST'])
def process_sale():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    items = data['items']
    customer_id = data.get('customer_id')
    payment_method = data.get('payment_method', 'Cash')
    discount_percent = data.get('discount_percent', 0)
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    try:
        # Calculate totals
        subtotal = 0
        for item in items:
            cursor.execute('SELECT price, stock_quantity FROM products WHERE id = ?', (item['product_id'],))
            product = cursor.fetchone()
            if not product or product[1] < item['quantity']:
                raise Exception(f'Insufficient stock for product ID {item["product_id"]}')
            subtotal += product[0] * item['quantity']
        
        discount_amount = subtotal * (discount_percent / 100)
        tax_amount = (subtotal - discount_amount) * 0.08  # 8% tax
        total_amount = subtotal - discount_amount + tax_amount
        
        # Create sale record
        cursor.execute('''
            INSERT INTO sales (customer_id, subtotal, tax_amount, discount_amount, total_amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_id, subtotal, tax_amount, discount_amount, total_amount, payment_method))
        
        sale_id = cursor.lastrowid
        
        # Add sale items and update stock
        for item in items:
            cursor.execute('SELECT price FROM products WHERE id = ?', (item['product_id'],))
            unit_price = cursor.fetchone()[0]
            total_price = unit_price * item['quantity']
            
            cursor.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (sale_id, item['product_id'], item['quantity'], unit_price, total_price))
            
            cursor.execute('''
                UPDATE products SET stock_quantity = stock_quantity - ?
                WHERE id = ?
            ''', (item['quantity'], item['product_id']))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sale processed successfully',
            'sale_id': sale_id,
            'total_amount': total_amount,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'discount_amount': discount_amount
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/sales', methods=['GET'])
def get_sales():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, c.name, s.subtotal, s.tax_amount, s.discount_amount, 
               s.total_amount, s.payment_method, s.sale_date
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        ORDER BY s.sale_date DESC
        LIMIT 50
    ''')
    sales = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': s[0], 'customer_name': s[1] or 'Walk-in Customer',
        'subtotal': s[2], 'tax_amount': s[3], 'discount_amount': s[4],
        'total_amount': s[5], 'payment_method': s[6], 'sale_date': s[7]
    } for s in sales])

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE stock_quantity < 10')
    low_stock = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(sale_date) = DATE("now")')
    today_sales = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime("%Y-%m", sale_date) = strftime("%Y-%m", "now")')
    month_sales = cursor.fetchone()[0]
    
    # Chart data - Sales by day for last 7 days
    cursor.execute('''
        SELECT DATE(sale_date) as sale_date, COALESCE(SUM(total_amount), 0) as daily_sales
        FROM sales 
        WHERE sale_date >= date('now', '-7 days')
        GROUP BY DATE(sale_date)
        ORDER BY sale_date
    ''')
    daily_sales = cursor.fetchall()
    
    # Top selling products
    cursor.execute('''
        SELECT p.name, COALESCE(SUM(si.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN sale_items si ON p.id = si.product_id
        LEFT JOIN sales s ON si.sale_id = s.id
        WHERE s.sale_date >= date('now', '-30 days') OR s.sale_date IS NULL
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
    ''')
    top_products = cursor.fetchall()
    
    # Category-wise sales
    cursor.execute('''
        SELECT p.category, COALESCE(SUM(si.total_price), 0) as category_sales
        FROM products p
        LEFT JOIN sale_items si ON p.id = si.product_id
        LEFT JOIN sales s ON si.sale_id = s.id
        WHERE s.sale_date >= date('now', '-30 days') OR s.sale_date IS NULL
        GROUP BY p.category
        ORDER BY category_sales DESC
    ''')
    category_sales = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_products': total_products,
        'low_stock': low_stock,
        'today_sales': today_sales,
        'month_sales': month_sales,
        'daily_sales': [{'date': d[0], 'sales': d[1]} for d in daily_sales],
        'top_products': [{'name': p[0], 'sold': p[1]} for p in top_products],
        'category_sales': [{'category': c[0], 'sales': c[1]} for c in category_sales]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)