# GLH Cooperative — Web Application

A Flask-based farm-to-consumer cooperative platform built for my T-Level Digital Production, Design and Development Occupational Specialism.

---

## Setup & Installation

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialise the database
```bash
python3 setup_db.py
```
This creates `GLH.db` with all 5 tables and inserts demo data.

### 3. Run the application
```bash
python3 app.py
```

Then open: **http://127.0.0.1:5000**

---

## Test Credentials

> **Note:** The dummy data in `setup_db.py` uses plain-text password placeholders (`passwordhash123`). To log in properly, register a new account via `/signup` or `/producer-signup`.

| Role     | Endpoint           |
|----------|--------------------|
| Customer | `/signup`          |
| Producer | `/producer-signup` |

---

## Database — `GLH.db`

### Tables

| Table         | Purpose                                      |
|---------------|----------------------------------------------|
| `user`        | All registered accounts (customers & producers) |
| `producers`   | Farm profiles linked to producer user accounts |
| `products`    | Product listings with price, stock, image path |
| `orders`      | Customer orders (pickup or delivery)         |
| `order_items` | Individual products within each order        |

### Key Schema Notes
- `user.is_producer` — `0` = customer, `1` = producer (enforced with `CHECK`)
- `user.locked_until` — set when a user exceeds 5 failed login attempts (30-minute lockout)
- `orders.delivery_method` — constrained to `'pickup'` or `'deliver'` via `CHECK`
- `products.image_path` — relative path to uploaded image under `static/images/products/`
- Foreign keys enforced via `PRAGMA foreign_keys = ON`

---

## Routes

### Public
| Method | Route          | Description                  |
|--------|----------------|------------------------------|
| GET    | `/`            | Homepage with featured products |
| GET    | `/products`    | Full product catalogue       |
| GET    | `/producers`   | All registered farms         |
| GET    | `/forgot_password` | Forgot password page     |

### Authentication
| Method    | Route              | Description                     |
|-----------|--------------------|---------------------------------|
| GET/POST  | `/signup`          | Register a customer account     |
| GET/POST  | `/producer-signup` | Register a producer + farm      |
| GET/POST  | `/login`           | Log in (with lockout after 5 fails) |
| GET       | `/logout`          | Clear session and redirect home |

### Customer
| Method    | Route                        | Description                          |
|-----------|------------------------------|--------------------------------------|
| GET/POST  | `/schedule`                  | Schedule a new order                 |
| POST      | `/schedule_order_clicked`    | Pre-selects a product on schedule page |
| GET       | `/dashboard`                 | Order history + loyalty points       |
| GET       | `/manage_order/<order_id>`   | View a specific order                |
| POST      | `/cancel_order`              | Cancel a Scheduled order             |

### Producer
| Method    | Route                                      | Description                          |
|-----------|--------------------------------------------|--------------------------------------|
| GET       | `/producer-dashboard`                      | Dashboard with products overview     |
| GET       | `/producer-orders`                         | All customer orders for their products |
| GET       | `/your-products`                           | Full product list management page    |
| POST      | `/producer-add-product`                    | Add a new product with image upload  |
| GET/POST  | `/producer-update-price/<product_id>`      | Update price and stock level         |
| POST      | `/producer-update-product/<product_id>`    | Update name, price, and stock        |
| GET       | `/join-glh`                                | Join GLH info page                   |

---

## Features

### Customer Features
- Register and log in securely
- Browse all produce and farm listings
- Schedule orders (pickup with date, or delivery)
- View order history with mock tracking numbers on the dashboard
- Cancel scheduled orders
- Earn loyalty points — 10 points per item on orders of 5+ items

### Producer Features
- Separate producer sign-up with farm name and description
- Producer dashboard showing all listed products
- Add new products with image upload (PNG, JPG, JPEG, WEBP)
- Update product name, price, and stock level
- View all customer orders containing their products

### Security
- CSRF protection on all forms via `Flask-WTF` (`CSRFProtect`)
- Passwords hashed with `werkzeug` (`pbkdf2:sha256`)
- Account lockout after 5 failed login attempts (30-minute lock)
- Remaining attempt count shown to user on failed login
- Automatic lockout expiry — account unlocks after 30 minutes
- All SQL queries use parameterised placeholders (no string concatenation)
- Input sanitisation with `markupsafe.escape()`
- Producer-only routes check `session['is_producer']` before granting access
- File uploads validated by extension whitelist (`png`, `jpg`, `jpeg`, `webp`)
- `secure_filename()` used on all uploaded file names

---

## Image Uploads

Uploaded product images are saved to:
```
static/images/products/
```
The folder is created automatically if it does not exist.  
Supported formats: **PNG, JPG, JPEG, WEBP**

---

## Dependencies

```
Flask==3.1.3
Werkzeug==3.1.7
MarkupSafe==3.0.3
Flask-WTF==1.3.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Project Structure

```
├── app.py                        # Main Flask application
├── setup_db.py                   # Database initialisation & seed data
├── requirements.txt              # Python dependencies
├── GLH.db                        # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── images/
│       └── products/             # Uploaded product images
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── signup.html
    ├── producer_signup.html
    ├── forgot_password.html
    ├── products.html
    ├── producers.html
    ├── schedule.html
    ├── dashboard.html
    ├── manage_order.html
    ├── producer_dashboard.html
    ├── producer_orders.html
    ├── producer_update_price.html
    ├── your_products.html
    └── join_glh.html
```