"""
Upload Malaysia POIs (processed OSM data) into Supabase
"""

from supabase import create_client
import json
import math
import os
from dotenv import load_dotenv

load_dotenv()

# TODO: replace these with your own Supabase values
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)


def load_pois(filepath: str):
    """Loads the processed JSON file containing POIs."""
    print(f"Loading POIs from: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pois"]


def upload_pois(pois, batch_size=500, use_upsert=True):
    """
    Uploads POIs to Supabase in batches.
    
    batch_size: number of rows per insert
    use_upsert: if True, uses upsert (update existing, insert new)
                if False, only inserts (will fail on duplicates)
    """

    total = len(pois)
    print(f"Total POIs to upload: {total}")
    print(f"Mode: {'UPSERT (update/insert)' if use_upsert else 'INSERT only'}\n")

    successful_batches = 0
    failed_batches = 0

    for i in range(0, total, batch_size):
        batch = pois[i : i + batch_size]

        # Add geometry field (PostGIS POINT)
        for poi in batch:
            # Create WKT POINT string
            poi["geom"] = f"POINT({poi['lon']} {poi['lat']})"

        batch_num = math.ceil((i+1)/batch_size)
        print(f"Uploading batch {batch_num}/{math.ceil(total/batch_size)} ({len(batch)} POIs)...")

        # Insert or upsert batch
        try:
            if use_upsert:
                # Upsert: update on conflict, using 'id' as the conflict column
                response = supabase.table("osm_pois").upsert(batch).execute()
            else:
                # Insert only (will fail on duplicates)
                response = supabase.table("osm_pois").insert(batch).execute()
            
            print(f"  ✓ Batch {batch_num} uploaded successfully")
            successful_batches += 1
        except Exception as e:
            print(f"  ✗ Error inserting batch {batch_num}: {e}")
            failed_batches += 1
            # Continue with next batch instead of breaking

    print(f"\n{'='*50}")
    print(f"Upload Summary:")
    print(f"  Total batches: {math.ceil(total/batch_size)}")
    print(f"  ✓ Successful: {successful_batches}")
    print(f"  ✗ Failed: {failed_batches}")
    print(f"{'='*50}")
    print("✓ Upload complete!")


def main():
    pois = load_pois("data/malaysia_all_pois_processed.json")
    upload_pois(pois)


if __name__ == "__main__":
    main()
