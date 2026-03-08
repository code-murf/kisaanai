-- Create mandis table without PostGIS dependency

CREATE TABLE IF NOT EXISTS mandis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(50),
    state VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    market_type VARCHAR(50) DEFAULT 'Regulated',
    pincode VARCHAR(10),
    contact_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mandis_name ON mandis(name);
CREATE INDEX IF NOT EXISTS idx_mandis_state ON mandis(state);
CREATE INDEX IF NOT EXISTS idx_mandis_district ON mandis(district);
CREATE INDEX IF NOT EXISTS idx_mandis_state_district ON mandis(state, district);
CREATE INDEX IF NOT EXISTS idx_mandis_active ON mandis(is_active);

-- Insert sample mandis (Delhi region)
INSERT INTO mandis (name, district, state, latitude, longitude, market_type, contact_phone, is_active)
VALUES 
    ('Azadpur Mandi', 'Delhi', 'DL', 28.7041, 77.1025, 'Regulated', '+91-11-27682000', true),
    ('Okhla Mandi', 'Delhi', 'DL', 28.5355, 77.2750, 'Regulated', '+91-11-26812345', true),
    ('Ghazipur Mandi', 'Delhi', 'DL', 28.6139, 77.3150, 'Regulated', '+91-11-22150000', true),
    ('Keshopur Mandi', 'Delhi', 'DL', 28.6692, 77.1350, 'Regulated', '+91-11-27350000', true),
    ('Narela Mandi', 'Delhi', 'DL', 28.8500, 77.0900, 'Regulated', '+91-11-27040000', true),
    ('Bahadurgarh Mandi', 'Jhajjar', 'HR', 28.6928, 76.9200, 'Regulated', '+91-1276-222000', true)
ON CONFLICT DO NOTHING;

-- Verify
SELECT 'Mandis created:' as info, COUNT(*) as count FROM mandis;
SELECT * FROM mandis LIMIT 3;
