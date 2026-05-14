import sqlite3
from flask import Flask, render_template, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape, Markup
from datetime import datetime, timedelta
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
import os
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")
csrf = CSRFProtect(app)


UPLOAD_FOLDER = 'static/images/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
        conn = sqlite3.connect('GLH.db')
        conn.row_factory = sqlite3.Row
        return conn
   
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)   

@app.route("/")
def index():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products LIMIT 3")
        products = cursor.fetchall()

        return render_template("index.html", products=products)
    except sqlite3.Error as error:
        return f"Database Error: {error}"
    finally:
        if conn:
            conn.close()
    
@app.route("/signup", methods=["GET", "POST"])
def signup():
     if request.method == "POST":
          
          conn = None
          errors = []
          try:
               full_name = escape(request.form.get("full_name", "").strip())
               email = escape(request.form.get("email", "").strip())
               password = request.form.get("password", "")
               confirm_password = request.form.get("confirm_password", "")
               
               if not full_name.strip() or not email.strip() or not password or not confirm_password:
                    errors.append("Error: Fields cannot be empty")

               if password != confirm_password:
                    errors.append("Error: Passwords do not match")
               
               if len(password) < 8:
                    errors.append("Error: Password must be at least 8 characters")
               
               if '@' not in email or '.' not in email:
                    errors.append("Error: Input a valid email")
               
               special_characters = ['@', '#', '$', '!', '^', '&', '*']

               if not any(char in special_characters for char in password):
                    errors.append("Error: Password must contain at least one special character")
                    
               if errors:
                    return render_template("signup.html",
                                    errors=errors,
                                    full_name=full_name,
                                    email=email
                                    )
               
               hashed_password = generate_password_hash(password)

               conn =get_db()
               cursor = conn.cursor()
               
               cursor.execute(
                    "INSERT INTO user (full_name, email, password_hash) VALUES (?, ?, ?)",
                    (full_name, email, hashed_password)
               )
               conn.commit()
               flash("User registered successfully. Please log in.", "success")
               return redirect("/login")
          except sqlite3.IntegrityError:
            errors.append("Email already exists")
            return render_template("signup.html",
                                    errors=errors,
                                    full_name=full_name,
                                    email=email
                                    )
            
          except sqlite3.Error as error:
            return f"Error: {error}"
          finally:
               if conn:
                    conn.close()
     return render_template("signup.html")
 
