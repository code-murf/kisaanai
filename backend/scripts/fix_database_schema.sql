-- Fix database schema to match backend models
-- Run this on the production database

-- Fix commodities table
ALTER TABLE commodities 
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing records
UPDATE commodities SET is_active = true WHERE is_active IS NULL;
UPDATE commodities SET updated_at = created_at WHERE updated_at IS NULL;

-- Fix mandis table (add missing columns for non-PostGIS setup)
ALTER TABLE mandis
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8),
ADD COLUMN IF NOT EXISTS market_type VARCHAR(50) DEFAULT 'Regulated',
ADD COLUMN IF NOT EXISTS pincode VARCHAR(10),
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commodities_name ON commodities(name);
CREATE INDEX IF NOT EXISTS idx_commodities_category ON commodities(category);
CREATE INDEX IF NOT EXISTS idx_commodities_active ON commodities(is_active);

CREATE INDEX IF NOT EXISTS idx_mandis_name ON mandis(name);
CREATE INDEX IF NOT EXISTS idx_mandis_state ON mandis(state);
CREATE INDEX IF NOT EXISTS idx_mandis_district ON mandis(district);
CREATE INDEX IF NOT EXISTS idx_mandis_state_district ON mandis(state, district);
CREATE INDEX IF NOT EXISTS idx_mandis_active ON mandis(is_active);

-- Insert sample mandis with lat/long (Delhi region)
INSERT INTO mandis (name, district, state, latitude, longitude, market_type, contact_phone, is_active)
VALUES 
    ('Azadpur Mandi', 'Delhi', 'DL', 28.7041, 77.1025, 'Regulated', '+91-11-27682000', true),
    ('Okhla Mandi', 'Delhi', 'DL', 28.5355, 77.2750, 'Regulated', '+91-11-26812345', true),
    ('Ghazipur Mandi', 'Delhi', 'DL', 28.6139, 77.3150, 'Regulated', '+91-11-22150000', true),
    ('Keshopur Mandi', 'Delhi', 'DL', 28.6692, 77.1350, 'Regulated', '+91-11-27350000', true),
    ('Narela Mandi', 'Delhi', 'DL', 28.8500, 77.0900, 'Regulated', '+91-11-27040000', true),
    ('Bahadurgarh Mandi', 'Jhajjar', 'HR', 28.6928, 76.9200, 'Regulated', '+91-1276-222000', true)
ON CONFLICT DO NOTHING;

-- Verify the changes
SELECT 'Commodities table structure:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'commodities' 
ORDER BY ordinal_position;

SELECT 'Mandis table structure:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'mandis' 
ORDER BY ordinal_position;

SELECT 'Commodities count:' as info, COUNT(*) as count FROM commodities;
SELECT 'Mandis count:' as info, COUNT(*) as count FROM mandis;
