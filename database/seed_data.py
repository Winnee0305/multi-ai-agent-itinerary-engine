"""
Upload Malaysia POIs (Google-enriched data) into Supabase
Enhanced version with priority scores support
"""

import json
import math
import os
import sys
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.supabase_client import get_supabase
from config.settings import settings

load_dotenv()


def load_pois(filepath: str) -> List[Dict]:
    """Load POIs from enriched JSON file"""
    print(f"📂 Loading POIs from: {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"POI file not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pois = data.get("pois", [])
    metadata = data.get("metadata", {})
    
    print(f"✅ Loaded {len(pois)} POIs")
    print(f"📊 Metadata: {metadata}")
    
    return pois


def prepare_poi_for_upload(poi: Dict) -> Dict:
    """
    Prepare POI data for Supabase upload
    Ensures all fields match the JSON schema exactly
    Handles null/empty values gracefully - all POIs uploaded regardless of missing fields
    """
    # Required fields - must have values
    if not poi.get("id") or not poi.get("lat") or not poi.get("lon"):
        raise ValueError(f"POI missing required fields: {poi.get('name', 'Unknown')}")
    
    # Create PostGIS geometry point
    prepared = {
        "id": poi.get("id"),
        "name": poi.get("name", "Unknown"),  # Default if missing
        "category": poi.get("category"),  # Can be None
        "lat": poi.get("lat"),
        "lon": poi.get("lon"),
        "geom": f"POINT({poi['lon']} {poi['lat']})",  # WKT format for PostGIS
        "state": poi.get("state"),  # Can be None
        
        # Golden list & popularity (with defaults for missing values)
        "in_golden_list": poi.get("in_golden_list", False),
        "popularity_score": poi.get("popularity_score", 0),
        "wikidata_sitelinks": poi.get("wikidata_sitelinks", 0),
        
        # Google Places enrichment - all optional, can be None
        "google_rating": poi.get("google_rating"),
        "google_reviews": poi.get("google_reviews"),
        "google_place_id": poi.get("google_place_id"),
        "google_matched_name": poi.get("google_matched_name"),
        "google_types": poi.get("google_types") if poi.get("google_types") else None,
    }
    
    # Keep all fields including None values - database will handle nulls
    # Only remove if explicitly empty list (but keep None)
    cleaned = {}
    for k, v in prepared.items():
        if v == []:  # Convert empty lists to None
            cleaned[k] = None
        else:
            cleaned[k] = v
    
    return cleaned


def upload_pois_batch(pois: List[Dict], batch_size: int = 500, use_upsert: bool = True):
    """
    Upload POIs to Supabase in batches
    
    Args:
        pois: List of POI dictionaries
        batch_size: Number of rows per batch
        use_upsert: If True, update existing rows; if False, insert only
    """
    supabase = get_supabase()
    
    total = len(pois)
    total_batches = math.ceil(total / batch_size)
    
    print(f"\n{'='*80}")
    print(f"UPLOADING {total} POIs TO SUPABASE")
    print(f"{'='*80}")
    print(f"Mode: {'UPSERT (update/insert)' if use_upsert else 'INSERT only'}")
    print(f"Batch size: {batch_size}")
    print(f"Total batches: {total_batches}\n")
    
    successful_batches = 0
    failed_batches = 0
    total_uploaded = 0
    
    for i in range(0, total, batch_size):
        batch = pois[i : i + batch_size]
        batch_num = i // batch_size + 1
        
        # Prepare batch for upload
        prepared_batch = [prepare_poi_for_upload(poi) for poi in batch]
        
        print(f"[{batch_num}/{total_batches}] Uploading {len(prepared_batch)} POIs...")
        
        try:
            if use_upsert:
                # Upsert: update on conflict, using 'id' as the conflict column
                response = supabase.table("osm_pois").upsert(prepared_batch).execute()
            else:
                # Insert only (will fail on duplicates)
                response = supabase.table("osm_pois").insert(prepared_batch).execute()
            
            print(f"  ✅ Batch {batch_num} uploaded successfully")
            successful_batches += 1
            total_uploaded += len(prepared_batch)
            
        except Exception as e:
            print(f"  ❌ Error uploading batch {batch_num}: {e}")
            failed_batches += 1
            # Continue with next batch
    
    # Summary
    print(f"\n{'='*80}")
    print(f"UPLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"Total POIs: {total}")
    print(f"Successfully uploaded: {total_uploaded}")
    print(f"Successful batches: {successful_batches}/{total_batches}")
    print(f"Failed batches: {failed_batches}")
    print(f"{'='*80}\n")
    
    if failed_batches == 0:
        print("✅ All POIs uploaded successfully!")
    else:
        print(f"⚠️  {failed_batches} batch(es) failed. Check errors above.")


def main():
    """Main upload script"""
    
    # Get POI data file path
    data_dir = Path(settings.DATA_DIR)
    poi_file = data_dir / settings.POI_DATA_FILE
    
    # Load POIs
    pois = load_pois(str(poi_file))
    
    # Upload to Supabase
    upload_pois_batch(pois, batch_size=500, use_upsert=True)


if __name__ == "__main__":
    main()
