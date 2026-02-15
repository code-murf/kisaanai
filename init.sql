-- KisaanAI Database Initialization Script
-- PostgreSQL 15+

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    district VARCHAR(50),
    village VARCHAR(50),
    role VARCHAR(20) DEFAULT 'farmer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Commodities table
CREATE TABLE IF NOT EXISTS commodities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    unit VARCHAR(20) DEFAULT 'quintal',
    aliases TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mandis table
CREATE TABLE IF NOT EXISTS mandis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(50),
    state VARCHAR(50),
    location GEOGRAPHY(POINT),
    contact VARCHAR(15),
    operating_hours JSONB,
    facilities TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    commodity_id INT REFERENCES commodities(id) ON DELETE CASCADE,
    mandi_id INT REFERENCES mandis(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    modal_price DECIMAL(10,2),
    arrivals INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(commodity_id, mandi_id, date)
);

-- Forecasts table
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    commodity_id INT REFERENCES commodities(id) ON DELETE CASCADE,
    district VARCHAR(50),
    forecast_date DATE NOT NULL,
    predicted_price DECIMAL(10,2),
    confidence_lower DECIMAL(10,2),
    confidence_upper DECIMAL(10,2),
    model_version VARCHAR(20),
    factors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather data table
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    location GEOGRAPHY(POINT),
    district VARCHAR(50),
    date DATE NOT NULL,
    temperature DECIMAL(5,2),
    rainfall DECIMAL(7,2),
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(district, date)
);

-- Diseases table
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    crop_type VARCHAR(50),
    symptoms TEXT,
    treatment TEXT,
    severity VARCHAR(20),
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Disease detections table
CREATE TABLE IF NOT EXISTS disease_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    crop_type VARCHAR(50),
    disease_id INT REFERENCES diseases(id),
    confidence DECIMAL(5,2),
    image_url TEXT,
    location GEOGRAPHY(POINT),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50),
    title VARCHAR(200),
    message TEXT,
    channels TEXT[],
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Alert subscriptions table
CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    commodity_id INT REFERENCES commodities(id) ON DELETE CASCADE,
    price_threshold DECIMAL(10,2),
    notification_channels TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, commodity_id)
);

-- Credit profiles table
CREATE TABLE IF NOT EXISTS credit_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    credit_score INT CHECK (credit_score >= 300 AND credit_score <= 900),
    land_size DECIMAL(10,2),
    annual_income DECIMAL(12,2),
    risk_category VARCHAR(20),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan applications table
CREATE TABLE IF NOT EXISTS loan_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(12,2),
    purpose VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    partner_id INT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    disbursed_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_commodity ON price_history(commodity_id);
CREATE INDEX IF NOT EXISTS idx_price_history_mandi ON price_history(mandi_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_date ON forecasts(forecast_date DESC);
CREATE INDEX IF NOT EXISTS idx_forecasts_commodity ON forecasts(commodity_id);
CREATE INDEX IF NOT EXISTS idx_mandis_location ON mandis USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date DESC);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, sent_at DESC);

-- Insert sample commodities
INSERT INTO commodities (name, category, unit, aliases) VALUES
    ('Wheat', 'Cereals', 'quintal', ARRAY['Gehun', 'Gahu']),
    ('Rice', 'Cereals', 'quintal', ARRAY['Chawal', 'Dhan']),
    ('Potato', 'Vegetables', 'quintal', ARRAY['Aaloo', 'Aloo']),
    ('Tomato', 'Vegetables', 'quintal', ARRAY['Tamatar']),
    ('Onion', 'Vegetables', 'quintal', ARRAY['Pyaz', 'Pyaaz']),
    ('Cotton', 'Cash Crops', 'quintal', ARRAY['Kapas']),
    ('Sugarcane', 'Cash Crops', 'quintal', ARRAY['Ganna']),
    ('Maize', 'Cereals', 'quintal', ARRAY['Makka', 'Corn']),
    ('Soybean', 'Pulses', 'quintal', ARRAY['Soya']),
    ('Groundnut', 'Oilseeds', 'quintal', ARRAY['Moongfali', 'Peanut'])
ON CONFLICT (name) DO NOTHING;

-- Insert sample mandis (major cities)
INSERT INTO mandis (name, district, state, location, contact, facilities) VALUES
    ('Delhi Azadpur Mandi', 'Delhi', 'Delhi', ST_SetSRID(ST_MakePoint(77.1734, 28.7041), 4326), '+91-11-27682000', ARRAY['Cold Storage', 'Weighbridge', 'Banking']),
    ('Mumbai APMC', 'Mumbai', 'Maharashtra', ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326), '+91-22-28521000', ARRAY['Cold Storage', 'Auction Hall']),
    ('Bangalore KR Market', 'Bangalore', 'Karnataka', ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326), '+91-80-26702000', ARRAY['Weighbridge', 'Banking']),
    ('Kolkata Posta Bazar', 'Kolkata', 'West Bengal', ST_SetSRID(ST_MakePoint(88.3639, 22.5726), 4326), '+91-33-22143000', ARRAY['Cold Storage']),
    ('Chennai Koyambedu', 'Chennai', 'Tamil Nadu', ST_SetSRID(ST_MakePoint(80.2707, 13.0827), 4326), '+91-44-23742000', ARRAY['Cold Storage', 'Auction Hall', 'Banking'])
ON CONFLICT DO NOTHING;

-- Insert sample diseases
INSERT INTO diseases (name, crop_type, symptoms, treatment, severity) VALUES
    ('Late Blight', 'Potato', 'Dark brown spots on leaves, white mold on underside', 'Apply fungicide, remove infected plants', 'High'),
    ('Leaf Curl', 'Tomato', 'Curling and yellowing of leaves', 'Use resistant varieties, control whiteflies', 'Medium'),
    ('Blast', 'Rice', 'Diamond-shaped lesions on leaves', 'Apply fungicide, use resistant varieties', 'High'),
    ('Rust', 'Wheat', 'Orange-brown pustules on leaves', 'Apply fungicide, crop rotation', 'Medium'),
    ('Wilt', 'Cotton', 'Yellowing and wilting of leaves', 'Soil treatment, use resistant varieties', 'High')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Create a function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for credit_profiles
CREATE TRIGGER update_credit_profiles_updated_at BEFORE UPDATE ON credit_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'KisaanAI database initialized successfully!';
    RAISE NOTICE 'Database: kisaanai';
    RAISE NOTICE 'Tables created: %', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Sample data inserted';
END $$;