@app.route("/producer-signup", methods=["GET", "POST"])
def producer_signup():
     if request.method == "POST":
          
          conn = None
          errors = []
          try:
               full_name = escape(request.form.get("full_name", "").strip())
               email = escape(request.form.get("email", "").strip())
               password = request.form.get("password", "")
               confirm_password = request.form.get("confirm_password", "")
               
               if not full_name.strip() or not email.strip() or not password or not confirm_password:
                    errors.append("Error: Fields cannot be empty")

               if password != confirm_password:
                    errors.append("Error: Passwords do not match")
               
               if len(password) < 8:
                    errors.append("Error: Password must be at least 8 characters")
               
               if '@' not in email or '.' not in email:
                    errors.append("Error: Input a valid email")
               
               special_characters = ['@', '#', '$', '!', '^', '&', '*']

               if not any(char in special_characters for char in password):
                    errors.append("Error: Password must contain at least one special character")
                    
               if errors:
                    return render_template("producer_signup.html",
                                    errors=errors,
                                    full_name=full_name,
                                    email=email
                                    )
               
               hashed_password = generate_password_hash(password)

               conn = get_db()
               cursor = conn.cursor()

               #Insert into user table
               cursor.execute("""
                    INSERT INTO user (full_name, email, password_hash, is_producer)
                    VALUES (?, ?, ?, ?)
                """, (full_name, email, hashed_password, 1))

               user_id = cursor.lastrowid

               #Insert into producers table
               farm_name = request.form.get("farm_name")
               description = request.form.get("description")
               
               if not farm_name or not description:
                    errors.append("Farm details are required")
                    return render_template("producer_signup.html", errors=errors)

               cursor.execute("""
                    INSERT INTO producers (user_id, farm_name, description)
                    VALUES (?, ?, ?)
                """, (user_id, farm_name, description))

               conn.commit()
               flash("Farm registered successfully. Please log in.", "success")
               return redirect("/login")
          except sqlite3.IntegrityError:
            errors.append("Email already exists")
            return render_template("producer_signup.html",
                                    errors=errors,
                                    full_name=full_name,
                                    email=email
                                    )
            
          except sqlite3.Error as error:
            return f"Error: {error}"
          finally:
               if conn:
                    conn.close()
     return render_template("producer_signup.html")
 

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = None
        errors = []

        email = escape(request.form.get("email", "").strip())
        password = request.form.get("password", "")

        if not email or not password:
            errors.append("All fields are required")
            return render_template("login.html", errors=errors, email=email)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user is None:
                errors.append("Email not registered")
                return render_template("login.html", errors=errors, email=email)

            # Check if account is locked
            if user["locked_until"]:
                locked_until = datetime.strptime(user["locked_until"], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < locked_until:
                    errors.append("Account locked due to too many failed attempts. Please contact support.")
                    return render_template("login.html", errors=errors, email=email)
                else:
                    
                    cursor.execute("""
                        UPDATE user SET failed_attempts = 0, locked_until = NULL
                        WHERE user_id = ?
                    """, (user["user_id"],))
                    conn.commit()

            # Check password
            if not check_password_hash(user["password_hash"], password):
                new_attempts = user["failed_attempts"] + 1

                if new_attempts >= 5:
                    
                    lock_time = datetime.now() + timedelta(minutes=30)
                    cursor.execute("""
                        UPDATE user SET failed_attempts = ?, locked_until = ?
                        WHERE user_id = ?
                    """, (new_attempts, lock_time.strftime("%Y-%m-%d %H:%M:%S"), user["user_id"]))
                    conn.commit()
                    errors.append("Account locked due to too many failed attempts. Please contact support.")
                else:
                   
                    cursor.execute("""
                        UPDATE user SET failed_attempts = ?
                        WHERE user_id = ?
                    """, (new_attempts, user["user_id"]))
                    conn.commit()
                    remaining = 5 - new_attempts
                    errors.append(f"Incorrect password. {remaining} attempt{'s' if remaining != 1 else ''} remaining before account is locked.")

                return render_template("login.html", errors=errors, email=email)

            
            cursor.execute("""
                UPDATE user SET failed_attempts = 0, locked_until = NULL
                WHERE user_id = ?
            """, (user["user_id"],))
            conn.commit()

            session["user_id"] = user["user_id"]
            session["user_name"] = user["full_name"]
            session["is_producer"] = user["is_producer"]
            return redirect("/")

        except sqlite3.Error as error:
            return f"Database error: {error}"

        finally:
            if conn:
                conn.close()

    return render_template("login.html")
                    

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")

@app.route("/producers")
def producers():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM producers")
        producer_data = cursor.fetchall()

        return render_template("producers.html", producers=producer_data)

    except sqlite3.Error as error:
        return f"Database Error: {error}"

    finally:
        if conn:
            conn.close()
            
            
@app.route("/products")
def products():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        product_data = cursor.fetchall()

        return render_template("products.html", products=product_data)

    except sqlite3.Error as error:
        return f"Database Error: {error}"

    finally:
        if conn:
            conn.close()
            
@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if 'user_id' not in session:
        flash("Please log in to schedule order", "error")
        return redirect('/login?next=/schedule')

    conn = get_db()
    cursor = conn.cursor()

    try:
        # For GET request load products
        if request.method == "GET":
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()

            today = datetime.today().date()
            max_date = today + timedelta(days=30)

            return render_template(
                "schedule.html",
                products=products,
                today=today,
                max_date=max_date
            )

        # POST request process form
        product_id = request.form.get('product')
        quantity = request.form.get('quantity')
        delivery_method = request.form.get('delivery_method').lower()
        collection_date = request.form.get('collection_date')

        errors = []

        # Input Validation
        if not product_id:
            errors.append("Product is required")

        try:
            quantity = int(quantity)
            if quantity < 1 or quantity > 99:
                errors.append("Quantity must be between 1 and 99")
        except:
            errors.append("Invalid quantity")

        if delivery_method not in ["deliver", "pickup"]:
            errors.append("Invalid delivery method")

        if delivery_method == "pickup":
            if not collection_date:
                errors.append("Collection date is required for pickup")
            else:
                try:
                    selected_date = datetime.strptime(collection_date, "%Y-%m-%d").date()
                    today = datetime.today().date()
                    max_date = today + timedelta(days=30)

                    if selected_date < today or selected_date > max_date:
                        errors.append("Date must be within 30 days")
                except:
                    errors.append("Invalid date format")

        # If errors then reload page
        if errors:
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()

            return render_template(
                "schedule.html",
                products=products,
                errors=errors,
                today=datetime.today().date(),
                max_date=datetime.today().date() + timedelta(days=30)
            )

        # Inserting orders to orders table
        cursor.execute("""
            INSERT INTO orders (user_id, collection_date, delivery_method, status)
            VALUES (?, ?, ?, ?)
        """, (
            session["user_id"],
            collection_date if delivery_method == "pickup" else None,
            delivery_method,
            "Scheduled"
        ))

        order_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (
            order_id,
            product_id,
            quantity
        ))

        
        
        if quantity >= 5:
            cursor.execute("""
                UPDATE user
                SET loyalty_point = loyalty_point + ?
                WHERE user_id = ?
            """, (quantity * 10, session["user_id"]))
            
        conn.commit()

        flash(Markup("Order scheduled successfully! Do you want to <a>schedule another order<a>"), "success")
        return redirect("/dashboard")
            

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        conn.close()
        
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to view dashboard", "error")
        return redirect('/login?next=/dashboard')

    import random
    import string

    def generate_tracking():
        carriers = ["EVRI", "DPD", "ROYALMAIL"]
        prefix = random.choice(carriers)
        code = "H05VIA" + "".join(random.choices(string.digits, k=10))
        return f"{prefix}: {code}"

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get user info
        cursor.execute(
            "SELECT * FROM user WHERE user_id = ?",
            (session["user_id"],)
        )
        user = cursor.fetchone()

        # Get order history with product info
        cursor.execute("""
            SELECT 
                o.order_id,
                o.collection_date,
                o.delivery_method,
                o.status,
                oi.quantity,
                p.product_name
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.user_id = ?
            ORDER BY o.order_id DESC
        """, (session["user_id"],))

        orders = cursor.fetchall()

        # Attach tracking numbers
        orders_with_tracking = []
        for order in orders:
            order_dict = dict(order)
            order_dict["tracking"] = generate_tracking()
            orders_with_tracking.append(order_dict)

        return render_template(
            "dashboard.html",
            user=user,
            orders=orders_with_tracking
        )

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()
        
