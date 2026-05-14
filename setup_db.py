import sqlite3

try:
    conn = sqlite3.connect('GLH.db')

    cursor = conn.cursor()

    cursor.execute('PRAGMA foreign_keys = ON')

    #Creating user table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                loyalty_point INTEGER DEFAULT 0,
                is_producer INTEGER NOT NULL DEFAULT 0 CHECK(is_producer IN (0,1)),
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS producers (
                producer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                farm_name TEXT NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user (user_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                producer_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                stock_level INTEGER NOT NULL,
                image_path TEXT,
                FOREIGN KEY (producer_id) REFERENCES producers (producer_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                collection_date TEXT,
                delivery_method TEXT CHECK(delivery_method IN ('pickup', 'deliver')),
                status TEXT NOT NULL DEFAULT 'Scheduled',
                FOREIGN KEY (user_id) REFERENCES user (user_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                product_id INTEGER  NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id))''')

    #inserting dummy data
    cursor.executemany('''INSERT OR IGNORE INTO user (full_name, email, password_hash, loyalty_point, is_producer, created_at)
                VALUES (?, ?, ?, ?, ?, ?)''' ,
                [
                    ('David Alo', 'david@example.com', 'passwordhash123', 10, 1, '2026-03-24 10:00:15'),
                    ('Jane Doe', 'jane@example.com', 'passwordhash133', 150, 0, '2026-03-24 13:00:15')
                ]
                )

    cursor.executemany('''INSERT OR IGNORE INTO producers (user_id, farm_name, description)
            VALUES (?, ?, ?)''',
            [
                (1, 'Grace & Mercy Farms', 'Feed the nation now'),
                (2, 'Pinnacle Farms', 'Your very local farmers')
            ]
            )

    cursor.executemany('''INSERT OR IGNORE INTO products (producer_id, product_name, price, stock_level, image_path)
                VALUES (?, ?, ?, ?, ?)''',
                [
                    (1, 'Raw Cow Milk', 21.00, 55, 'images/products/milk.jpg'),
                    (1, 'Free Range Eggs', 4.50, 80, 'images/products/eggs.jpg'),
                    (1, 'Organic Butter', 6.00, 40, 'images/products/butter.jpg'),
                    (2, 'Apple Box', 20.00, 55, 'images/products/apples.jpg'),
                    (2, 'Seasonal Veg Box', 15.00, 30, 'images/products/veg_box.jpg'),
                    (2, 'Honey Jar', 8.00, 60, 'images/products/honey.jpg'),
                ])
    cursor.executemany('''INSERT OR IGNORE INTO orders (user_id, collection_date, delivery_method, status)
                VALUES (?, ?, ?, ?)''',
                [
                    (1, '2026-03-25 14:00:00', 'pickup', 'Scheduled'),
                    (2, '2026-04-25 14:05:00', 'deliver', 'Scheduled')
                ]
                )

    cursor.executemany('''INSERT OR IGNORE INTO order_items (order_id, product_id, quantity)
                VALUES (?, ?, ?)''',
                [
                    (1, 1, 4,),
                    (1, 2, 16)
                ]
                )


    print('Database tables successfully created with secure parameterized placeholders')
    conn.commit()
   
    
except sqlite3.Error as error:
    print(f'Database error: {error}')
finally:
    conn.close()
    print('Done')
