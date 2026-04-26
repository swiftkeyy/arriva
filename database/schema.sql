-- Arriva Vape Bot Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    referred_by_id INTEGER REFERENCES users(id),
    total_spent INTEGER DEFAULT 0,
    is_vip BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price INTEGER NOT NULL,
    flavors TEXT[] NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    total_amount INTEGER NOT NULL,
    delivery_city VARCHAR(100) NOT NULL,
    delivery_address TEXT NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    flavor VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    subtotal INTEGER NOT NULL
);

-- Referral bonuses table
CREATE TABLE IF NOT EXISTS referral_bonuses (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER REFERENCES users(id) NOT NULL,
    referee_id INTEGER REFERENCES users(id) NOT NULL,
    order_id INTEGER REFERENCES orders(id) NOT NULL,
    amount INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_id ON referral_bonuses(referrer_id);

-- Meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    scheduled_time TIMESTAMP,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled_time ON meetings(scheduled_time);

-- Cart items table
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    flavor VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);

-- Broadcasts table
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    template_name VARCHAR(50) NOT NULL,
    message_text TEXT NOT NULL,
    target_audience VARCHAR(50) NOT NULL,
    total_sent INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default products
INSERT INTO products (name, price, flavors, stock_quantity) VALUES
('Arriva Pro 8000', 1899, ARRAY['Mango Ice', 'Strawberry Kiwi', 'Blue Razz', 'Cola Energy'], 50),
('Elf Bar BC5000', 1699, ARRAY['Mango', 'Watermelon', 'Grape', 'Mint'], 45),
('Crystal Bar 6000', 1599, ARRAY['Lemon Mint', 'Blueberry', 'Peach'], 40),
('Geek Bar Pulse 6000', 1999, ARRAY['Watermelon Ice', 'Strawberry Banana', 'Miami Mint'], 35),
('Arriva Max 12000', 2499, ARRAY['Almaty Cherry', 'Shymkent Lemon', 'Kazakh Energy'], 30),
('Vozol Star 8000', 1799, ARRAY['Cola', 'Energy Drink', 'Pineapple'], 25),
('Waka 6000', 1499, ARRAY['Mango Lassi', 'Passion Fruit'], 20),
('Arriva Black Edition 5000', 1399, ARRAY['Tobacco', 'Coffee', 'Mint'], 15),
('Arriva Desert 7000', 2099, ARRAY['Tiramisu', 'Cheesecake', 'Chocolate'], 12),
('Crystal Legend 8000', 2199, ARRAY['Sakura', 'Lychee', 'Dragon Fruit'], 10),
('Elf Bar Ultra 9000', 2299, ARRAY['Red Bull', 'Monster', '7Up'], 8),
('Arriva Limited 10000', 2699, ARRAY['Алматы Sunset'], 5)
ON CONFLICT DO NOTHING;

-- Insert default settings
INSERT INTO settings (key, value) VALUES
('shop_name', 'Arriva Shop KZ v4.0'),
('kaspi_account', '+7 777 123 4567'),
('kaspi_recipient', 'Arriva Shop KZ'),
('delivery_cities', 'Almaty,Astana,Shymkent,Karaganda'),
('min_order_amount', '1000'),
('referral_bonus_amount', '500')
ON CONFLICT DO NOTHING;