@app.route("/producer-dashboard")
def producer_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access your dashboard", "error")
        return redirect('/login?next=/producer-dashboard')

    if not session.get('is_producer'):
        flash("Access denied: Producer accounts only", "error")
        return redirect('/')

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM producers WHERE user_id = ?", (session['user_id'],))
        producer = cursor.fetchone()

        if not producer:
            flash("Producer profile not found", "error")
            return redirect('/')

        cursor.execute("SELECT * FROM products WHERE producer_id = ?", (producer['producer_id'],))
        products = cursor.fetchall()

        return render_template("producer_dashboard.html", producer=producer, products=products)

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()


@app.route("/producer-add-product", methods=["POST"])
def producer_add_product():
    if 'user_id' not in session or not session.get('is_producer'):
        flash("Unauthorised", "error")
        return redirect('/login')

    conn = None
    errors = []
    try:
        product_name = escape(request.form.get("product_name", "").strip())
        stock_level  = request.form.get("stock_level", "")
        price        = request.form.get("price", "")

        # Validation
        if not product_name:
            errors.append("Product name is required")

        try:
            stock_level = int(stock_level)
            if stock_level < 0:
                errors.append("Stock level cannot be negative")
        except ValueError:
            errors.append("Stock level must be a whole number")

        try:
            price = float(price)
            if price <= 0:
                errors.append("Price must be greater than 0")
        except ValueError:
            errors.append("Price must be a valid number")
            
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Make folder if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"images/products/{filename}"


        if errors:
            for error in errors:
                flash(error, "error")
            return redirect('/producer-dashboard')

        conn = get_db()
        cursor = conn.cursor()

        # Get producer_id for this user
        cursor.execute("SELECT producer_id FROM producers WHERE user_id = ?", (session['user_id'],))
        producer = cursor.fetchone()

        if not producer:
            flash("Producer profile not found", "error")
            return redirect('/producer-dashboard')

        cursor.execute("""
            INSERT INTO products (producer_id, product_name, price, stock_level, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (producer['producer_id'], product_name, price, stock_level, image_path))
        
        conn.commit()
        flash(f"'{product_name}' added successfully!", "success")
        return redirect('/producer-dashboard')

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()


@app.route("/producer-update-price/<int:product_id>", methods=["GET", "POST"])
def producer_update_price(product_id):
    if 'user_id' not in session or not session.get('is_producer'):
        flash("Unauthorised", "error")
        return redirect('/login')

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verify this product belongs to the logged-in producer
        cursor.execute("""
            SELECT p.*, pr.producer_id
            FROM products p
            JOIN producers pr ON p.producer_id = pr.producer_id
            WHERE p.product_id = ? AND pr.user_id = ?
        """, (product_id, session['user_id']))

        product = cursor.fetchone()

        if not product:
            flash("Product not found or access denied", "error")
            return redirect('/producer-dashboard')

        if request.method == "GET":
            return render_template("producer_update_price.html", product=product)

        # POST — process the update
        errors = []
        new_price        = request.form.get("price", "")
        new_stock_level  = request.form.get("stock_level", "")

        try:
            new_price = float(new_price)
            if new_price <= 0:
                errors.append("Price must be greater than 0")
        except ValueError:
            errors.append("Price must be a valid number")

        try:
            new_stock_level = int(new_stock_level)
            if new_stock_level < 0:
                errors.append("Stock level cannot be negative")
        except ValueError:
            errors.append("Stock level must be a whole number")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("producer_update_price.html", product=product)

        cursor.execute("""
            UPDATE products
            SET price = ?, stock_level = ?
            WHERE product_id = ?
        """, (new_price, new_stock_level, product_id))

        conn.commit()
        flash(f"'{product['product_name']}' updated successfully!", "success")
        return redirect('/producer-dashboard')

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()
            
@app.route("/join-glh")
def join_glh():
    return render_template("join_glh.html")

@app.route("/your-products")
def your_products():
    if 'user_id' not in session or not session.get('is_producer'):
        flash("Access denied", "error")
        return redirect('/')

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM producers WHERE user_id = ?", (session['user_id'],))
        producer = cursor.fetchone()

        if not producer:
            flash("Producer profile not found", "error")
            return redirect('/')

        cursor.execute("SELECT * FROM products WHERE producer_id = ?", (producer['producer_id'],))
        products = cursor.fetchall()

        return render_template("your_products.html", producer=producer, products=products)

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()
        

@app.route("/producer-update-product/<int:product_id>", methods=["POST"])
def producer_update_product(product_id):
    if 'user_id' not in session or not session.get('is_producer'):
        flash("Unauthorised", "error")
        return redirect('/login')

    conn = None
    errors = []
    try:
        product_name = escape(request.form.get("product_name", "").strip())
        stock_level  = request.form.get("stock_level", "")
        price        = request.form.get("price", "")

        if not product_name:
            errors.append("Product name is required")

        try:
            stock_level = int(stock_level)
            if stock_level < 0:
                errors.append("Stock level cannot be negative")
        except ValueError:
            errors.append("Stock level must be a whole number")

        try:
            price = float(price)
            if price <= 0:
                errors.append("Price must be greater than 0")
        except ValueError:
            errors.append("Price must be a valid number")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect('/producer-dashboard')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.product_id FROM products p
            JOIN producers pr ON p.producer_id = pr.producer_id
            WHERE p.product_id = ? AND pr.user_id = ?
        """, (product_id, session['user_id']))

        if not cursor.fetchone():
            flash("Product not found or access denied", "error")
            return redirect('/producer-dashboard')

        cursor.execute("""
            UPDATE products
            SET product_name = ?, stock_level = ?, price = ?
            WHERE product_id = ?
        """, (product_name, stock_level, price, product_id))

        conn.commit()
        flash(f"'{product_name}' updated successfully!", "success")
        return redirect('/producer-dashboard')

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()

