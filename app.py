from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pymysql
import json
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MySQL connection setup
def get_db_connection():
    conn = pymysql.connect(
        host='abhaynigam927.mysql.pythonanywhere-services.com',   # your host
        user='abhaynigam927',                                     # your MySQL username
        password='YOUR_MYSQL_PASSWORD',                           # your MySQL password
        database='abhaynigam927$Store',                           # your database name
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            cost_price DECIMAL(10,2) NOT NULL DEFAULT 0,
            stock_quantity INT NOT NULL,
            supplier VARCHAR(255),
            barcode VARCHAR(100),
            image_url VARCHAR(255),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            subtotal DECIMAL(10,2) NOT NULL,
            tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # Sale items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT,
            product_id INT,
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Insert default admin user if not exists
    cursor.execute('''
        SELECT COUNT(*) AS cnt FROM admin_users WHERE username = %s
    ''', ('admin',))
    row = cursor.fetchone()
    if row['cnt'] == 0:
        cursor.execute('''
            INSERT INTO admin_users (username, password, full_name, email)
            VALUES (%s, %s, %s, %s)
        ''', ('admin', 'admin123', 'Store Administrator', 'admin@store.com'))

    conn.commit()
    conn.close()


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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password, full_name FROM admin_users WHERE username = %s', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password'] == password:
        session['user_id'] = user['id']
        session['username'] = username
        session['full_name'] = user['full_name']
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
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY name')
    products = cursor.fetchall()
    conn.close()
    
    # convert DictCursor rows to expected JSON
    return jsonify([{
        'id': p['id'], 'name': p['name'], 'category': p['category'],
        'price': float(p['price']), 'cost_price': float(p['cost_price']),
        'stock_quantity': p['stock_quantity'], 'supplier': p['supplier'],
        'barcode': p['barcode'], 'image_url': p['image_url']
    } for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products 
          (name, category, price, cost_price, stock_quantity, supplier, barcode, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        data['name'], data['category'], data['price'], data.get('cost_price', 0),
        data['stock_quantity'], data.get('supplier', ''), data.get('barcode', ''), 
        data.get('image_url', '/static/images/default-product.jpg')
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Product added successfully'})

@app.route('/api/customers', methods=['GET'])
def get_customers():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers ORDER BY name')
    customers = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': c['id'], 'name': c['name'], 'email': c['email'], 'phone': c['phone'], 'address': c['address']
    } for c in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (name, email, phone, address)
        VALUES (%s, %s, %s, %s)
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
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Calculate totals
        subtotal = 0
        for item in items:
            cursor.execute('SELECT price, stock_quantity FROM products WHERE id = %s', (item['product_id'],))
            product = cursor.fetchone()
            if not product or product['stock_quantity'] < item['quantity']:
                raise Exception(f'Insufficient stock for product ID {item["product_id"]}')
            subtotal += float(product['price']) * item['quantity']
        
        discount_amount = subtotal * (discount_percent / 100)
        tax_amount = (subtotal - discount_amount) * 0.08  # 8% tax
        total_amount = subtotal - discount_amount + tax_amount
        
        # Create sale record
        cursor.execute('''
            INSERT INTO sales (customer_id, subtotal, tax_amount, discount_amount, total_amount, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (customer_id, subtotal, tax_amount, discount_amount, total_amount, payment_method))
        sale_id = cursor.lastrowid
        
        # Add sale items and update stock
        for item in items:
            cursor.execute('SELECT price FROM products WHERE id = %s', (item['product_id'],))
            unit_price = float(cursor.fetchone()['price'])
            total_price = unit_price * item['quantity']
            
            cursor.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s)
            ''', (sale_id, item['product_id'], item['quantity'], unit_price, total_price))
            
            cursor.execute('''
                UPDATE products 
                   SET stock_quantity = stock_quantity - %s
                 WHERE id = %s
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
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, c.name AS customer_name, s.subtotal, s.tax_amount, 
               s.discount_amount, s.total_amount, s.payment_method, s.sale_date
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        ORDER BY s.sale_date DESC
        LIMIT 50
    ''')
    sales = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': s['id'],
        'customer_name': s['customer_name'] or 'Walk-in Customer',
        'subtotal': float(s['subtotal']),
        'tax_amount': float(s['tax_amount']),
        'discount_amount': float(s['discount_amount']),
        'total_amount': float(s['total_amount']),
        'payment_method': s['payment_method'],
        'sale_date': s['sale_date'].isoformat() if isinstance(s['sale_date'], datetime) else s['sale_date']
    } for s in sales])

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('SELECT COUNT(*) AS cnt FROM products')
    total_products = cursor.fetchone()['cnt']
    
    cursor.execute('SELECT COUNT(*) AS cnt FROM products WHERE stock_quantity < 10')
    low_stock = cursor.fetchone()['cnt']
    
    cursor.execute('SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE DATE(sale_date) = CURDATE()')
    today_sales = float(cursor.fetchone()['total'])
    
    cursor.execute('SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE DATE_FORMAT(sale_date, "%Y-%m") = DATE_FORMAT(CURDATE(), "%Y-%m")')
    month_sales = float(cursor.fetchone()['total'])
    
    # Chart data - sales by day for last 7 days
    cursor.execute('''
        SELECT DATE(sale_date) AS sale_date, COALESCE(SUM(total_amount), 0) AS daily_sales
        FROM sales
        WHERE sale_date >= (CURDATE() - INTERVAL 7 DAY)
        GROUP BY DATE(sale_date)
        ORDER BY sale_date
    ''')
    daily = cursor.fetchall()
    daily_sales = [{'date': d['sale_date'].isoformat() if hasattr(d['sale_date'], 'isoformat') else str(d['sale_date']),
                    'sales': float(d['daily_sales'])} for d in daily]
    
    # Top selling products in last 30 days
    cursor.execute('''
        SELECT p.name, COALESCE(SUM(si.quantity), 0) AS total_sold
        FROM products p
        LEFT JOIN sale_items si ON p.id = si.product_id
        LEFT JOIN sales s ON si.sale_id = s.id
        WHERE s.sale_date >= (CURDATE() - INTERVAL 30 DAY) OR s.sale_date IS NULL
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
    ''')
    top = cursor.fetchall()
    top_products = [{'name': t['name'], 'sold': t['total_sold']} for t in top]
    
    # Category-wise sales in last 30 days
    cursor.execute('''
        SELECT p.category, COALESCE(SUM(si.total_price), 0) AS category_sales
        FROM products p
        LEFT JOIN sale_items si ON p.id = si.product_id
        LEFT JOIN sales s ON si.sale_id = s.id
        WHERE s.sale_date >= (CURDATE() - INTERVAL 30 DAY) OR s.sale_date IS NULL
        GROUP BY p.category
        ORDER BY category_sales DESC
    ''')
    cats = cursor.fetchall()
    category_sales = [{'category': c['category'], 'sales': float(c['category_sales'])} for c in cats]
    
    conn.close()
    
    return jsonify({
        'total_products': total_products,
        'low_stock': low_stock,
        'today_sales': today_sales,
        'month_sales': month_sales,
        'daily_sales': daily_sales,
        'top_products': top_products,
        'category_sales': category_sales
    })

if __name__ == '__main__':
    init_db()
    app.run()  # in production on PythonAnywhere you don’t need debug=True
