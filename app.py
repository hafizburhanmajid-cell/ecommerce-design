from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pymysql
pymysql.install_as_MySQLdb()  # ⚠️ Ye line zaroor add karein!
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config
from decimal import Decimal  # ✅ Decimal import karein

app = Flask(__name__)
app.config.from_object(Config)

# Database Connection Function
def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password='anummajid@123',
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

# ============ ✅ HELPER FUNCTION - Decimal to Float Convert ============
def convert_decimal_to_float(data):
    """Convert Decimal values to float for template compatibility"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, Decimal):
                        item[key] = float(value)
    return data
# =======================================================================

# ============ ✅ GLOBAL CONTEXT PROCESSOR ============
@app.context_processor
def inject_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return dict(categories=categories)
    except Exception as e:
        print(f"Error loading categories: {e}")
        return dict(categories=[])
# ====================================================

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home Page
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT 8")
    featured_products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # ✅ Convert Decimal to float
    featured_products = convert_decimal_to_float(featured_products)
    
    return render_template('index.html', featured_products=featured_products)

# Product Listing Page
@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    
    query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1"
    params = []
    
    if category:
        query += " AND c.name = %s"
        params.append(category)
    
    if search:
        query += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if min_price:
        query += " AND p.price >= %s"
        params.append(min_price)
    
    if max_price:
        query += " AND p.price <= %s"
        params.append(max_price)
    
    cursor.execute(query, tuple(params))
    all_products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # ✅ Convert Decimal to float
    all_products = convert_decimal_to_float(all_products)
    
    return render_template('products.html', products=all_products)

# ✅ Product Detail Page - UPDATED with Reviews
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get product
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.id = %s
    """, (product_id,))
    product = cursor.fetchone()
    
    if product:
        # Convert Decimal to float for product
        if product.get('price'):
            product['price'] = float(product['price'])
        if product.get('old_price'):
            product['old_price'] = float(product['old_price'])
        if product.get('rating'):
            product['rating'] = float(product['rating'])
        
        # Get reviews for this product
        cursor.execute("""
            SELECT r.*, u.username 
            FROM reviews r 
            LEFT JOIN users u ON r.user_id = u.id 
            WHERE r.product_id = %s 
            ORDER BY r.created_at DESC
        """, (product_id,))
        reviews = cursor.fetchall()
        
        # Get related products
        cursor.execute("""
            SELECT * FROM products 
            WHERE category_id = %s AND id != %s 
            LIMIT 6
        """, (product['category_id'], product_id))
        related_products = cursor.fetchall()
        
        # Convert Decimal to float for reviews and related products
        reviews = convert_decimal_to_float(reviews)
        related_products = convert_decimal_to_float(related_products)
    else:
        reviews = []
        related_products = []
    
    cursor.close()
    conn.close()
    
    return render_template('product_detail.html', 
                          product=product, 
                          reviews=reviews, 
                          related_products=related_products)

# Cart Page - ✅ FIXED Decimal Error
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return render_template('cart.html', cart_items=[], total=0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, p.name, p.price, p.image 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = %s
    """, (session['user_id'],))
    cart_items = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # ✅ Convert Decimal to float and calculate total safely
    total = 0
    for item in cart_items:
        if item.get('price'):
            item['price'] = float(item['price'])
            total += item['price'] * item.get('quantity', 1)
    
    cart_items = convert_decimal_to_float(cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=float(total))

# ✅ CHECKOUT ROUTE
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'GET':
        # Get cart items
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, p.name, p.price, p.image 
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = %s
        """, (session['user_id'],))
        cart_items = cursor.fetchall()
        
        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        
        cursor.close()
        conn.close()
        
        if not cart_items:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('cart'))
        
        return render_template('checkout.html', cart_items=cart_items, total=total)
    
    elif request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        city = request.form['city']
        postal_code = request.form['postal_code']
        country = request.form['country']
        notes = request.form.get('notes', '')
        payment_method = request.form['payment_method']
        
        # Get cart items
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, p.name, p.price 
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = %s
        """, (session['user_id'],))
        cart_items = cursor.fetchall()
        
        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        tax = total * 0.1  # 10% tax
        final_total = total + tax
        
        # Create shipping address
        shipping_address = f"{address}, {city}, {postal_code}, {country}"
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, shipping_address, phone_number, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (session['user_id'], final_total, shipping_address, phone))
        
        order_id = cursor.lastrowid
        
        # Create order items
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
            
            # Update product stock
            cursor.execute("""
                UPDATE products SET stock = stock - %s WHERE id = %s
            """, (item['quantity'], item['product_id']))
        
        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (session['user_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_success', order_id=order_id))

# ✅ ORDER SUCCESS ROUTE
@app.route('/order-success/<int:order_id>')
@login_required
def order_success(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", 
                   (order_id, session['user_id']))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('order_success.html', order=order)

# ✅ MY ORDERS ROUTE
@app.route('/my-orders')
@login_required
def my_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (session['user_id'],))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('my_orders.html', orders=orders)

# ✅ PROFILE ROUTE
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        cursor.execute("""
            UPDATE users SET username = %s, email = %s, phone = %s, address = %s
            WHERE id = %s
        """, (username, email, phone, address, session['user_id']))
        
        conn.commit()
        session['username'] = username
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user data
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('profile.html', user=user)

# ✅ CHANGE PASSWORD ROUTE
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long!', 'error')
        return redirect(url_for('profile'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    if not check_password_hash(user['password'], current_password):
        cursor.close()
        conn.close()
        flash('Current password is incorrect!', 'error')
        return redirect(url_for('profile'))
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))

# ✅ SEARCH FUNCTIONALITY
@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query
    sql = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params.extend([f'%{query}%', f'%{query}%'])
    
    if category:
        sql += " AND c.name = %s"
        params.append(category)
    
    if min_price:
        sql += " AND p.price >= %s"
        params.append(min_price)
    
    if max_price:
        sql += " AND p.price <= %s"
        params.append(max_price)
    
    cursor.execute(sql, tuple(params))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert Decimal to float
    products = convert_decimal_to_float(products)
    
    return render_template('search.html', 
                          products=products, 
                          query=query, 
                          category=category)

# ✅ AJAX SEARCH - Real-time suggestions
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, price, image 
        FROM products 
        WHERE name LIKE %s OR description LIKE %s 
        LIMIT 10
    """, (f'%{query}%', f'%{query}%'))
    
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert to JSON format
    results = []
    for product in products:
        results.append({
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image']
        })
    
    return jsonify(results)