@app.route("/producer-orders")
def producer_orders():
    if 'user_id' not in session or not session.get('is_producer'):
        flash("Access denied", "error")
        return redirect('/')

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get producer
        cursor.execute("SELECT * FROM producers WHERE user_id = ?", (session['user_id'],))
        producer = cursor.fetchone()

        if not producer:
            flash("Producer profile not found", "error")
            return redirect('/')

        # Get all orders for this producer's products
        cursor.execute("""
            SELECT
                o.order_id,
                o.collection_date,
                o.delivery_method,
                o.status,
                oi.quantity,
                p.product_id,
                p.product_name,
                p.price,
                (oi.quantity * p.price) AS total_price,
                u.user_id,
                u.full_name,
                u.email
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN user u ON o.user_id = u.user_id
            WHERE p.producer_id = ?
            ORDER BY o.order_id DESC
        """, (producer['producer_id'],))

        orders = cursor.fetchall()

        return render_template("producer_orders.html", producer=producer, orders=orders)

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()
            
@app.route("/schedule_order_clicked", methods=["POST"])
def schedule_order_clicked():
    if 'user_id' not in session:
        flash("Please log in to schedule an order", "error")
        return redirect('/login?next=/products')

    product_id = request.form.get("product_id")

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products", )
        products = cursor.fetchall()

        today = datetime.today().date()
        max_date = today + timedelta(days=30)

        return render_template(
            "schedule.html",
            products=products,
            preselected_product=product_id,
            today=today,
            max_date=max_date
        )
    except sqlite3.Error as error:
        return f"Database error: {error}"
    finally:
        if conn:
            conn.close()
            
