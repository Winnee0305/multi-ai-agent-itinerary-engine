-- ============================================================================
-- CLEAN DATABASE: Drop existing table and recreate fresh
-- Run this in Supabase SQL Editor before uploading new data
-- ============================================================================

-- Drop the existing table (CAUTION: This deletes all data!)
DROP TABLE IF EXISTS osm_pois CASCADE;

-- Recreate the table with fields matching your JSON structure
CREATE TABLE osm_pois (
    -- Core OSM fields
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,  -- From your JSON: "Gastronomy", etc.
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    geom GEOGRAPHY(POINT, 4326),  -- PostGIS geometry column
    
    -- Location metadata
    state TEXT,
    
    -- Golden list classification
    in_golden_list BOOLEAN DEFAULT FALSE,
    
    -- Popularity scoring
    popularity_score INTEGER DEFAULT 0,
    wikidata_sitelinks INTEGER DEFAULT 0,
    
    -- Google Places enrichment (optional fields)
    google_rating REAL,
    google_reviews INTEGER,
    google_place_id TEXT UNIQUE,
    google_matched_name TEXT,
    google_types TEXT[],  -- Array of place types
    
    -- Metadata timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Spatial index for PostGIS queries
CREATE INDEX idx_osm_pois_geom ON osm_pois USING GIST(geom);

-- Filter indexes
CREATE INDEX idx_osm_pois_state ON osm_pois(state);
CREATE INDEX idx_osm_pois_category ON osm_pois(category);
CREATE INDEX idx_osm_pois_golden ON osm_pois(in_golden_list) WHERE in_golden_list = TRUE;
CREATE INDEX idx_osm_pois_popularity ON osm_pois(popularity_score DESC);
CREATE INDEX idx_osm_pois_google_rating ON osm_pois(google_rating DESC) WHERE google_rating IS NOT NULL;

-- Text search index
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_osm_pois_name_trgm ON osm_pois USING gin(name gin_trgm_ops);

-- Google Place ID lookup
CREATE INDEX idx_osm_pois_google_place_id ON osm_pois(google_place_id) WHERE google_place_id IS NOT NULL;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_osm_pois_updated_at ON osm_pois;
CREATE TRIGGER update_osm_pois_updated_at
    BEFORE UPDATE ON osm_pois
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Run this after creating the table to verify structure
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'osm_pois'
ORDER BY ordinal_position;
