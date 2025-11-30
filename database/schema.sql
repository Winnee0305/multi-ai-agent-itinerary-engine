-- ============================================================================
-- Supabase PostGIS Schema for Malaysia POI Database
-- ============================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop existing table if needed (CAUTION: This will delete all data)
-- DROP TABLE IF EXISTS osm_pois CASCADE;

-- Create POIs table with all enriched fields
CREATE TABLE IF NOT EXISTS osm_pois (
    -- Core OSM fields
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    geom GEOGRAPHY(POINT, 4326),  -- PostGIS geometry column
    
    -- Location metadata
    state TEXT,
    tags JSONB,  -- Original OSM tags
    
    -- Wikidata enrichment
    wikidata_id TEXT,
    wikidata_sitelinks INTEGER DEFAULT 0,
    wikidata_label TEXT,
    wikidata_description TEXT,
    
    -- Golden list classification
    in_golden_list BOOLEAN DEFAULT FALSE,
    golden_list_category TEXT,
    
    -- Popularity scoring
    popularity_score INTEGER DEFAULT 0,
    
    -- Google Places enrichment
    google_rating REAL,
    google_reviews INTEGER,
    google_place_id TEXT UNIQUE,
    google_matched_name TEXT,
    google_types TEXT[],  -- Array of place types
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Spatial index (automatically created for geography type, but explicit for clarity)
CREATE INDEX IF NOT EXISTS idx_osm_pois_geom ON osm_pois USING GIST(geom);

-- Filter indexes
CREATE INDEX IF NOT EXISTS idx_osm_pois_state ON osm_pois(state);
CREATE INDEX IF NOT EXISTS idx_osm_pois_golden ON osm_pois(in_golden_list) WHERE in_golden_list = TRUE;
CREATE INDEX IF NOT EXISTS idx_osm_pois_popularity ON osm_pois(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_osm_pois_google_rating ON osm_pois(google_rating DESC) WHERE google_rating IS NOT NULL;

-- Text search index (for POI names)
CREATE INDEX IF NOT EXISTS idx_osm_pois_name_trgm ON osm_pois USING gin(name gin_trgm_ops);
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Enable trigram similarity

-- Google Place ID lookup
CREATE INDEX IF NOT EXISTS idx_osm_pois_google_place_id ON osm_pois(google_place_id) WHERE google_place_id IS NOT NULL;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamp
DROP TRIGGER IF EXISTS update_osm_pois_updated_at ON osm_pois;
CREATE TRIGGER update_osm_pois_updated_at
    BEFORE UPDATE ON osm_pois
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Utility Views
-- ============================================================================

-- View: Golden POIs only
CREATE OR REPLACE VIEW golden_pois AS
SELECT * FROM osm_pois
WHERE in_golden_list = TRUE
ORDER BY popularity_score DESC;

-- View: Highly-rated POIs (Google rating >= 4.0)
CREATE OR REPLACE VIEW highly_rated_pois AS
SELECT * FROM osm_pois
WHERE google_rating >= 4.0
ORDER BY google_rating DESC, google_reviews DESC;

-- ============================================================================
-- Sample Queries (for reference)
-- ============================================================================

-- Find POIs within 5km of a location
-- SELECT *, ST_Distance(geom, ST_SetSRID(ST_MakePoint(100.3327, 5.4164), 4326)::geography) as distance_meters
-- FROM osm_pois
-- WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(100.3327, 5.4164), 4326)::geography, 5000)
-- ORDER BY distance_meters;

-- Find top POIs by state
-- SELECT name, state, popularity_score, google_rating
-- FROM osm_pois
-- WHERE state = 'Penang' AND in_golden_list = TRUE
-- ORDER BY popularity_score DESC
-- LIMIT 20;

-- Calculate distance between two POIs
-- SELECT ST_Distance(
--     (SELECT geom FROM osm_pois WHERE id = 123)::geography,
--     (SELECT geom FROM osm_pois WHERE id = 456)::geography
-- ) as distance_meters;