@app.route("/manage_order/<int:order_id>")
def manage_order(order_id):
    if 'user_id' not in session:
        flash("Please log in", "error")
        return redirect('/login')

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verify order belongs to this user
        cursor.execute("""
            SELECT o.*, p.product_name, oi.quantity
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_id = ? AND o.user_id = ?
        """, (order_id, session['user_id']))

        order = cursor.fetchone()

        if not order:
            flash("Order not found", "error")
            return redirect('/dashboard')

        return render_template("manage_order.html", order=order)

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()


@app.route("/cancel_order", methods=["POST"])
def cancel_order():
    if 'user_id' not in session:
        flash("Please log in", "error")
        return redirect('/login')

    order_id = request.form.get("order_id")

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verify ownership before cancelling
        cursor.execute("""
            SELECT order_id FROM orders
            WHERE order_id = ? AND user_id = ?
        """, (order_id, session['user_id']))

        if not cursor.fetchone():
            flash("Order not found or access denied", "error")
            return redirect('/dashboard')

        cursor.execute("""
            UPDATE orders SET status = 'Cancelled'
            WHERE order_id = ?
        """, (order_id,))

        conn.commit()
        flash("Order cancelled successfully", "success")
        return redirect('/dashboard')

    except sqlite3.Error as error:
        return f"Database error: {error}"

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":     
     app.run(debug=True)
