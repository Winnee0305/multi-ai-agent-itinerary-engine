-- ============================================================================
-- Supabase RPC Functions for PostGIS Distance Calculations
-- Run these in your Supabase SQL Editor
-- ============================================================================

-- Function: Get nearby POIs using PostGIS
CREATE OR REPLACE FUNCTION get_nearby_pois(
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    radius_m INTEGER DEFAULT 5000,
    min_pop INTEGER DEFAULT 0,
    golden_only BOOLEAN DEFAULT FALSE,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    id BIGINT,
    name TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    state TEXT,
    popularity_score INTEGER,
    google_rating REAL,
    google_reviews INTEGER,
    google_place_id TEXT,
    google_types TEXT[],
    wikidata_sitelinks INTEGER,
    in_golden_list BOOLEAN,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.lat,
        p.lon,
        p.state,
        p.popularity_score,
        p.google_rating,
        p.google_reviews,
        p.google_place_id,
        p.google_types,
        p.wikidata_sitelinks,
        p.in_golden_list,
        ST_Distance(
            p.geom,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) as distance_meters
    FROM osm_pois p
    WHERE ST_DWithin(
        p.geom,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_m
    )
    AND p.popularity_score >= min_pop
    AND (NOT golden_only OR p.in_golden_list = TRUE)
    ORDER BY distance_meters ASC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;


-- Function: Calculate distance between two points
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN ST_Distance(
        ST_SetSRID(ST_MakePoint(lon1, lat1), 4326)::geography,
        ST_SetSRID(ST_MakePoint(lon2, lat2), 4326)::geography
    );
END;
$$ LANGUAGE plpgsql;


-- Function: Get POIs with distances from a center point
CREATE OR REPLACE FUNCTION get_pois_with_distances(
    poi_ids BIGINT[],
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION
)
RETURNS TABLE (
    id BIGINT,
    name TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.lat,
        p.lon,
        ST_Distance(
            p.geom,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) as distance_meters
    FROM osm_pois p
    WHERE p.id = ANY(poi_ids)
    ORDER BY distance_meters ASC;
END;
$$ LANGUAGE plpgsql;


-- Test the functions
-- SELECT * FROM get_nearby_pois(5.4164, 100.3327, 5000, 70, TRUE, 10);
-- SELECT calculate_distance(5.4164, 100.3327, 5.3547, 100.3020);
