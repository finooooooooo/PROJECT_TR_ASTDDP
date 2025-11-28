DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'cashier'))
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(15, 0) NOT NULL,
    category VARCHAR(50),
    image_url VARCHAR(255),
    is_inventory_managed BOOLEAN DEFAULT FALSE,
    stock INT DEFAULT 0
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    transaction_code VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(15, 0) NOT NULL,
    tax_amount DECIMAL(15, 0) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'paid' CHECK (status IN ('paid', 'void'))
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_name_snapshot VARCHAR(100) NOT NULL,
    price_snapshot DECIMAL(15, 0) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(15, 0) NOT NULL
);
