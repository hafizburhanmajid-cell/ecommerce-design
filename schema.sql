CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    old_price DECIMAL(10, 2),
    image VARCHAR(255),
    category_id INT,
    stock INT DEFAULT 0,
    rating DECIMAL(2, 1) DEFAULT 0,
    reviews_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Cart table
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert sample categories
INSERT INTO categories (name) VALUES 
('Electronics'), ('Clothing'), ('Home & Outdoor'), ('Sports');

-- Insert sample products
INSERT INTO products (name, description, price, old_price, image, category_id, stock, rating, reviews_count) VALUES
('Smart Watch', 'Latest smart watch with fitness tracking', 99.50, 128.00, 'watch.jpg', 1, 50, 4.5, 154),
('GoPro Camera', '4K Action Camera - Black', 398.00, 498.00, 'camera.jpg', 1, 30, 4.8, 200),
('Laptop', 'High performance laptop', 899.00, 999.00, 'laptop.jpg', 1, 20, 4.7, 180),
('Headphones', 'Wireless noise-canceling headphones', 149.99, 199.99, 'headphones.jpg', 1, 45, 4.6, 120),
('T-Shirt', 'Cotton t-shirt multiple colors', 29.99, 39.99, 'tshirt.jpg', 2, 100, 4.3, 85),
('Jeans', 'Classic blue jeans', 59.99, 79.99, 'jeans.jpg', 2, 75, 4.4, 92);