# ✅ WISHLIST ROUTES
@app.route('/wishlist')
@login_required
def wishlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.*, p.name, p.price, p.image, p.rating 
        FROM wishlist w 
        JOIN products p ON w.product_id = p.id 
        WHERE w.user_id = %s 
        ORDER BY w.created_at DESC
    """, (session['user_id'],))
    wishlist_items = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert Decimal to float
    wishlist_items = convert_decimal_to_float(wishlist_items)
    
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO wishlist (user_id, product_id) 
            VALUES (%s, %s)
        """, (session['user_id'], product_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Added to wishlist'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Already in wishlist'})

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM wishlist 
        WHERE user_id = %s AND product_id = %s
    """, (session['user_id'], product_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Removed from wishlist'})

# ✅ PRODUCT REVIEWS ROUTES (NEW)
@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        flash('Please select a valid rating (1-5)', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already reviewed
    cursor.execute("SELECT id FROM reviews WHERE product_id = %s AND user_id = %s", 
                   (product_id, session['user_id']))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash('You have already reviewed this product!', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Insert review
    cursor.execute("INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (%s, %s, %s, %s)",
                   (product_id, session['user_id'], rating, comment))
    
    # Update product average rating
    cursor.execute("""
        UPDATE products SET rating = (SELECT AVG(rating) FROM reviews WHERE product_id = %s)
        WHERE id = %s
    """, (product_id, product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/product/<int:product_id>/review/<int:review_id>/delete', methods=['POST'])
@admin_required
def delete_review(product_id, review_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM reviews WHERE id = %s AND product_id = %s", 
                   (review_id, product_id))
    
    # Recalculate average rating
    cursor.execute("""
        UPDATE products SET rating = COALESCE((SELECT AVG(rating) FROM reviews WHERE product_id = %s), 4.5)
        WHERE id = %s
    """, (product_id, product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

# Add to Cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    quantity = request.json.get('quantity', 1)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cart WHERE user_id = %s AND product_id = %s", 
                   (session['user_id'], product_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE user_id = %s AND product_id = %s",
                      (quantity, session['user_id'], product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                      (session['user_id'], product_id, quantity))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Added to cart'})

# Remove from Cart
@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

# Update Cart Quantity
@app.route('/update_cart/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    quantity = request.json.get('quantity', 1)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s",
                  (quantity, cart_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters long')
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                          (username, email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            cursor.close()
            conn.close()
            return render_template('register.html', error='Username or email already exists')
    
    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# ✅ UPDATED ADMIN ROUTE
@app.route('/admin')
@admin_required
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get products
    cursor.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id")
    products = cursor.fetchall()
    
    # Get categories
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    # Get orders
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    
    # Get users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_price) as revenue FROM orders WHERE status != 'cancelled'")
    result = cursor.fetchone()
    total_revenue = result['revenue'] if result['revenue'] else 0
    
    cursor.close()
    conn.close()
    
    # Convert Decimal to float
    products = convert_decimal_to_float(products)
    
    return render_template('admin.html', 
                          products=products, 
                          categories=categories, 
                          orders=orders, 
                          users=users,
                          total_orders=total_orders,
                          total_users=total_users,
                          total_revenue=round(total_revenue, 2))

# Admin: Add Product
@app.route('/admin/add_product', methods=['POST'])
@admin_required
def add_product():
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    category_id = request.form['category_id']
    stock = request.form['stock']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, description, price, category_id, stock) VALUES (%s, %s, %s, %s, %s)",
                  (name, description, price, category_id, stock))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin'))

# Admin: Delete Product
@app.route('/admin/delete_product/<int:product_id>')
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)